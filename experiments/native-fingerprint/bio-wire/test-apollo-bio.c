/* SPDX-License-Identifier: MIT */
#include "apollo-bio.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static unsigned calls;static uint32_t op,want_target=11,answer;static int outer,transport;
static uint32_t get(const unsigned char *b){return b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;}
static void put(unsigned char *b,uint32_t n){for(unsigned i=0;i<4;i++)b[i]=n>>(8*i);}
static int exchange(void *ctx,void *ptr,size_t len,int32_t *status)
{
 (void)ctx;unsigned char *b=ptr;calls++;assert(len==4096 && get(b)==want_target && get(b+4)==op);
 if(want_target==10 && op==4)assert(get(b+8)==0 && get(b+20)==1);
 memset(b,0,len);put(b+8,answer);for(unsigned i=0;i<25;i++)put(b+12+4*i,i+1);
 *status=outer;return transport;
}
static int token_exchange(void *ctx,void *ptr,size_t len,int32_t *status)
{
 unsigned char *b=ptr;assert(len==4096 && get(b)==3 && get(b+4)==4 && get(b+8)==69);
 memset(b,0,len);unsigned char *token=b+12;put(token+1,123);token[9]=1;token[28]=2;token[36]=1;token[37]=1;
 if(ctx)token[1]^=1;
 *status=0;return 0;
}
int main(void)
{
 struct apollo_bio p={0,exchange};uint32_t ids[25],count,n;
 op=0;assert(apollo_bio_init(&p)==0);op=10;assert(apollo_bio_group(&p,1000)==0);
 unsigned before=calls;assert(apollo_bio_group(&p,0)==-EINVAL && apollo_bio_group(&p,65536)==-EINVAL && calls==before);
 op=8;for(answer=0;answer<1000;answer++){int rc=apollo_bio_ids(&p,ids,&count);assert(rc==(answer>25?-EPROTO:0));assert(count==(answer>25?0:answer));}
 op=2;for(answer=0;answer<1000;answer++){int rc=apollo_bio_sample(&p,&n);assert(rc==(answer>100?-EPROTO:0));assert(n==(answer>100?UINT32_MAX:answer));}
 outer=6;answer=42;assert(apollo_bio_sample(&p,&n)==6 && n==42);answer=101;assert(apollo_bio_sample(&p,&n)==-EPROTO && n==UINT32_MAX);outer=0;
 op=3;answer=0;assert(apollo_bio_end(&p,&n)==-EPROTO && !n);answer=7;assert(!apollo_bio_end(&p,&n) && n==7);
 outer=-30;op=8;assert(apollo_bio_ids(&p,ids,&count)==-30 && !count);outer=0;transport=-EIO;assert(apollo_bio_ids(&p,ids,&count)==-EIO && !count);transport=0;
 want_target=10;op=4;assert(!apollo_sensor_command(&p,4,&n));before=calls;assert(apollo_sensor_command(&p,6,&n)==-EINVAL && calls==before);
 assert(apollo_bio_init(0)==-EINVAL);
 p.exchange=token_exchange;p.context=0;assert(apollo_bio_fresh_result(&p,123)==0);
 p.context=&p;assert(apollo_bio_fresh_result(&p,123)==-EPROTO);assert(apollo_bio_fresh_result(&p,0)==-EINVAL);
 puts("Apollo BIO: wire offsets, bounded lengths, fail-closed transport and commands passed");
}
