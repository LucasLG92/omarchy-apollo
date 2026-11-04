/* SPDX-License-Identifier: MIT */
#include "time-listener.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static uint64_t get(const uint8_t *p,unsigned n){uint64_t v=0;for(unsigned i=0;i<n;i++)v|=(uint64_t)p[i]<<(8*i);return v;}
static void put(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
int main(void)
{
 uint8_t b[64];unsigned cases=0;const unsigned commands[]={0x302,0x303,0x304,0x305,0x306};
 for(unsigned c=0;c<5;c++){
  unsigned need=commands[c]==0x303?44:commands[c]==0x304?12:commands[c]==0x306?8:16;
  for(unsigned n=0;n<need;n++){
   memset(b,0xa5,sizeof b);put(b,commands[c]);uint8_t original[64];memcpy(original,b,64);
   assert(apollo_time_reply(b,n,0,0)==-EMSGSIZE && !memcmp(b,original,64));cases++;
  }
  memset(b,0xa5,sizeof b);put(b,commands[c]);assert(apollo_time_reply(b,need,0,0)==0 && get(b,4)==commands[c]);
  for(unsigned n=need;n<64;n++)assert(b[n]==0xa5);cases++;
 }
 put(b,0x302);assert(apollo_time_reply(b,64,1704067200,123456789)==0 && get(b+4,4)==1704067200 && get(b+8,4)==123456789 && !get(b+12,4));cases++;
 put(b,0x303);assert(apollo_time_reply(b,64,1704067200,0)==0 && get(b+16,4)==1 && get(b+20,4)==0 && get(b+24,4)==124 && get(b+28,4)==1 && !get(b+40,4));cases++;
 put(b,0x304);assert(apollo_time_reply(b,64,1704067200,1000000)==0 && get(b+4,8)==UINT64_C(1704067200001));cases++;
 put(b,0x302);assert(apollo_time_reply(b,64,-1,0)==0 && get(b+12,4)==UINT32_MAX && !get(b+4,8));cases++;
 put(b,0x304);assert(apollo_time_reply(b,64,0,1000000000)==0 && get(b+4,8)==UINT64_MAX);cases++;
 put(b,0x301);assert(apollo_time_reply(b,64,0,0)==0 && get(b+4,4)==UINT32_MAX);cases++;
 assert(apollo_time_reply(NULL,64,0,0)==-EMSGSIZE);cases++;
 printf("TIME_LISTENER_TESTS_OK cases=%u\n",cases);return 0;
}
