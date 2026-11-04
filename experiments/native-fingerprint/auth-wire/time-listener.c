/* SPDX-License-Identifier: MIT
 * Wire layout independently implemented from Qualcomm MinkIPC time_msg.h,
 * commit939259cc69ee6358343a4968f732938b864799a6. QSEECOM delivery differs;
 * the numeric listener11 shared-buffer protocol is the same public interface.
 */
#define _POSIX_C_SOURCE 200809L
#include "time-listener.h"
#include <errno.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
static uint32_t word(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(uint8_t *p,uint64_t n,unsigned length){for(unsigned i=0;i<length;i++)p[i]=(uint8_t)(n>>(i*8));}
int apollo_time_reply(void *buffer,size_t size,int64_t seconds,int32_t nanoseconds)
{
 if(!buffer || size<8)return -EMSGSIZE;
 uint8_t *p=buffer;uint32_t command=word(p);size_t length;
 switch(command){case 0x302:case 0x305:length=16;break;case 0x303:length=44;break;case 0x304:length=12;break;case 0x306:length=8;break;default:put(p+4,UINT32_MAX,4);return 0;}
 if(size<length)return -EMSGSIZE;
 memset(p+4,0,length-4);
 if(command==0x306)return 0;
 if(seconds<0 || (uint64_t)seconds>UINT32_MAX || nanoseconds<0 || nanoseconds>=1000000000){
  if(command==0x304)put(p+4,UINT64_MAX,8);else put(p+length-4,UINT32_MAX,4);return 0;
 }
 if(command==0x302 || command==0x305){put(p+4,(uint64_t)seconds,4);put(p+8,(uint32_t)nanoseconds,4);return 0;}
 if(command==0x304){put(p+4,(uint64_t)seconds*1000+(uint32_t)nanoseconds/1000000,8);return 0;}
 time_t stamp=(time_t)seconds;struct tm calendar;
 if(!gmtime_r(&stamp,&calendar)){put(p+40,UINT32_MAX,4);return 0;}
 const int values[]={calendar.tm_sec,calendar.tm_min,calendar.tm_hour,calendar.tm_mday,calendar.tm_mon,calendar.tm_year,calendar.tm_wday,calendar.tm_yday,calendar.tm_isdst};
 for(unsigned i=0;i<9;i++)put(p+4+i*4,(uint32_t)values[i],4);
 return 0;
}
int apollo_time_dispatch(struct qs_store *unused,void *buffer,size_t size)
{
 (void)unused;struct timespec stamp;
 if(clock_gettime(CLOCK_REALTIME,&stamp))return apollo_time_reply(buffer,size,-1,0);
 return apollo_time_reply(buffer,size,stamp.tv_sec,(int32_t)stamp.tv_nsec);
}
