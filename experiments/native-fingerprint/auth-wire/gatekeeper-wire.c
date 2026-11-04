/* SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include "gatekeeper-wire.h"
#include <errno.h>
#include <stdbool.h>
#include <string.h>
static uint32_t le32(const uint8_t *p)
{return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put_le(uint8_t *p,uint64_t n,unsigned len)
{for(unsigned i=0;i<len;i++)p[i]=(uint8_t)(n>>(8*i));}
static uint64_t be(const uint8_t *p,unsigned len)
{uint64_t n=0;for(unsigned i=0;i<len;i++)n=(n<<8)|p[i];return n;}
struct writer {uint8_t *p;size_t cap,n;bool bad;};
static void byte(struct writer *w,uint8_t n)
{if(w->n>=w->cap)w->bad=true;else w->p[w->n++]=n;}
static void number(struct writer *w,unsigned major,uint64_t n)
{
 if(n<24){byte(w,(uint8_t)(major*32+n));return;}
 unsigned count=n<=UINT8_MAX?1:n<=UINT16_MAX?2:n<=UINT32_MAX?4:8;
 byte(w,(uint8_t)(major*32+(count==1?24:count==2?25:count==4?26:27)));
 for(unsigned i=count;i>0;i--)byte(w,(uint8_t)(n>>(8*(i-1))));
}
static void uint_pair(struct writer *w,unsigned key,uint64_t n)
{number(w,0,key);number(w,0,n);}
static void bytes_pair(struct writer *w,unsigned key,const uint8_t *p,size_t size)
{number(w,0,key);number(w,2,size);for(size_t i=0;i<size;i++)byte(w,p[i]);}
static int begin(struct writer *w,uint32_t uid,uint32_t command,uint8_t *output,size_t capacity,size_t *length)
{
 if(length)*length=0;
 if(!output || !length || capacity<4 || capacity>APOLLO_GK_MAX_MESSAGE)return -EINVAL;
 memset(output,0,capacity);
 if(uid<APOLLO_GK_UID_FIRST || uid>APOLLO_GK_UID_LAST)return -EINVAL;
 put_le(output,command,4);*w=(struct writer){.p=output,.cap=capacity,.n=4};return 0;
}
static int finish(struct writer *w,size_t *length)
{
 if(w->bad){explicit_bzero(w->p,w->cap);return -ENOSPC;}
 *length=w->n;return 0;
}
int apollo_gk_encode_enroll(uint32_t uid,const uint8_t *secret,size_t secret_len,
 const uint8_t *old_handle,size_t handle_len,const uint8_t *old_secret,size_t old_secret_len,
 uint8_t *output,size_t capacity,size_t *length)
{
 struct writer w;int rc=begin(&w,uid,0x21001,output,capacity,length);if(rc)return rc;
 if(!secret || !secret_len || secret_len>128 || handle_len>APOLLO_GK_MAX_HANDLE || old_secret_len>128 ||
    (!!old_handle!=!!handle_len) || (!!old_secret!=!!old_secret_len) || (!!old_handle!=!!old_secret)){
  explicit_bzero(output,capacity);return -EINVAL;
 }
 number(&w,5,old_handle?4:2);uint_pair(&w,3,uid);
 if(old_handle){bytes_pair(&w,5,old_handle,handle_len);bytes_pair(&w,7,old_secret,old_secret_len);}
 bytes_pair(&w,8,secret,secret_len);return finish(&w,length);
}
int apollo_gk_encode_verify(uint32_t uid,uint64_t challenge,const uint8_t *handle,size_t handle_len,
 const uint8_t *secret,size_t secret_len,uint8_t *output,size_t capacity,size_t *length)
{
 struct writer w;int rc=begin(&w,uid,0x21002,output,capacity,length);if(rc)return rc;
 if(!challenge || !handle || !handle_len || handle_len>APOLLO_GK_MAX_HANDLE || !secret || !secret_len || secret_len>128){
  explicit_bzero(output,capacity);return -EINVAL;
 }
 number(&w,5,4);uint_pair(&w,3,uid);uint_pair(&w,4,challenge);
 bytes_pair(&w,6,handle,handle_len);bytes_pair(&w,9,secret,secret_len);return finish(&w,length);
}
struct reader {const uint8_t *p;size_t n,pos;};
struct field {uint8_t type;uint64_t value;const uint8_t *bytes;};
static int item(struct reader *r,unsigned *major,uint64_t *value)
{
 if(r->pos>=r->n)return -EPROTO;
 uint8_t head=r->p[r->pos++];*major=head>>5;unsigned extra=head&31;
 if(extra<24){*value=extra;return 0;}
 unsigned count=extra==24?1:extra==25?2:extra==26?4:extra==27?8:0;
 if(!count || count>r->n-r->pos)return -EPROTO;
 *value=be(r->p+r->pos,count);r->pos+=count;
 if((count==1 && *value<24) || (count==2 && *value<=UINT8_MAX) ||
    (count==4 && *value<=UINT16_MAX) || (count==8 && *value<=UINT32_MAX))return -EPROTO;
 return 0;
}
static int fields(const uint8_t *response,size_t size,struct field found[17])
{
 if(!response || size<8)return -EINVAL;
 int32_t status=(int32_t)le32(response);if(status)return status;
 uint32_t length=le32(response+4);
 if(!length || length>APOLLO_GK_MAX_MESSAGE || length>size-8)return -EPROTO;
 struct reader r={.p=response+8,.n=length};unsigned major;uint64_t count;uint32_t seen=0;
 if(item(&r,&major,&count) || major!=5 || count>16)return -EPROTO;
 for(uint64_t i=0;i<count;i++){
  uint64_t key,value;
  if(item(&r,&major,&key) || major!=0 || key>16 || (seen&(1u<<key)))return -EPROTO;
  seen|=1u<<key;
  if(item(&r,&major,&value))return -EPROTO;
  if(major==0)found[key]=(struct field){.type=1,.value=value};
  else if(major==2 && value<=r.n-r.pos){
   found[key]=(struct field){.type=2,.value=value,.bytes=r.p+r.pos};r.pos+=(size_t)value;
  }else return -EPROTO;
 }
 return r.pos==r.n?0:-EPROTO;
}
int apollo_gk_decode_handle(const uint8_t *response,size_t size,uint8_t *handle,size_t capacity,size_t *length)
{
 if(length)*length=0;
 if(!handle || !length || !capacity || capacity>APOLLO_GK_MAX_HANDLE)return -EINVAL;
 memset(handle,0,capacity);struct field values[17]={0};int rc=fields(response,size,values);if(rc)return rc;
 const struct field *h=&values[6];
 if(h->type!=2 || !h->value || h->value>capacity)return -EPROTO;
 memcpy(handle,h->bytes,(size_t)h->value);*length=(size_t)h->value;return 0;
}
int apollo_gk_decode_token(const uint8_t *response,size_t size,uint64_t expected_challenge,uint8_t token[APOLLO_GK_HAT_SIZE])
{
 if(!token)return -EINVAL;
 memset(token,0,APOLLO_GK_HAT_SIZE);
 if(!expected_challenge)return -EINVAL;
 struct field values[17]={0};int rc=fields(response,size,values);if(rc)return rc;
 const unsigned required[]={4,11,12,13,14,15};
 for(unsigned i=0;i<6;i++)if(values[required[i]].type!=1)return -EPROTO;
 if(values[11].value!=0 || values[4].value!=expected_challenge || !values[12].value ||
    values[14].value>UINT32_MAX || values[16].type!=2 || values[16].value!=32)return -EPROTO;
 uint8_t scratch[APOLLO_GK_HAT_SIZE]={0};
 put_le(scratch+1,values[4].value,8);put_le(scratch+9,values[12].value,8);put_le(scratch+17,values[13].value,8);
 put_le(scratch+25,values[14].value,4);put_le(scratch+29,values[15].value,8);
 unsigned nonzero=0;for(unsigned i=0;i<32;i++)nonzero|=values[16].bytes[i];
 if(!(be(scratch+25,4)&1) || !be(scratch+29,8) || !nonzero){explicit_bzero(scratch,sizeof scratch);return -EPROTO;}
 memcpy(scratch+37,values[16].bytes,32);memcpy(token,scratch,sizeof scratch);explicit_bzero(scratch,sizeof scratch);return 0;
}

static int legacy_begin(uint32_t uid,uint32_t command,uint8_t *out,size_t cap,size_t *length)
{
 if(length)*length=0;
 if(!out || !length || cap>APOLLO_GK_MAX_MESSAGE || cap<32)return -EINVAL;
 memset(out,0,cap);
 if(uid<APOLLO_GK_UID_FIRST || uid>APOLLO_GK_UID_LAST)return -EINVAL;
 put_le(out,command,4);put_le(out+4,uid,4);return 0;
}
int apollo_gk_encode_legacy_enroll(uint32_t uid,const uint8_t *secret,size_t secret_len,
 const uint8_t *old_handle,size_t handle_len,const uint8_t *old_secret,size_t old_secret_len,
 uint8_t *output,size_t capacity,size_t *length)
{
 int rc=legacy_begin(uid,0x1001,output,capacity,length);if(rc)return rc;
 if(!secret || !secret_len || secret_len>128 || handle_len>APOLLO_GK_MAX_HANDLE || old_secret_len>128 ||
    (!!old_handle!=!!handle_len) || (!!old_secret!=!!old_secret_len) || (!!old_handle!=!!old_secret)){
  explicit_bzero(output,capacity);return -EINVAL;
 }
 size_t size=32+secret_len+handle_len+old_secret_len;
 if(size>capacity){explicit_bzero(output,capacity);return -ENOSPC;}
 size_t offset=32;
 if(old_handle){
  put_le(output+8,offset,4);put_le(output+12,handle_len,4);memcpy(output+offset,old_handle,handle_len);offset+=handle_len;
  put_le(output+16,offset,4);put_le(output+20,old_secret_len,4);memcpy(output+offset,old_secret,old_secret_len);offset+=old_secret_len;
 }
 put_le(output+24,offset,4);put_le(output+28,secret_len,4);memcpy(output+offset,secret,secret_len);*length=size;return 0;
}
int apollo_gk_encode_legacy_verify(uint32_t uid,uint64_t challenge,const uint8_t *handle,size_t handle_len,
 const uint8_t *secret,size_t secret_len,uint8_t *output,size_t capacity,size_t *length)
{
 int rc=legacy_begin(uid,0x1002,output,capacity,length);if(rc)return rc;
 if(!challenge || !handle || !handle_len || handle_len>APOLLO_GK_MAX_HANDLE || !secret || !secret_len || secret_len>128){
  explicit_bzero(output,capacity);return -EINVAL;
 }
 size_t size=32+handle_len+secret_len;
 if(size>capacity){explicit_bzero(output,capacity);return -ENOSPC;}
 put_le(output+8,challenge,8);put_le(output+16,32,4);put_le(output+20,handle_len,4);
 put_le(output+24,32+handle_len,4);put_le(output+28,secret_len,4);
 memcpy(output+32,handle,handle_len);memcpy(output+32+handle_len,secret,secret_len);*length=size;return 0;
}
static int legacy_blob(const uint8_t *reply,size_t size,const uint8_t **data,size_t *length)
{
 if(!reply || size<12)return -EINVAL;
 int32_t status=(int32_t)le32(reply);if(status)return status;
 uint32_t offset=le32(reply+4),n=le32(reply+8);
 if(offset<12 || offset>size || !n || n>size-offset)return -EPROTO;
 *data=reply+offset;*length=n;return 0;
}
int apollo_gk_decode_legacy_handle(const uint8_t *response,size_t size,uint8_t *handle,size_t capacity,size_t *length)
{
 if(length)*length=0;
 if(!handle || !length || !capacity || capacity>APOLLO_GK_MAX_HANDLE)return -EINVAL;
 memset(handle,0,capacity);const uint8_t *blob=NULL;size_t n=0;int rc=legacy_blob(response,size,&blob,&n);if(rc)return rc;
 if(n>capacity)return -EPROTO;
 memcpy(handle,blob,n);*length=n;return 0;
}
int apollo_gk_decode_legacy_token(const uint8_t *response,size_t size,uint64_t expected_challenge,uint8_t token[APOLLO_GK_HAT_SIZE])
{
 if(!token)return -EINVAL;
 memset(token,0,APOLLO_GK_HAT_SIZE);
 if(!expected_challenge)return -EINVAL;
 const uint8_t *blob=NULL;size_t n=0;int rc=legacy_blob(response,size,&blob,&n);if(rc)return rc;
 if(n!=APOLLO_GK_HAT_SIZE || blob[0]!=0 ||
    (le32(blob+1)|(uint64_t)le32(blob+5)<<32)!=expected_challenge ||
    !(le32(blob+9)|(uint64_t)le32(blob+13)<<32) || !(be(blob+25,4)&1) || !be(blob+29,8))return -EPROTO;
 unsigned nonzero=0;for(unsigned i=37;i<APOLLO_GK_HAT_SIZE;i++)nonzero|=blob[i];
 if(!nonzero)return -EPROTO;
 memcpy(token,blob,n);return 0;
}
