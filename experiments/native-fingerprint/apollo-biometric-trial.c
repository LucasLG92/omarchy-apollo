/* SPDX-License-Identifier: MIT
 * Supervised first enrollment and verification, not a PAM/lock backend.
 * Only authenticated TA-wrapped templates are persisted, only on the phone.
 */
#define _GNU_SOURCE
#include "bio-wire/apollo-bio.h"
#include "qsee-transport.h"
#include "apollo-auth-check.h"
#include "fpc1020.h"
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/prctl.h>
#include <sys/random.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
static volatile sig_atomic_t cancelled;
static void stop(int sig){(void)sig;cancelled=1;}
static uint32_t get(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(uint8_t *p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=n>>(i*8);}
static int64_t now(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return -1;return (int64_t)t.tv_sec*1000+t.tv_nsec/1000000;}
static void event(const char *name,unsigned value){printf("{\"event\":\"%s\",\"value\":%u}\n",name,value);fflush(stdout);}
static int trusted_dir(int fd,int strict)
{
 struct stat s;if(fd<0 || fstat(fd,&s))return -EPERM;
 return S_ISDIR(s.st_mode) && s.st_uid==0 && !(s.st_mode&0022) && (!strict || (s.st_mode&0777)==0700)?0:-EPERM;
}
static int store_open(void)
{
 int fd=open("/",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 const char *parents[]={"var","lib","apollo","fingerprint-templates-v1","u1000"};
 for(unsigned i=0;i<5;i++){
  if(trusted_dir(fd,i>=4)){if(fd>=0)close(fd);return -EPERM;}
  if(i>=3 && mkdirat(fd,parents[i],0700) && errno!=EEXIST){close(fd);return -errno;}
  int next=openat(fd,parents[i],O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);close(fd);fd=next;
 }
 if(trusted_dir(fd,1)){if(fd>=0)close(fd);return -EPERM;}
 struct statfs fs;if(fstatfs(fd,&fs) || fs.f_type!=0xef53){close(fd);return -EPERM;}
 if(flock(fd,LOCK_EX|LOCK_NB)){close(fd);return -EBUSY;}return fd;
}
static int read_store(int dir,uint8_t **database,size_t *size,uint32_t *id)
{
 *database=0;*size=0;*id=0;int fd=openat(dir,"enrolled-v1",O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_NOFOLLOW);
 if(fd<0)return -errno;
 struct stat s;uint8_t header[24];int rc=-EPROTO;
 if(fstat(fd,&s) || !S_ISREG(s.st_mode) || s.st_uid!=0 || (s.st_mode&0777)!=0600 || s.st_nlink!=1 || s.st_size<76 || s.st_size>24+APOLLO_BIO_DB_MAX)goto out;
 if(read(fd,header,sizeof header)!=sizeof header || memcmp(header,"APFPC001",8) || get(header+8)!=1000 || !get(header+12) || get(header+16)!=7 || get(header+20)!=(size_t)s.st_size-24)goto out;
 *size=get(header+20);*database=malloc(*size);if(!*database){rc=-ENOMEM;goto out;}
 size_t pos=0;while(pos<*size){ssize_t n=read(fd,*database+pos,*size-pos);if(n<0 && errno==EINTR)continue;if(n<=0)goto out;pos+=(size_t)n;}
 if(!apollo_bio_wrapped_database(*database,*size))goto out;
 *id=get(header+12);rc=0;
out:
 close(fd);explicit_bzero(header,sizeof header);if(rc && *database){explicit_bzero(*database,*size);free(*database);*database=0;*size=0;}return rc;
}
static int save_first(int dir,const uint8_t *database,size_t size,uint32_t id)
{
 if(!id || !apollo_bio_wrapped_database(database,size))return -EINVAL;
 uint8_t header[24]={0};memcpy(header,"APFPC001",8);put(header+8,1000);put(header+12,id);put(header+16,7);put(header+20,size);
 int fd=openat(dir,"pending-enrollment-v1",O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW,0600);if(fd<0)return -errno;
 int rc=0;if(write(fd,header,sizeof header)!=sizeof header)rc=-EIO;
 size_t pos=0;while(!rc && pos<size){ssize_t n=write(fd,database+pos,size-pos);if(n<0 && errno==EINTR)continue;if(n<=0){rc=-EIO;break;}pos+=(size_t)n;}
 if(!rc && fsync(fd))rc=-errno;
 if(close(fd) && !rc)rc=-errno;
 if(!rc && renameat2(dir,"pending-enrollment-v1",dir,"enrolled-v1",RENAME_NOREPLACE))rc=-errno;
 if(!rc && fsync(dir))rc=-errno;
 explicit_bzero(header,sizeof header);return rc;
}
static int authorize(void)
{
 pid_t child=fork();if(child<0)return -errno;
 if(!child){int fd=open("/dev/null",O_WRONLY|O_CLOEXEC);if(fd<0 || dup2(fd,1)<0 || dup2(fd,2)<0)_exit(125);close(fd);
  execl("/usr/lib/apollo/fingerprint/apollo-enrollment-authority","apollo-enrollment-authority","--authorize-enrollment-for-uid","1000",(char *)0);_exit(126);}
 int status;pid_t p;do{p=waitpid(child,&status,0);}while(p<0 && errno==EINTR);
 return p==child && WIFEXITED(status) && !WEXITSTATUS(status)?0:-EACCES;
}
static int wait_irq(int fd,int64_t deadline)
{
 while(!cancelled && now()<deadline){
  struct fpc1020_irq_event e={0};if(ioctl(fd,FPC1020_IOC_GET_IRQ,&e) || e.reserved || e.level>1)return -EIO;
  if(e.level)return 0;
  struct pollfd p={.fd=fd,.events=POLLIN};int rc=poll(&p,1,100);if(rc<0 && errno!=EINTR)return -errno;
  if(p.revents&(POLLERR|POLLHUP|POLLNVAL))return -EIO;
  if(p.revents&POLLIN){ssize_t n=read(fd,&e,sizeof e);if(n<0 && errno==EAGAIN)continue;if(n!=sizeof e || e.reserved || e.level>1)return -EPROTO;}
 }
 return cancelled?-ECANCELED:-ETIMEDOUT;
}
static int wait_release(struct apollo_bio *bio,int fd,int64_t deadline)
{
 while(!cancelled && now()<deadline){
  int rc=apollo_sensor_command(bio,1,0);if(rc==1)return 0;if(rc)return rc;
  rc=apollo_sensor_command(bio,2,0);if(rc)return rc;rc=wait_irq(fd,deadline);if(rc)return rc;
  struct timespec pause={.tv_nsec=20000000};nanosleep(&pause,0);
 }
 return cancelled?-ECANCELED:-ETIMEDOUT;
}
static int capture(struct apollo_bio *bio,int fd,int64_t deadline)
{
 int rc=apollo_sensor_command(bio,3,0);if(rc)return rc;
 event("place-finger",0);rc=wait_irq(fd,deadline);if(rc)return rc;
 return apollo_sensor_command(bio,4,0);
}
int main(int argc,char **argv)
{
 if(argc!=2 || (strcmp(argv[1],"--enroll-first-right-index") && strcmp(argv[1],"--verify-uid1000")))return 2;
 struct utsname u;if(geteuid() || uname(&u) || strcmp(u.release,"7.3.1-apollo-native-r15"))return 3;
 struct rlimit limit={0};if(setrlimit(RLIMIT_CORE,&limit) || prctl(PR_SET_DUMPABLE,0))return 4;
 struct sigaction action={.sa_handler=stop};sigemptyset(&action.sa_mask);sigaction(SIGTERM,&action,0);sigaction(SIGINT,&action,0);
 int enroll=!strcmp(argv[1],"--enroll-first-right-index"),rc=0,fd=-1,store=-1,saved=0,matched=0,captures=0;uint32_t id=0,count=0,ids[25]={0};
 uint8_t *database=0;size_t size=0;uint64_t challenge=0;
 struct fpc_qsee_session session=FPC_QSEE_SESSION_INIT;struct apollo_bio bio={&session,fpc_qsee_command};
 const char *phase="open-private-template-store";store=store_open();if(store<0){rc=store;goto out;}
 phase="load-private-enrollment";rc=read_store(store,&database,&size,&id);
 if(enroll){if(rc!=-ENOENT){if(!rc)rc=-EEXIST;goto out;}rc=0;struct stat pending;if(!fstatat(store,"pending-enrollment-v1",&pending,AT_SYMLINK_NOFOLLOW) || errno!=ENOENT){rc=-EINPROGRESS;goto out;}}
 else if(rc)goto out;
 phase="attach-FPC";rc=fpc_qsee_open(&session,"fpcapo");if(rc)goto out;
 phase="open-sensor";fd=open("/dev/fpc1020",O_RDWR|O_NONBLOCK|O_CLOEXEC|O_NOFOLLOW);if(fd<0){rc=-errno;goto out;}
 phase="initialize-sensor";rc=apollo_sensor_command(&bio,0,0);if(rc)goto out;rc=apollo_sensor_command(&bio,5,0);if(rc)goto out;
 phase="initialize-BIO";rc=apollo_bio_init(&bio);if(rc)goto out;
 if(database){phase="load-authenticated-database";rc=apollo_bio_import(&bio,database,size);if(rc)goto out;}
 phase="select-Linux-group";rc=apollo_bio_group(&bio,1000);if(rc)goto out;
 phase="enumerate-current-group";rc=apollo_bio_ids(&bio,ids,&count);if(rc)goto out;
 if(enroll){
  if(count){rc=-EEXIST;goto out;}
  phase="authorize-enrollment";rc=authorize();if(rc)goto out;
  phase="begin-enrollment";rc=apollo_bio_begin(&bio);if(rc)goto out;
  int64_t deadline=now()+150000;uint32_t remaining=UINT32_MAX;
  for(unsigned attempt=0;attempt<80 && now()<deadline && !cancelled;attempt++){
   phase="capture-enrollment-sample";rc=capture(&bio,fd,deadline);if(rc<0)goto out;
   if(rc==0){
    captures++;phase="process-enrollment-sample";rc=apollo_bio_sample(&bio,&remaining);if(rc<0)goto out;
    if(rc==0 || rc==6){event("enrollment-progress",remaining);if(remaining==0 && rc==0)break;}
    else event("retry-sample",(unsigned)rc);
   }else event("retry-capture",(unsigned)rc);
   event("remove-finger",0);phase="wait-for-finger-removal";rc=wait_release(&bio,fd,deadline);if(rc)goto out;
  }
  if(cancelled){rc=-ECANCELED;goto out;}if(remaining){rc=-ETIMEDOUT;goto out;}
  phase="finalize-enrollment";rc=apollo_bio_end(&bio,&id);if(rc)goto out;
  phase="wrap-enrolled-database";rc=apollo_bio_export(&bio,&database,&size);if(rc)goto out;
  phase="validate-enrolled-roundtrip";rc=apollo_bio_import(&bio,database,size);if(rc)goto out;rc=apollo_bio_group(&bio,1000);if(rc)goto out;
  rc=apollo_bio_ids(&bio,ids,&count);if(rc)goto out;if(count!=1 || ids[0]!=id){rc=-EPROTO;goto out;}
  phase="persist-enrolled-database";rc=save_first(store,database,size,id);if(rc)goto out;saved=1;event("enrollment-completed",1);
 }else{
  if(count!=1 || ids[0]!=id){rc=-EPROTO;goto out;}
  phase="import-wrapped-auth-key";struct apollo_auth_check check;rc=apollo_auth_check(&check);if(rc)goto out;
  phase="fresh-verification-challenge";if(getrandom(&challenge,sizeof challenge,0)!=sizeof challenge || !challenge){rc=-EIO;goto out;}
  rc=apollo_bio_challenge(&bio,challenge);if(rc)goto out;
  int64_t deadline=now()+45000;phase="capture-verification-sample";rc=capture(&bio,fd,deadline);if(rc)goto out;captures++;
  uint32_t found=0;phase="TEE-identify";rc=apollo_bio_identify(&bio,&found);if(rc)goto out;
  if(found){if(found!=id){rc=-EPROTO;goto out;}phase="fresh-fingerprint-auth-result";rc=apollo_bio_fresh_result(&bio,challenge);if(rc)goto out;matched=1;}
  event(matched?"verify-match":"verify-no-match",0);
 }
 phase="complete";
out:
 if(fd>=0){int sleep=apollo_sensor_command(&bio,5,0);if(!rc && sleep)rc=sleep;close(fd);}
 fpc_qsee_close(&session);if(store>=0)close(store);if(database){explicit_bzero(database,size);free(database);}
 explicit_bzero(ids,sizeof ids);explicit_bzero(&challenge,sizeof challenge);
 printf("{\"ok\":%s,\"phase\":\"%s\",\"code\":%d,\"finger_enrolled\":%s,\"matched\":%s,\"secure_captures\":%d,\"biometric_bytes_exported\":false,\"lock_or_PAM_changed\":false}\n",rc?"false":"true",phase,rc,saved?"true":"false",matched?"true":"false",captures);
 return rc?1:0;
}
