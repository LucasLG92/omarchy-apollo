/* SPDX-License-Identifier: MIT */
#include "rpmb-authenticated.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static uint8_t data[APOLLO_RPMB_BUFFER+2];static unsigned calls;static int fail,error,malformed;
static uint32_t le(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(uint8_t *p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i));}
static void packet(unsigned type,uint32_t count,uint32_t batch){memset(data,0xa5,sizeof data);uint8_t *p=data+1;memset(p,0,APOLLO_RPMB_BUFFER);put(p,0x103);put(p+4,count);put(p+8,count*512);put(p+12,24);put(p+16,1);put(p+20,batch);for(unsigned i=0;i<count && i<39;i++){p[24+i*512+511]=type;p[24+i*512+507]=batch;}}
static int writer(const uint8_t *frames,uint32_t n,uint8_t result[512],void *ctx){(void)ctx;calls++;for(unsigned i=0;i<n;i++)assert(frames[i*512+510]==0 && frames[i*512+511]==3 && frames[i*512+507]==n);memset(result,0,512);result[510]=malformed?0:3;result[509]=error?2:0;return fail?-EIO:0;}
int main(void){uint8_t *p=data+1;struct apollo_rpmb_read_metadata m;unsigned cases=0;
 for(unsigned type=0;type<256;type++){packet(type,1,1);unsigned before=calls;assert(apollo_rpmb_authenticated(p,APOLLO_RPMB_BUFFER,0,writer,0,&m)==0);assert(calls-before==(type==3?1u:0u));cases++;}
 for(unsigned n=0;n<50;n++)for(unsigned batch=0;batch<50;batch++){
  packet(3,n,batch);unsigned before=calls;apollo_rpmb_authenticated(p,APOLLO_RPMB_BUFFER,0,writer,0,&m);
  unsigned good=n && n<=39 && batch && batch<=n && n%batch==0;assert(calls-before==(good?n/batch:0));assert((le(p+4)==0)==(good!=0));cases++;
 }
 for(size_t size=0;size<APOLLO_RPMB_BUFFER;size++){packet(3,1,1);unsigned before=calls;apollo_rpmb_authenticated(p,size,0,writer,0,&m);assert(calls==before && data[0]==0xa5 && data[APOLLO_RPMB_BUFFER+1]==0xa5);cases++;}
 for(unsigned which=0;which<3;which++){packet(3,3,1);fail=which==0;error=which==1;malformed=which==2;unsigned before=calls;apollo_rpmb_authenticated(p,APOLLO_RPMB_BUFFER,0,writer,0,&m);assert(calls==before+1 && (int32_t)le(p+4)<0 && le(p+8)==0);cases++;}
 printf("PASS %u authenticated-write validation cases; key programming denied and partial failures stop\n",cases);return 0;}
