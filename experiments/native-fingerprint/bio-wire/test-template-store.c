/* SPDX-License-Identifier: MIT. Tests phone record format on a temporary FS. */
#define main biometric_unused_entry
#include "../apollo-biometric-trial.c"
#undef main
#include <assert.h>
int main(void)
{
 char temp[]="/tmp/apollo-template-test-XXXXXX";assert(mkdtemp(temp));
 int fd=open(temp,O_RDONLY|O_DIRECTORY|O_CLOEXEC);assert(fd>=0);
 uint8_t blob[9001]={0};put(blob,sizeof blob-52);memset(blob+4,0xa5,sizeof blob-4);
 uint8_t *data=0;size_t size=0;uint32_t id=0;
 assert(read_store(fd,&data,&size,&id)==-ENOENT && !data);
 assert(!save_first(fd,blob,sizeof blob,1234));assert(!read_store(fd,&data,&size,&id));
 assert(id==1234 && size==sizeof blob && !memcmp(data,blob,size));free(data);
 assert(fchmodat(fd,"enrolled-v1",0644,0)==0);assert(read_store(fd,&data,&size,&id)==-EPROTO && !data);
 assert(fchmodat(fd,"enrolled-v1",0600,0)==0);
 assert(linkat(fd,"enrolled-v1",fd,"hardlink",0)==0);assert(read_store(fd,&data,&size,&id)==-EPROTO && !data);assert(!unlinkat(fd,"hardlink",0));
 assert(save_first(fd,blob,sizeof blob,5678)==-EEXIST);assert(!read_store(fd,&data,&size,&id) && id==1234);free(data);
 assert(!unlinkat(fd,"pending-enrollment-v1",0));assert(!unlinkat(fd,"enrolled-v1",0));
 assert(!symlinkat("/dev/null",fd,"enrolled-v1"));assert(read_store(fd,&data,&size,&id)==-ELOOP);assert(!unlinkat(fd,"enrolled-v1",0));
 assert(save_first(fd,blob,sizeof blob,0)==-EINVAL);
 close(fd);assert(!rmdir(temp));puts("Apollo template store: atomic first commit, no replacement, permissions, hardlinks and symlinks passed");
}
