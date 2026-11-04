/* SPDX-License-Identifier: MIT */
#include "gatekeeper-wire.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static int all_zero(const uint8_t *p,size_t n){for(size_t i=0;i<n;i++)if(p[i])return 0;return 1;}
static void length_word(uint8_t *p,uint32_t n){for(unsigned i=0;i<4;i++)p[4+i]=(uint8_t)(n>>(8*i));}
int main(void)
{
 const uint32_t uid=0x4f4d0001;const uint64_t nonce=UINT64_C(0x0102030405060708);
 const uint8_t handle[]={0xaa,0xbb},secret[]={0xcc,0xdd};uint8_t out[2048];size_t len=0;
 const uint8_t expected_verify[]={2,0x10,2,0,0xa4,3,0x1a,0x4f,0x4d,0,1,4,0x1b,1,2,3,4,5,6,7,8,6,0x42,0xaa,0xbb,9,0x42,0xcc,0xdd};
 assert(apollo_gk_encode_verify(uid,nonce,handle,2,secret,2,out,sizeof out,&len)==0);
 assert(len==sizeof expected_verify && !memcmp(out,expected_verify,len));
 const uint8_t expected_enroll[]={1,0x10,2,0,0xa2,3,0x1a,0x4f,0x4d,0,1,8,0x42,0xcc,0xdd};
 assert(apollo_gk_encode_enroll(uid,secret,2,NULL,0,NULL,0,out,sizeof out,&len)==0);
 assert(len==sizeof expected_enroll && !memcmp(out,expected_enroll,len));
 assert(apollo_gk_encode_enroll(0,secret,2,NULL,0,NULL,0,out,sizeof out,&len)==-EINVAL && len==0 && all_zero(out,sizeof out));
 assert(apollo_gk_encode_enroll(uid,secret,2,handle,2,NULL,0,out,sizeof out,&len)==-EINVAL && all_zero(out,sizeof out));
 assert(apollo_gk_encode_verify(uid,0,handle,2,secret,2,out,sizeof out,&len)==-EINVAL && len==0 && all_zero(out,sizeof out));
 assert(apollo_gk_encode_verify(uid,nonce,handle,2,secret,2,out,5,&len)==-ENOSPC && len==0 && all_zero(out,5));
 uint8_t reply[80]={0},hat[69];
 const uint8_t body[]={0xa7,11,0,4,0x1b,1,2,3,4,5,6,7,8,12,0x1a,0x12,0x34,0x56,0x78,13,0,14,0x1a,1,0,0,0,15,0x1b,1,0,0,0,0,0,0,0,16,0x58,32};
 assert(sizeof body==40);memcpy(reply+8,body,40);memset(reply+48,0xa5,32);length_word(reply,72);
 assert(apollo_gk_decode_token(reply,sizeof reply,nonce,hat)==0);
 assert(hat[0]==0 && hat[1]==8 && hat[8]==1 && hat[9]==0x78 && hat[12]==0x12);
 assert(hat[25]==0 && hat[28]==1 && hat[29]==0 && hat[36]==1);
 for(unsigned i=37;i<69;i++)assert(hat[i]==0xa5);
 unsigned cases=7;
 for(size_t size=0;size<sizeof reply;size++){
  memset(hat,0xff,sizeof hat);assert(apollo_gk_decode_token(reply,size,nonce,hat)!=0 && all_zero(hat,sizeof hat));cases++;
 }
 assert(apollo_gk_decode_token(reply,sizeof reply,nonce+1,hat)==-EPROTO && all_zero(hat,sizeof hat));cases++;
 uint8_t original[80];memcpy(original,reply,sizeof reply);
 reply[8+19]=12;assert(apollo_gk_decode_token(reply,sizeof reply,nonce,hat)==-EPROTO && all_zero(hat,sizeof hat));cases++;
 memcpy(reply,original,sizeof reply);memset(reply+48,0,32);
 assert(apollo_gk_decode_token(reply,sizeof reply,nonce,hat)==-EPROTO && all_zero(hat,sizeof hat));cases++;
 memcpy(reply,original,sizeof reply);reply[8+39]=31;
 assert(apollo_gk_decode_token(reply,sizeof reply,nonce,hat)==-EPROTO && all_zero(hat,sizeof hat));cases++;
 memcpy(reply,original,sizeof reply);reply[8+39]=33;
 assert(apollo_gk_decode_token(reply,sizeof reply,nonce,hat)==-EPROTO && all_zero(hat,sizeof hat));cases++;
 memcpy(reply,original,sizeof reply);reply[0]=(uint8_t)-30;reply[1]=reply[2]=reply[3]=0xff;
 assert(apollo_gk_decode_token(reply,sizeof reply,nonce,hat)==-30 && all_zero(hat,sizeof hat));cases++;
 memcpy(reply,original,sizeof reply);reply[8+2]=1;
 assert(apollo_gk_decode_token(reply,sizeof reply,nonce,hat)==-EPROTO && all_zero(hat,sizeof hat));cases++;
 uint8_t hreply[]={0,0,0,0,5,0,0,0,0xa1,6,0x42,0xaa,0xbb},decoded[512];
 assert(apollo_gk_decode_handle(hreply,sizeof hreply,decoded,sizeof decoded,&len)==0 && len==2 && decoded[0]==0xaa && decoded[1]==0xbb);cases++;
 hreply[4]=255;assert(apollo_gk_decode_handle(hreply,sizeof hreply,decoded,sizeof decoded,&len)==-EPROTO && len==0 && all_zero(decoded,sizeof decoded));cases++;
 /* Deterministic malformed-data exercise, no genuine tokens or credentials. */
 uint32_t rng=0x49504d4f;uint8_t junk[256];
 for(unsigned iteration=0;iteration<12000;iteration++){
  size_t size=iteration%sizeof junk;
  for(size_t i=0;i<size;i++){rng=rng*1664525+1013904223;junk[i]=(uint8_t)(rng>>24);}
  int rc=apollo_gk_decode_token(junk,size,nonce,hat);
  assert(rc!=0 && all_zero(hat,sizeof hat));
 }
 printf("GATEKEEPER_WIRE_TESTS_OK cases=%u malformed_inputs=12000\n",cases);return 0;
}
