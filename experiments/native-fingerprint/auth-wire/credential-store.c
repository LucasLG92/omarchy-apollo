/* SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include "credential-store.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static int directory_ok(int fd)
{
 struct stat s;if(fstat(fd,&s))return -errno;
 return S_ISDIR(s.st_mode) && s.st_uid==0 && (s.st_mode&0777)==0700?0:-EPERM;
}
static int read_file(int fd,const char *name,uint8_t *out,size_t cap,size_t *size)
{
 int file=openat(fd,name,O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);*size=0;
 if(file<0)return -errno;
 struct stat s;int rc=0;
 if(fstat(file,&s))rc=-errno;
 else if(!S_ISREG(s.st_mode) || s.st_uid!=0 || (s.st_mode&0777)!=0600 || s.st_nlink!=1 || s.st_size<1 || (uint64_t)s.st_size>cap)rc=-EPERM;
 else {
  size_t n=(size_t)s.st_size;
  while(*size<n){ssize_t count=read(file,out+*size,n-*size);if(count<0 && errno==EINTR)continue;if(count<=0){rc=count<0?-errno:-EIO;break;}*size+=(size_t)count;}
  uint8_t extra;if(!rc && read(file,&extra,1)!=0)rc=-EIO;
 }
 close(file);if(rc){explicit_bzero(out,cap);*size=0;}return rc;
}
static int absent(int fd,const char *name)
{
 struct stat s;if(!fstatat(fd,name,&s,AT_SYMLINK_NOFOLLOW))return 0;return errno==ENOENT?1:-errno;
}
static int create_file(int fd,const char *name,const uint8_t *data,size_t size)
{
 int file=openat(fd,name,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);if(file<0)return -errno;
 size_t offset=0;int rc=0;
 while(offset<size){ssize_t n=write(file,data+offset,size-offset);if(n<0 && errno==EINTR)continue;if(n<=0){rc=n<0?-errno:-EIO;break;}offset+=(size_t)n;}
 if(!rc && fsync(file))rc=-errno;
 if(close(file) && !rc)rc=-errno;
 if(!rc && fsync(fd))rc=-errno;
 /* Do not remove a partially written record and silently start over. */
 return rc;
}
int apollo_credential_load(int fd,uint8_t secret[32],uint8_t handle[512],size_t *handle_size)
{
 if(!secret || !handle || !handle_size)return -EINVAL;
 explicit_bzero(secret,32);explicit_bzero(handle,512);*handle_size=0;
 int rc=directory_ok(fd);if(rc)return rc;
 int p=absent(fd,"pending-v1"),s=absent(fd,"secret-v1"),h=absent(fd,"handle-v1");
 if(p<0 || s<0 || h<0)return -EIO;
 if(p==1 && s==1 && h==1)return 1;
 if(h==1 || (p==0 && s==0) || (p==1 && s==1))return -EINPROGRESS;
 size_t size=0;
 rc=read_file(fd,p==0?"pending-v1":"secret-v1",secret,32,&size);if(rc)goto bad;
 if(size!=32){rc=-EPROTO;goto bad;}
 rc=read_file(fd,"handle-v1",handle,512,handle_size);if(rc)goto bad;
 return p==0?2:0;
bad:explicit_bzero(secret,32);explicit_bzero(handle,512);*handle_size=0;return rc;
}
int apollo_credential_begin(int fd,const uint8_t secret[32])
{
 int rc=directory_ok(fd);if(rc)return rc;
 if(!secret)return -EINVAL;
 if(absent(fd,"pending-v1")!=1 || absent(fd,"secret-v1")!=1 || absent(fd,"handle-v1")!=1)return -EEXIST;
 return create_file(fd,"pending-v1",secret,32);
}
int apollo_credential_save_handle(int fd,const uint8_t *handle,size_t size)
{
 int rc=directory_ok(fd);if(rc)return rc;
 if(!handle || !size || size>512)return -EINVAL;
 uint8_t secret[32]={0};size_t n=0;rc=read_file(fd,"pending-v1",secret,sizeof secret,&n);explicit_bzero(secret,sizeof secret);
 if(rc)return rc;
 if(n!=32 || absent(fd,"secret-v1")!=1)return -EPROTO;
 return create_file(fd,"handle-v1",handle,size);
}
int apollo_credential_finish(int fd)
{
 uint8_t secret[32],handle[512];size_t n;int rc=apollo_credential_load(fd,secret,handle,&n);
 explicit_bzero(secret,sizeof secret);explicit_bzero(handle,sizeof handle);
 if(rc!=2)return rc<0?rc:-EINVAL;
 /* Atomic no-replacement rename: a crash leaves the complete credential or
  * the recoverable pending-secret + durable-handle pair, never an overwrite.
  */
 if(renameat2(fd,"pending-v1",fd,"secret-v1",RENAME_NOREPLACE))return -errno;
 if(fsync(fd))return -errno;
 return 0;
}
int apollo_credential_retry_unenrolled(int fd,uint8_t secret[32])
{
 if(!secret)return -EINVAL;
 explicit_bzero(secret,32);int rc=directory_ok(fd);if(rc)return rc;
 if(absent(fd,"handle-v1")!=1 || absent(fd,"secret-v1")!=1 || absent(fd,"pending-v1")!=0)return -EPERM;
 int marker=openat(fd,"retry-unenrolled-v1",O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);if(marker<0)return -errno;
 struct stat s;rc=fstat(marker,&s);close(marker);
 if(rc || !S_ISREG(s.st_mode) || s.st_uid!=0 || (s.st_mode&0777)!=0600 || s.st_nlink!=1 || s.st_size)return -EPERM;
 size_t size;rc=read_file(fd,"pending-v1",secret,32,&size);if(rc || size!=32){explicit_bzero(secret,32);return rc?rc:-EPROTO;}
 if(unlinkat(fd,"retry-unenrolled-v1",0) || fsync(fd)){rc=-errno;explicit_bzero(secret,32);return rc;}
 return 0;
}
