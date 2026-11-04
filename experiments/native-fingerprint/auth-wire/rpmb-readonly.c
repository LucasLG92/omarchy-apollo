/* SPDX-License-Identifier: MIT */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "rpmb-readonly.h"
#include <errno.h>
#include <string.h>
static uint32_t le(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static unsigned be16(const uint8_t *p){return (unsigned)p[0]<<8|p[1];}
static void put(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
int apollo_rpmb_readonly(void *buffer,size_t size,apollo_rpmb_read_fn reader,void *context,struct apollo_rpmb_read_metadata *m)
{
 if(!m)return -EINVAL;
 memset(m,0,sizeof *m);m->storage_status=-EOPNOTSUPP;
 if(!buffer || size<24 || size>APOLLO_RPMB_BUFFER)return -EINVAL;
 uint8_t *p=buffer;uint32_t command=le(p),count=le(p+4),length=le(p+8),offset=le(p+12),version=le(p+16);
 if(command>=0x101 && command<=0x104)m->operation=command;
 if(command!=0x102){uint32_t ignored;return apollo_rpmb_observe(buffer,size,&ignored);}
 uint8_t request[512]={0};int status=-EPROTO;
 if(size!=APOLLO_RPMB_BUFFER || !reader || !count || count>(size-20)/512 || length!=512 || offset<24 || offset>size || length>size-offset)goto respond;
 memcpy(request,p+offset,sizeof request);unsigned type=be16(request+510),blocks=be16(request+506);
 m->frames=count;m->request_type=(type==2 || type==4)?type:0;
 /* An outbound read request is not an authenticated write: allow only the
  * JEDEC read and counter-query operations, never key-program/write/result.
  */
 if((type!=2 && type!=4) || (type==2 && count!=1) || (type==4 && blocks && blocks!=count)){
  status=-EPERM;goto respond;
 }
 memset(p,0,size);status=reader(request,count,p+20,context);
 if(status){memset(p+20,0,size-20);goto respond;}
 for(uint32_t i=0;i<count;i++)if(be16(p+20+i*512+510)!=(type<<8)){
  status=-EPROTO;memset(p+20,0,size-20);goto respond;
 }
 put(p,command);put(p+4,0);put(p+8,count*512);put(p+12,20);put(p+16,version);
 m->storage_status=0;explicit_bzero(request,sizeof request);return 0;
respond:
 explicit_bzero(request,sizeof request);memset(p,0,size);
 if(size>=20){put(p,command);put(p+4,(uint32_t)status);put(p+12,20);put(p+16,version);}
 m->storage_status=status;return 0;
}
