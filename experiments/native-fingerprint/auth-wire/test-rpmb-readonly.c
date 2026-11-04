/* SPDX-License-Identifier: MIT */
#include "rpmb-readonly.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static uint8_t data[APOLLO_RPMB_BUFFER+2];static unsigned calls;static int fail,wrong;
static void put(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
static uint32_t le(uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int reader(const uint8_t *req,uint32_t n,uint8_t *res,void *ctx){(void)ctx;calls++;assert(req[510]==0 && (req[511]==2 || req[511]==4));
 memset(res,0x5a,n*512);for(uint32_t i=0;i<n;i++){res[i*512+510]=wrong?0: req[511];res[i*512+511]=0;}return fail?-EIO:0;}
static void packet(unsigned type,uint32_t count){memset(data,0xa5,sizeof data);uint8_t *p=data+1;memset(p,0,APOLLO_RPMB_BUFFER);put(p,0x102);put(p+4,count);put(p+8,512);put(p+12,24);put(p+16,1);p[24+511]=type;}
int main(void){unsigned cases=0;uint8_t *p=data+1;struct apollo_rpmb_read_metadata m;
 for(size_t size=0;size<APOLLO_RPMB_BUFFER;size++){packet(4,1);unsigned before=calls;assert(apollo_rpmb_readonly(p,size,reader,0,&m)<=0 && calls==before);assert(data[0]==0xa5 && data[APOLLO_RPMB_BUFFER+1]==0xa5);cases++;}
 for(unsigned type=0;type<256;type++){packet(type,1);unsigned before=calls;assert(apollo_rpmb_readonly(p,APOLLO_RPMB_BUFFER,reader,0,&m)==0);assert(calls-before==((type==2 || type==4)?1:0));cases++;}
 for(unsigned n=0;n<80;n++){packet(4,n);unsigned before=calls;apollo_rpmb_readonly(p,APOLLO_RPMB_BUFFER,reader,0,&m);int good=n && n<40;assert(calls-before==(unsigned)good);assert(le(p+8)==(good?n*512:0));cases++;}
 for(unsigned offset=0;offset<APOLLO_RPMB_BUFFER+3;offset++){packet(4,1);put(p+12,offset);unsigned before=calls;apollo_rpmb_readonly(p,APOLLO_RPMB_BUFFER,reader,0,&m);assert(calls-before==(offset==24?1u:0u));assert(data[0]==0xa5 && data[APOLLO_RPMB_BUFFER+1]==0xa5);cases++;}
 for(unsigned which=0;which<2;which++){packet(4,1);fail=which==0;wrong=which==1;apollo_rpmb_readonly(p,APOLLO_RPMB_BUFFER,reader,0,&m);assert((int32_t)le(p+4)<0 && le(p+8)==0);for(unsigned i=20;i<APOLLO_RPMB_BUFFER;i++)assert(p[i]==0);cases++;}
 printf("PASS %u read-only parser/IO-isolation cases; key programming and writes blocked\n",cases);return 0;}
