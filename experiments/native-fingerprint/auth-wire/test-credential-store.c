/* SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include "credential-store.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static int zero(const uint8_t *p,size_t n){for(size_t i=0;i<n;i++)if(p[i])return 0;return 1;}
static int fresh(void){char name[]="/tmp/apollo-credential-test-XXXXXX";assert(mkdtemp(name));return open(name,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);}
static void check_bad(int fd){uint8_t s[32],h[512];size_t n=999;memset(s,1,32);memset(h,1,512);assert(apollo_credential_load(fd,s,h,&n)<0 && !n && zero(s,32) && zero(h,512));}
int main(void)
{
 uint8_t secret[32],handle[58],s[32],h[512];size_t n;memset(secret,0xa5,32);memset(handle,0x55,58);
 int fd=fresh();assert(fd>=0);assert(apollo_credential_load(fd,s,h,&n)==1 && !n && zero(s,32));
 assert(apollo_credential_begin(fd,secret)==0);check_bad(fd);
 assert(apollo_credential_begin(fd,secret)==-EEXIST);
 assert(apollo_credential_save_handle(fd,handle,58)==0);
 assert(apollo_credential_load(fd,s,h,&n)==2 && n==58 && !memcmp(s,secret,32) && !memcmp(h,handle,58));
 assert(apollo_credential_save_handle(fd,handle,58)==-EEXIST);
 assert(apollo_credential_finish(fd)==0);
 assert(apollo_credential_load(fd,s,h,&n)==0 && n==58 && !memcmp(s,secret,32));
 assert(apollo_credential_begin(fd,secret)==-EEXIST);assert(apollo_credential_finish(fd)==-EINVAL);
 assert(fchmodat(fd,"secret-v1",0644,0)==0);check_bad(fd);close(fd);
 fd=fresh();assert(symlinkat("/dev/null",fd,"secret-v1")==0);check_bad(fd);assert(apollo_credential_begin(fd,secret)==-EEXIST);close(fd);
 fd=fresh();assert(apollo_credential_begin(fd,secret)==0);assert(apollo_credential_save_handle(fd,handle,58)==0);
 assert(linkat(fd,"pending-v1",fd,"other",0)==0);check_bad(fd);close(fd);
 fd=fresh();assert(apollo_credential_begin(fd,secret)==0);assert(apollo_credential_save_handle(fd,handle,58)==0);
 assert(linkat(fd,"pending-v1",fd,"secret-v1",0)==0);check_bad(fd);close(fd);
 fd=fresh();assert(fchmod(fd,0755)==0);check_bad(fd);assert(apollo_credential_begin(fd,secret)==-EPERM);close(fd);
 fd=fresh();assert(apollo_credential_begin(fd,secret)==0);assert(apollo_credential_save_handle(fd,handle,58)==0);
 int f=openat(fd,"pending-v1",O_WRONLY|O_TRUNC);assert(f>=0 && write(f,secret,1)==1);close(f);check_bad(fd);close(fd);
 fd=fresh();assert(mkfifoat(fd,"pending-v1",0600)==0);check_bad(fd);close(fd);
 fd=fresh();assert(apollo_credential_begin(fd,secret)==0);assert(apollo_credential_save_handle(fd,handle,58)==0);
 assert(fchownat(fd,"handle-v1",65534,65534,0)==0);check_bad(fd);close(fd);
 fd=fresh();assert(apollo_credential_begin(fd,secret)==0);
 assert(apollo_credential_retry_unenrolled(fd,s)<0 && zero(s,32));
 f=openat(fd,"retry-unenrolled-v1",O_WRONLY|O_CREAT|O_EXCL,0600);assert(f>=0);close(f);
 assert(apollo_credential_retry_unenrolled(fd,s)==0 && !memcmp(s,secret,32));
 assert(apollo_credential_retry_unenrolled(fd,s)<0 && zero(s,32));
 assert(apollo_credential_save_handle(fd,handle,58)==0);
 f=openat(fd,"retry-unenrolled-v1",O_WRONLY|O_CREAT|O_EXCL,0600);assert(f>=0);close(f);
 assert(apollo_credential_retry_unenrolled(fd,s)<0 && zero(s,32));close(fd);
 fd=fresh();assert(apollo_credential_begin(fd,secret)==0);assert(symlinkat("pending-v1",fd,"retry-unenrolled-v1")==0);
 assert(apollo_credential_retry_unenrolled(fd,s)<0 && zero(s,32));close(fd);
 fd=fresh();assert(apollo_credential_begin(fd,secret)==0);
 f=openat(fd,"retry-unenrolled-v1",O_WRONLY|O_CREAT|O_EXCL,0644);assert(f>=0);close(f);
 assert(apollo_credential_retry_unenrolled(fd,s)<0 && zero(s,32));close(fd);
 puts("CREDENTIAL_STORE_TESTS_OK interrupted-provisioning ownership symlink hardlink FIFO truncation no-overwrite");return 0;
}
