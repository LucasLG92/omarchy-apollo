/* SPDX-License-Identifier: MIT */
#include "gatekeeper-wire.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static void put(uint8_t *p,uint64_t n,unsigned size){for(unsigned i=0;i<size;i++)p[i]=(uint8_t)(n>>(8*i));}
static uint32_t word(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int zero(const uint8_t *p,size_t size){for(size_t i=0;i<size;i++)if(p[i])return 0;return 1;}
int main(void)
{
 uint8_t out[2048],secret[32],handle[58];size_t length=0;memset(secret,0xa5,sizeof secret);memset(handle,0x55,sizeof handle);
 uint32_t uid=0x4f4d0001;uint64_t challenge=UINT64_C(0x0102030405060708);
 assert(apollo_gk_encode_legacy_enroll(uid,secret,32,NULL,0,NULL,0,out,sizeof out,&length)==0 && length==64);
 assert(word(out)==0x1001 && word(out+4)==uid && zero(out+8,16) && word(out+24)==32 && word(out+28)==32 && !memcmp(out+32,secret,32));
 assert(apollo_gk_encode_legacy_enroll(uid,secret,32,handle,58,secret,32,out,sizeof out,&length)==0 && length==154);
 assert(word(out+8)==32 && word(out+12)==58 && word(out+16)==90 && word(out+20)==32 && word(out+24)==122);
 assert(apollo_gk_encode_legacy_verify(uid,challenge,handle,58,secret,32,out,sizeof out,&length)==0 && length==122);
 assert(word(out)==0x1002 && word(out+16)==32 && word(out+20)==58 && word(out+24)==90 && word(out+28)==32 && !memcmp(out+32,handle,58));
 assert(apollo_gk_encode_legacy_enroll(0,secret,32,NULL,0,NULL,0,out,sizeof out,&length)==-EINVAL && length==0 && zero(out,sizeof out));
 assert(apollo_gk_encode_legacy_enroll(uid,secret,32,handle,58,NULL,0,out,sizeof out,&length)==-EINVAL && zero(out,sizeof out));
 assert(apollo_gk_encode_legacy_verify(uid,challenge,handle,58,secret,32,out,64,&length)==-ENOSPC && zero(out,64));
 uint8_t reply[81]={0},token[69];put(reply+4,12,4);put(reply+8,69,4);put(reply+13,challenge,8);
 put(reply+21,0x12345678,8);reply[40]=1;reply[48]=1;memset(reply+49,0xa5,32);
 assert(apollo_gk_decode_legacy_token(reply,sizeof reply,challenge,token)==0 && !memcmp(token,reply+12,69));
 unsigned cases=7;
 for(size_t size=0;size<sizeof reply;size++){
  memset(token,0xff,sizeof token);assert(apollo_gk_decode_legacy_token(reply,size,challenge,token)!=0 && zero(token,sizeof token));cases++;
 }
 assert(apollo_gk_decode_legacy_token(reply,sizeof reply,challenge+1,token)==-EPROTO && zero(token,sizeof token));cases++;
 reply[8]=68;assert(apollo_gk_decode_legacy_token(reply,sizeof reply,challenge,token)==-EPROTO && zero(token,sizeof token));cases++;reply[8]=69;
 memset(reply+49,0,32);assert(apollo_gk_decode_legacy_token(reply,sizeof reply,challenge,token)==-EPROTO && zero(token,sizeof token));cases++;
 reply[0]=0xe2;reply[1]=reply[2]=reply[3]=0xff;assert(apollo_gk_decode_legacy_token(reply,sizeof reply,challenge,token)==-30 && zero(token,sizeof token));cases++;
 uint8_t hreply[70]={0},decoded[512];put(hreply+4,12,4);put(hreply+8,58,4);memcpy(hreply+12,handle,58);
 assert(apollo_gk_decode_legacy_handle(hreply,sizeof hreply,decoded,sizeof decoded,&length)==0 && length==58 && !memcmp(decoded,handle,58));cases++;
 put(hreply+4,UINT32_MAX,4);assert(apollo_gk_decode_legacy_handle(hreply,sizeof hreply,decoded,sizeof decoded,&length)==-EPROTO && length==0 && zero(decoded,sizeof decoded));cases++;
 printf("GATEKEEPER_LEGACY_TESTS_OK cases=%u\n",cases);return 0;
}
