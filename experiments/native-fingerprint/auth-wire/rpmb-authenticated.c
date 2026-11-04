/* SPDX-License-Identifier: MIT */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "rpmb-authenticated.h"
#include <errno.h>
#include <string.h>
static uint32_t le(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static unsigned be16(const uint8_t *p){return (unsigned)p[0]<<8|p[1];}
static void put(uint8_t *p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i));}
int apollo_rpmb_authenticated(void *buffer,size_t size,apollo_rpmb_read_fn reader,apollo_rpmb_write_fn writer,void *context,struct apollo_rpmb_read_metadata *m)
{
 if(!buffer || size<24 || size>APOLLO_RPMB_BUFFER || !m)return -EINVAL;
 uint8_t *p=buffer;
 if(le(p)!=0x103)return apollo_rpmb_readonly(buffer,size,reader,context,m);
 memset(m,0,sizeof *m);m->operation=0x103;m->storage_status=-EPROTO;
 uint32_t count=le(p+4),length=le(p+8),offset=le(p+12),version=le(p+16),batch=le(p+20);
 uint8_t request[39*512]={0},result[512]={0};int rc=-EPROTO;
 if(size!=APOLLO_RPMB_BUFFER || !writer || !count || count>39 || !batch || batch>count || count%batch || length!=count*512 || offset<24 || offset>size || length>size-offset)goto out;
 memcpy(request,p+offset,length);m->frames=count;
 /* Hardware verifies each MAC/counter. Host must not send a frame capable
  * of programming/replacing the RPMB key, even if the outer opcode is write.
  */
 for(uint32_t i=0;i<count;i++)if(be16(request+i*512+510)!=3 || be16(request+i*512+506)!=batch){rc=-EPERM;goto out;}
 m->request_type=3;
 for(uint32_t start=0;start<count;start+=batch){
  rc=writer(request+start*512,batch,result,context);if(rc)goto out;
  if(be16(result+510)!=0x300 || be16(result+508)!=0){rc=-EIO;goto out;}
 }
 rc=0;
out:
 memset(p,0,size);put(p,0x103);put(p+4,(uint32_t)rc);put(p+12,20);put(p+16,version);
 if(!rc){put(p+8,512);memcpy(p+20,result,512);}
 m->storage_status=rc;explicit_bzero(request,sizeof request);explicit_bzero(result,sizeof result);return 0;
}
