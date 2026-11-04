/* SPDX-License-Identifier: MIT
 * Apollo 112-byte logical messages, padded to 4096, separate outer status.
 * Confirmed against public HAL 8c499a88... and pinned Apollo BIO dispatcher.
 * Never select Sargo's command numbering or status-at-eight interpretation.
 */
#include "apollo-bio.h"
#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
static uint32_t get(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(uint8_t *p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(i*8));}
static int command(struct apollo_bio *p,uint8_t b[APOLLO_BIO_BYTES])
{
 if(!p || !p->exchange)return -EINVAL;
 int32_t outer=INT32_MIN;
 int rc=p->exchange(p->context,b,APOLLO_BIO_BYTES,&outer);
 return rc?rc:outer;
}
static int scalar(struct apollo_bio *p,uint32_t target,uint32_t op,uint32_t value,uint32_t *out)
{
 uint8_t b[APOLLO_BIO_BYTES]={0};put(b,target);put(b+4,op);put(b+8,value);
 int rc=command(p,b);if((!rc || (target==11 && op==2 && rc==6)) && out)*out=get(b+8);explicit_bzero(b,sizeof b);return rc;
}
int apollo_bio_init(struct apollo_bio *p){return scalar(p,11,0,0,0);}
int apollo_bio_group(struct apollo_bio *p,uint32_t group){if(group<1000 || group>65535)return -EINVAL;return scalar(p,11,10,group,0);}
int apollo_bio_begin(struct apollo_bio *p){return scalar(p,11,1,0,0);}
int apollo_bio_sample(struct apollo_bio *p,uint32_t *remaining)
{
 if(!remaining)return -EINVAL;
 *remaining=UINT32_MAX;uint32_t n=UINT32_MAX;int rc=scalar(p,11,2,0,&n);
 if(!rc || rc==6){if(n>100)return -EPROTO;*remaining=n;}return rc;
}
int apollo_bio_end(struct apollo_bio *p,uint32_t *id)
{
 if(!id)return -EINVAL;
 *id=0;uint32_t n=0;int rc=scalar(p,11,3,0,&n);if(!rc){if(!n)return -EPROTO;*id=n;}return rc;
}
int apollo_bio_ids(struct apollo_bio *p,uint32_t ids[APOLLO_BIO_MAX_IDS],uint32_t *count)
{
 if(!ids || !count)return -EINVAL;
 *count=0;memset(ids,0,APOLLO_BIO_MAX_IDS*sizeof *ids);
 uint8_t b[APOLLO_BIO_BYTES]={0};put(b,11);put(b+4,8);put(b+8,APOLLO_BIO_MAX_IDS);
 int rc=command(p,b);
 if(!rc){
  uint32_t n=get(b+8);if(n>APOLLO_BIO_MAX_IDS){rc=-EPROTO;goto out;}
  for(uint32_t i=0;i<n;i++){
   uint32_t id=get(b+12+4*i);if(!id){rc=-EPROTO;goto out;}
   for(uint32_t j=0;j<i;j++)if(ids[j]==id){rc=-EPROTO;goto out;}
   ids[i]=id;
  }
  *count=n;
 }
out:
 if(rc)memset(ids,0,APOLLO_BIO_MAX_IDS*sizeof *ids);
 explicit_bzero(b,sizeof b);return rc;
}
int apollo_sensor_command(struct apollo_bio *p,uint32_t op,uint32_t *detail)
{
 if(op>5)return -EINVAL;
 uint8_t b[APOLLO_BIO_BYTES]={0};put(b,10);put(b+4,op);
 /* Active capture: no implicit finger-lost loop, qualify mode enabled.
  * HAL capture_image(sensor,false): byte8=0, word20=1. */
 if(op==4)put(b+20,1);
 int rc=command(p,b);if(detail)*detail=rc>=0?get(b+16):0;
 explicit_bzero(b,sizeof b);return rc;
}
int apollo_bio_wrapped_database(const uint8_t *b,size_t n)
{
 /* fpc_wrap_crypto / fpc_unwrap_crypto: u32 plaintext length, 32-byte MAC,
  * 16-byte IV, ciphertext; checked by the TA when importing. */
 return b && n>=52 && n<=APOLLO_BIO_DB_MAX && get(b)<=APOLLO_BIO_DB_MAX-52 && (size_t)get(b)+52==n;
}
static int transfer_database(struct apollo_bio *p,uint8_t *data,size_t n,int load)
{
 uint8_t b[APOLLO_BIO_BYTES]={0};put(b,4);put(b+4,14);put(b+12,load);put(b+16,(uint32_t)n);
 int rc=command(p,b);if(rc)return rc<0?rc:-EPROTO;
 size_t offset=0;
 while(offset<n){
  size_t amount=n-offset;if(amount>sizeof b-12)amount=sizeof b-12;
  memset(b,0,sizeof b);put(b,4);put(b+4,load?17:16);put(b+8,(uint32_t)amount);
  if(load)memcpy(b+12,data+offset,amount);
  rc=command(p,b);if(rc<0)break;
  if((size_t)rc!=n-offset-amount){rc=-EPROTO;break;}
  if(!load)memcpy(data+offset,b+12,amount);
  offset+=amount;
 }
 int close_status=scalar(p,4,15,0,0);explicit_bzero(b,sizeof b);
 if(rc<0)return rc;
 if(close_status)return close_status<0?close_status:-EPROTO;
 return offset==n?0:-EPROTO;
}
int apollo_bio_export(struct apollo_bio *p,uint8_t **out,size_t *size)
{
 if(!out || !size)return -EINVAL;
 *out=0;*size=0;uint32_t n=0;int rc=scalar(p,4,6,0,&n);if(rc)return rc<0?rc:-EPROTO;
 if(n<52 || n>APOLLO_BIO_DB_MAX)return -EPROTO;
 uint8_t *data=calloc(1,n);if(!data)return -ENOMEM;
 rc=transfer_database(p,data,n,0);
 if(!rc && !apollo_bio_wrapped_database(data,n))rc=-EPROTO;
 if(rc){explicit_bzero(data,n);free(data);return rc;}
 *out=data;*size=n;return 0;
}
int apollo_bio_import(struct apollo_bio *p,const uint8_t *data,size_t n)
{
 if(!apollo_bio_wrapped_database(data,n))return -EPROTO;
 /* Transfer does not mutate load input. The TA verifies its MAC before use. */
 return transfer_database(p,(uint8_t *)data,n,1);
}
int apollo_bio_identify(struct apollo_bio *p,uint32_t *id)
{
 if(!id)return -EINVAL;
 *id=0;return scalar(p,11,4,0,id);
}
int apollo_bio_challenge(struct apollo_bio *p,uint64_t challenge)
{
 if(!challenge)return -EINVAL;
 uint8_t b[APOLLO_BIO_BYTES]={0};put(b,3);put(b+4,1);put(b+8,(uint32_t)challenge);put(b+12,challenge>>32);
 int rc=command(p,b);explicit_bzero(b,sizeof b);return rc;
}
int apollo_bio_fresh_result(struct apollo_bio *p,uint64_t challenge)
{
 if(!challenge)return -EINVAL;
 uint8_t b[APOLLO_BIO_BYTES]={0};put(b,3);put(b+4,4);put(b+8,69);int rc=command(p,b);
 if(!rc){
  uint8_t *token=b+12;uint64_t received=get(token+1)|(uint64_t)get(token+5)<<32;
  unsigned mac=0;for(unsigned i=37;i<69;i++)mac|=token[i];
  unsigned sid=0;for(unsigned i=9;i<17;i++)sid|=token[i];
  unsigned stamp=0;for(unsigned i=29;i<37;i++)stamp|=token[i];
  if(token[0]!=0 || received!=challenge || !sid || token[25] || token[26] || token[27] || token[28]!=2 || !stamp || !mac)rc=-EPROTO;
 }
 explicit_bzero(b,sizeof b);return rc;
}
