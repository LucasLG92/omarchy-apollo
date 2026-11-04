/* SPDX-License-Identifier: MIT. Simulated ciphertext, no biometric data. */
#include "apollo-bio.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct mock {unsigned char data[9001];size_t offset;int active,load,bad_remaining,closed;};
static uint32_t get(const unsigned char *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(unsigned char *p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=n>>(8*i);}
static int exchange(void *ctx,void *ptr,size_t n,int32_t *status)
{
 struct mock *m=ctx;unsigned char *b=ptr;assert(n==4096 && get(b)==4);*status=0;
 switch(get(b+4)){
 case 6:put(b+8,sizeof m->data);break;
 case 14:assert(!m->active && get(b+16)==sizeof m->data);m->active=1;m->load=get(b+12);m->offset=0;break;
 case 15:assert(m->active);m->active=0;m->closed++;break;
 case 16:case 17:{assert(m->active);size_t amount=get(b+8);assert(amount<=n-12 && amount<=sizeof m->data-m->offset);
  if(m->load)assert(!memcmp(b+12,m->data+m->offset,amount));else memcpy(b+12,m->data+m->offset,amount);
  m->offset+=amount;*status=sizeof m->data-m->offset+(m->bad_remaining?1:0);break;}
 default:assert(0);
 }return 0;
}
int main(void)
{
 struct mock m={0};memset(m.data,0xa5,sizeof m.data);put(m.data,sizeof m.data-52);
 struct apollo_bio p={&m,exchange};uint8_t *data=0;size_t size=0;
 assert(!apollo_bio_export(&p,&data,&size) && size==sizeof m.data && !memcmp(data,m.data,size) && !m.active && m.closed==1);
 assert(!apollo_bio_import(&p,data,size) && !m.active && m.closed==2);
 for(size_t n=0;n<size;n++)assert(!apollo_bio_wrapped_database(data,n));
 put(data,UINT32_MAX);assert(apollo_bio_import(&p,data,size)==-EPROTO);put(data,size-52);
 free(data);m.bad_remaining=1;assert(apollo_bio_export(&p,&data,&size)==-EPROTO && !data && !size && !m.active && m.closed==3);
 assert(!apollo_bio_wrapped_database(0,52));puts("Apollo database: bounded chunks, expected remaining, cleanup and wrapped format passed");
}
