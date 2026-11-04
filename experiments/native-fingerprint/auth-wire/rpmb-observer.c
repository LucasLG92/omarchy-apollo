/* SPDX-License-Identifier: MIT
 * Response layout: Qualcomm minkipc librpmbservice, pinned in research/.
 * This is a negative diagnostic endpoint, never a storage implementation.
 */
#include "rpmb-observer.h"
#include <errno.h>
#include <string.h>
static uint32_t le(const unsigned char *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(unsigned char *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(v>>(8*i));}
int apollo_rpmb_observe(void *buffer,size_t size,uint32_t *operation)
{
 if(operation)*operation=0;
 if(!buffer || !operation || size<8 || size>APOLLO_RPMB_BUFFER)return -EINVAL;
 unsigned char *p=buffer;uint32_t command=le(p),version=le(p+4);
 if(command>=0x101 && command<=0x104)*operation=command;
 if(size!=APOLLO_RPMB_BUFFER){memset(p,0,size);return -EINVAL;}
 if(command==0x102 || command==0x103)version=le(p+16);
 memset(p,0,size);put(p,command);
 switch(command){
 case 0x101:
  put(p+4,version>=2?2:1);put(p+8,(uint32_t)-EOPNOTSUPP);break;
 case 0x102:case 0x103:
  put(p+4,(uint32_t)-EOPNOTSUPP);put(p+12,20);put(p+16,version);break;
 case 0x104:
  put(p+4,(uint32_t)-EOPNOTSUPP);put(p+12,16);break;
 default:return -EOPNOTSUPP;
 }
 return 0;
}
