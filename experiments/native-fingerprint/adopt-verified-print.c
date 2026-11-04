/* SPDX-License-Identifier: MIT. Adopt metadata for the real, tested TA print.
 * No image/template export, TA mutation, replacement or new enrollment.
 */
#define _GNU_SOURCE
#include <fprint.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <pwd.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static uint32_t word(const unsigned char *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int directory(int parent,const char *name)
{
 if(mkdirat(parent,name,0700) && errno!=EEXIST)return -1;
 int fd=openat(parent,name,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);struct stat s;
 if(fd<0 || fstat(fd,&s) || s.st_uid!=0 || (s.st_mode&0777)!=0700){if(fd>=0)close(fd);return -1;}return fd;
}
int main(int argc,char **argv)
{
 if(argc!=2 || strcmp(argv[1],"--adopt-verified-right-index") || geteuid())return 2;
 struct passwd *owner=getpwuid(1000);if(!owner || !owner->pw_name || strlen(owner->pw_name)>63 || !(islower(owner->pw_name[0]) || owner->pw_name[0]=='_'))return 3;
 for(const char *c=owner->pw_name;*c;c++)if(!isalnum((unsigned char)*c) && *c!='_' && *c!='-' && *c!='.')return 3;
 int record=open("/var/lib/apollo/fingerprint-templates-v1/u1000/enrolled-v1",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);struct stat s;unsigned char header[24];
 if(record<0 || fstat(record,&s) || !S_ISREG(s.st_mode) || s.st_uid!=0 || (s.st_mode&0777)!=0600 || s.st_nlink!=1 || s.st_size<76 || s.st_size>4*1024*1024+24 || read(record,header,sizeof header)!=sizeof header){if(record>=0)close(record);return 4;}close(record);
 if(memcmp(header,"APFPC001",8) || word(header+8)!=1000 || !word(header+12) || word(header+16)!=FP_FINGER_RIGHT_INDEX || word(header+20)+24!=(uint64_t)s.st_size)return 4;
 guint32 identity=word(header+12);explicit_bzero(header,sizeof header);
 g_setenv("FP_APOLLO_FPC","/run/apollo-fingerprint/bridge.sock",TRUE);
 g_autoptr(FpContext) context=fp_context_new();fp_context_enumerate(context);GPtrArray *devices=fp_context_get_devices(context);FpDevice *device=NULL;
 for(guint i=0;i<devices->len;i++){FpDevice *candidate=g_ptr_array_index(devices,i);if(!strcmp(fp_device_get_driver(candidate),"apollo_fpc")){if(device)return 5;device=candidate;}}
 if(!device || strcmp(fp_device_get_device_id(device),"apollo-fpc-tee-v1"))return 5;
 g_autoptr(GError) error=NULL;if(!fp_device_open_sync(device,NULL,&error))return 6;
 g_autoptr(GPtrArray) prints=fp_device_list_prints_sync(device,NULL,&error);int rc=7;
 g_autoptr(GVariant) data=NULL;g_autofree guchar *serialized=NULL;gsize size=0;
 if(!prints || prints->len!=1)goto close_device;
 FpPrint *print=g_ptr_array_index(prints,0);g_object_get(print,"fpi-data",&data,NULL);
 if(!data || !g_variant_is_of_type(data,G_VARIANT_TYPE("(i)")) || fp_print_get_image(print))goto close_device;
 gint32 found=0;g_variant_get(data,"(i)",&found);if((guint32)found!=identity)goto close_device;
 fp_print_set_username(print,owner->pw_name);fp_print_set_finger(print,FP_FINGER_RIGHT_INDEX);fp_print_set_description(print,"Lector lateral del Apollo");
 if(!fp_print_serialize(print,&serialized,&size,&error) || !size || size>4096)goto close_device;
 int root=open("/var/lib",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(root<0)goto close_device;
 const char *names[]={"fprint",owner->pw_name,"apollo_fpc","apollo-fpc-tee-v1"};
 for(unsigned i=0;i<4;i++){int next=directory(root,names[i]);close(root);root=next;if(root<0)goto close_device;}
 int fd=openat(root,"7",O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);
 if(fd>=0){
  unsigned char existing[4096];struct stat old;ssize_t n=read(fd,existing,sizeof existing);
  int same=!fstat(fd,&old) && S_ISREG(old.st_mode) && old.st_uid==0 && (old.st_mode&0777)==0600 && old.st_nlink==1 && n==(ssize_t)size && old.st_size==(off_t)size && !memcmp(existing,serialized,size);
  explicit_bzero(existing,sizeof existing);close(fd);close(root);rc=same?0:8;goto close_device;
 }
 if(errno!=ENOENT){close(root);goto close_device;}
 fd=openat(root,"7.pending-apollo",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);if(fd<0){close(root);goto close_device;}
 size_t pos=0;while(pos<size){ssize_t n=write(fd,serialized+pos,size-pos);if(n<0 && errno==EINTR)continue;if(n<=0)break;pos+=(size_t)n;}
 int saved=pos==size && fsync(fd)==0;close(fd);
 if(saved && renameat2(root,"7.pending-apollo",root,"7",RENAME_NOREPLACE)==0 && fsync(root)==0)rc=0;
 close(root);
close_device:
 if(!fp_device_close_sync(device,NULL,NULL) && !rc)rc=9;
 printf("{\"ok\":%s,\"existing_verified_print_metadata_adopted\":%s,\"biometric_bytes_exported\":false,\"templates_changed\":false}\n",rc?"false":"true",rc?"false":"true");return rc;
}
