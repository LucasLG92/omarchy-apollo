/* SPDX-License-Identifier: MIT
 * Root-only Apollo credential authority. No sample capture, matching or PAM.
 * No credential, handle, token or challenge bytes are ever written to stdout.
 */
#define _GNU_SOURCE
#include "apollo-auth-check.h"
#include "auth-wire/gatekeeper-wire.h"
#include "auth-wire/credential-store.h"
#include "qsee-transport.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/random.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <sys/utsname.h>
#include <unistd.h>
static uint32_t word(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static uint64_t wide(const uint8_t *p){return word(p)|(uint64_t)word(p+4)<<32;}
static void put(uint8_t *p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i));}
static int trusted_directory(int fd,int mode)
{
 struct stat s;if(fd<0 || fstat(fd,&s))return -EPERM;
 return S_ISDIR(s.st_mode) && s.st_uid==0 && !(s.st_mode&0022) && (!mode || (s.st_mode&0777)==(unsigned)mode)?0:-EPERM;
}
static int child_directory(int parent,const char *name)
{
 if(mkdirat(parent,name,0700) && errno!=EEXIST)return -errno;
 int fd=openat(parent,name,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 if(trusted_directory(fd,0700)){if(fd>=0)close(fd);return -EPERM;}
 if(fsync(parent)){int rc=-errno;close(fd);return rc;}return fd;
}
static int open_store(unsigned uid)
{
 int fd=open("/",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(trusted_directory(fd,0))return -EPERM;
 const char *parents[]={"var","lib","apollo"};
 for(unsigned i=0;i<3;i++){
  int next=openat(fd,parents[i],O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);close(fd);fd=next;
  if(trusted_directory(fd,0)){if(fd>=0)close(fd);return -EPERM;}
 }
 struct statfs fs;if(fstatfs(fd,&fs) || fs.f_type!=0xef53){close(fd);return -EPERM;}
 int next=child_directory(fd,"fingerprint-credentials-v1");close(fd);if(next<0)return next;fd=next;
 char user[32];int n=snprintf(user,sizeof user,"u%u",uid);if(n<0 || (size_t)n>=sizeof user){close(fd);return -EINVAL;}
 next=child_directory(fd,user);close(fd);if(next<0)return next;fd=next;
 if(flock(fd,LOCK_EX|LOCK_NB)){int rc=-errno;close(fd);return rc;}return fd;
}
static int fpc(struct fpc_qsee_session *session,uint8_t payload[4096])
{
 int32_t outer=INT32_MIN;int rc=fpc_qsee_command(session,payload,4096,&outer);return rc?rc:outer;
}
static int runtime(void)
{
 struct utsname u;if(geteuid()!=0 || uname(&u) || strcmp(u.release,"7.3.1-apollo-native-r15"))return -EPERM;
 char board[4096];int fd=open("/proc/device-tree/compatible",O_RDONLY|O_CLOEXEC);if(fd<0)return -EPERM;
 ssize_t n=read(fd,board,sizeof board);close(fd);if(n<1 || n==(ssize_t)sizeof board)return -EPERM;
 int found=0;size_t start=0;
 for(size_t i=0;i<(size_t)n;i++)if(!board[i]){if(i-start==13 && !memcmp(board+start,"xiaomi,apollo",13))found=1;start=i+1;}
 if(!found || access("/etc/apollo/ram-trial",F_OK)==0)return -EPERM;
 fd=open("/etc/apollo/native-root-v1",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return -EPERM;
 struct stat s;char marker[64];n=read(fd,marker,sizeof marker);int rc=fstat(fd,&s);close(fd);
 if(rc || s.st_uid!=0 || !S_ISREG(s.st_mode) || (s.st_mode&0022) || n!=22 || memcmp(marker,"apollo-native-root-v1\n",22))return -EPERM;
 return 0;
}
int main(int argc,char **argv)
{
 if(argc!=3 || (strcmp(argv[1],"--authorize-enrollment-for-uid") && strcmp(argv[1],"--resume-unenrolled-provisioning-for-uid")))return 2;
 int resume=!strcmp(argv[1],"--resume-unenrolled-provisioning-for-uid");
 char *end;errno=0;unsigned long user=strtoul(argv[2],&end,10);
 if(errno || !*argv[2] || *end || argv[2][0]=='0' || user<1000 || user>65535)return 2;
 if(runtime())return 3;
 struct rlimit limit={0};if(setrlimit(RLIMIT_CORE,&limit) || prctl(PR_SET_DUMPABLE,0))return 4;
 struct {
  uint8_t secret[32],handle[512],token[69],request[2048],response[40960],payload[4096];
 } sensitive={0};
 if(mlock(&sensitive,sizeof sensitive))return 5;
 struct apollo_auth_check preparation;struct fpc_qsee_session sensor={.fd=-1},keymaster={.fd=-1};
 const char *phase="prepare-authorization";int rc=apollo_auth_check(&preparation),store=-1,state=-1;size_t handle_size=0,length=0;int provisioned=0,authorized=0,verified=0;
 if(rc)goto out;
 if(preparation.keymaster_version[0]!=4 || preparation.keymaster_version[1]!=0){rc=-EPROTO;goto out;}
 phase="open-fpc";rc=fpc_qsee_open(&sensor,"fpcapo");if(rc)goto out;
 phase="open-resident-keymaster";rc=fpc_qsee_open(&keymaster,"keymaster64");if(rc)goto out;
 phase="fresh-enrollment-challenge";put(sensitive.payload,3);put(sensitive.payload+4,2);
 rc=fpc(&sensor,sensitive.payload);if(rc)goto out;
 uint64_t challenge=wide(sensitive.payload+8);explicit_bzero(sensitive.payload,sizeof sensitive.payload);
 if(!challenge){rc=-EPROTO;goto out;}
 phase="open-persistent-Linux-credential";store=open_store((unsigned)user);if(store<0){rc=store;goto out;}
 state=apollo_credential_load(store,sensitive.secret,sensitive.handle,&handle_size);
 if(resume){
  phase="explicit-root-recovery-of-unenrolled-credential";
  if(state!=-EINPROGRESS){rc=-EPERM;goto out;}
  rc=apollo_credential_retry_unenrolled(store,sensitive.secret);if(rc)goto out;state=1;
 }else if(state<0){rc=state;goto out;}
 uint32_t uid=APOLLO_GK_UID_FIRST+(uint32_t)user;
 if(state==1){
  phase="durable-pending-credential";size_t got=0;
  if(!resume){
   while(got<32){ssize_t n=getrandom(sensitive.secret+got,32-got,0);if(n<0 && errno==EINTR)continue;if(n<=0){rc=n<0?-errno:-EIO;goto out;}got+=(size_t)n;}
   rc=apollo_credential_begin(store,sensitive.secret);if(rc)goto out;
  }
  phase="Gatekeeper-enroll-Linux-namespace";
  rc=apollo_gk_encode_legacy_enroll(uid,sensitive.secret,32,NULL,0,NULL,0,sensitive.request,sizeof sensitive.request,&length);if(rc)goto out;
  put(sensitive.response,(uint32_t)INT32_MIN);
  phase="Gatekeeper-enroll-transport";
  rc=fpc_qsee_exchange(&keymaster,sensitive.request,length,sensitive.response,40960-length,NULL,0,0);if(rc)goto out;
  phase="Gatekeeper-enroll-secure-response";
  rc=apollo_gk_decode_legacy_handle(sensitive.response,40960-length,sensitive.handle,sizeof sensitive.handle,&handle_size);
  explicit_bzero(sensitive.request,sizeof sensitive.request);explicit_bzero(sensitive.response,sizeof sensitive.response);if(rc)goto out;
  phase="persist-Gatekeeper-handle";rc=apollo_credential_save_handle(store,sensitive.handle,handle_size);if(rc)goto out;provisioned=1;
 }
 phase="Gatekeeper-verify-fresh-challenge";
 rc=apollo_gk_encode_legacy_verify(uid,challenge,sensitive.handle,handle_size,sensitive.secret,32,sensitive.request,sizeof sensitive.request,&length);if(rc)goto out;
 put(sensitive.response,(uint32_t)INT32_MIN);
 rc=fpc_qsee_exchange(&keymaster,sensitive.request,length,sensitive.response,40960-length,NULL,0,0);if(rc)goto out;
 rc=apollo_gk_decode_legacy_token(sensitive.response,40960-length,challenge,sensitive.token);
 explicit_bzero(sensitive.request,sizeof sensitive.request);explicit_bzero(sensitive.response,sizeof sensitive.response);explicit_bzero(&challenge,sizeof challenge);if(rc)goto out;verified=1;
 phase="FPC-authorize-real-hardware-token";put(sensitive.payload,3);put(sensitive.payload+4,3);put(sensitive.payload+8,69);memcpy(sensitive.payload+12,sensitive.token,69);
 rc=fpc(&sensor,sensitive.payload);explicit_bzero(sensitive.payload,sizeof sensitive.payload);explicit_bzero(sensitive.token,sizeof sensitive.token);if(rc)goto out;authorized=1;
 if(state==1 || state==2){phase="commit-Linux-credential";rc=apollo_credential_finish(store);if(rc)goto out;}
 phase="complete";
out:
 if(store>=0)close(store);fpc_qsee_close(&keymaster);fpc_qsee_close(&sensor);
 explicit_bzero(&sensitive,sizeof sensitive);munlock(&sensitive,sizeof sensitive);
 printf("{\"ok\":%s,\"operation\":\"authorize-enrollment\",\"phase\":\"%s\",\"code\":%d,\"new_Linux_credential_provisioned\":%s,\"real_Gatekeeper_token_verified\":%s,\"FPC_accepted_real_token\":%s,\"biometric_enrollment_performed\":false,\"biometric_match_verified\":false,\"credential_or_token_bytes_exported\":false}\n",rc?"false":"true",phase,rc,provisioned?"true":"false",verified?"true":"false",authorized?"true":"false");
 return rc?1:0;
}
