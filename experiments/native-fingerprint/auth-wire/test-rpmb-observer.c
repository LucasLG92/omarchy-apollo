/* SPDX-License-Identifier: MIT */
#include "rpmb-observer.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static unsigned char data[APOLLO_RPMB_BUFFER+2];
static uint32_t le(unsigned char *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(unsigned char *p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(n>>(8*i));}
int main(void){unsigned cases=0;uint32_t op=7;unsigned char *p=data+1;
 assert(apollo_rpmb_observe(NULL,APOLLO_RPMB_BUFFER,&op)==-EINVAL && op==0);cases++;
 assert(apollo_rpmb_observe(p,APOLLO_RPMB_BUFFER,NULL)==-EINVAL);cases++;
 for(size_t size=0;size<=APOLLO_RPMB_BUFFER+1;size++){
  memset(data,0xa5,sizeof data);op=7;int r=apollo_rpmb_observe(p,size,&op);
  assert(r<0 && op==0 && data[0]==0xa5 && data[APOLLO_RPMB_BUFFER+1]==0xa5);cases++;
 }
 for(uint32_t command=0x101;command<=0x104;command++)for(uint32_t version=0;version<4;version++){
  memset(data,0xa5,sizeof data);put(p,command);put(p+4,version);put(p+16,version);
  assert(apollo_rpmb_observe(p,APOLLO_RPMB_BUFFER,&op)==0 && op==command && le(p)==command);
  assert((int32_t)le(p+(command==0x101?8:4))==-EOPNOTSUPP);
  assert(data[0]==0xa5 && data[APOLLO_RPMB_BUFFER+1]==0xa5);
  for(size_t i=40;i<APOLLO_RPMB_BUFFER;i++)assert(p[i]==0);
  if(command==0x101)assert(le(p+12)==0 && le(p+16)==0);
  else assert(le(p+8)==0);
  cases++;
 }
 printf("PASS %u negative observer boundary and response cases; storage IO absent\n",cases);return 0;
}
