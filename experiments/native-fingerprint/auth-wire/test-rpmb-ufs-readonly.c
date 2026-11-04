/* SPDX-License-Identifier: MIT */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "rpmb-readonly.h"
#include "rpmb-authenticated.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/bsg.h>
#include <scsi/sg.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
static unsigned opens,ios,stage,frames=3;static int transport_failure;
static int write_mode,fail_at=-1;
int __wrap_open(const char *path,int flags,...){assert(!strcmp(path,"/dev/bsg/0:0:0:49476") && (flags&O_NOFOLLOW) && (flags&O_CLOEXEC));opens++;return 42;}
int __wrap___open_2(const char *path,int flags){return __wrap_open(path,flags);}
int __wrap_fstat(int fd,struct stat *s){assert(fd==42);memset(s,0,sizeof *s);s->st_mode=S_IFCHR|0600;return 0;}
int __wrap_close(int fd){assert(fd==42);return 0;}
int __wrap_ioctl(int fd,unsigned long cmd,...){assert(fd==42 && cmd==SG_IO);va_list ap;va_start(ap,cmd);struct sg_io_v4 *io=va_arg(ap,struct sg_io_v4*);va_end(ap);
 uint8_t *cdb=(uint8_t *)(uintptr_t)io->request;assert(io->guard=='Q' && io->protocol==BSG_PROTOCOL_SCSI && io->subprotocol==BSG_SUB_PROTOCOL_SCSI_CMD);
 assert(io->timeout==10000);
 unsigned current=stage++;
 if(current==0){assert(io->request_len==6 && cdb[0]==3 && cdb[4]==18 && io->din_xfer_len==18 && !io->dout_xfer_len);ios++;if(transport_failure || fail_at==0)io->transport_status=1;return 0;}
 assert(io->request_len==12 && cdb[1]==0xec && cdb[2]==0 && cdb[3]==1);
 uint32_t n=(uint32_t)cdb[6]<<24|(uint32_t)cdb[7]<<16|(uint32_t)cdb[8]<<8|cdb[9];ios++;
 if(write_mode){
  if(current<=2){unsigned expected=current==1?frames*512:512;assert(cdb[0]==0xb5 && n==expected && io->dout_xfer_len==expected && !io->din_xfer_len);uint8_t *p=(uint8_t *)(uintptr_t)io->dout_xferp;assert(p[510]==0 && p[511]==(current==1?3:5));}
  else {assert(current==3 && cdb[0]==0xa2 && n==512 && io->din_xfer_len==512 && !io->dout_xfer_len);uint8_t *p=(uint8_t *)(uintptr_t)io->din_xferp;memset(p,0,512);p[510]=3;}
 }else if(current==1){assert(cdb[0]==0xb5 && n==512 && io->dout_xfer_len==512 && !io->din_xfer_len);uint8_t *p=(uint8_t *)(uintptr_t)io->dout_xferp;assert(p[510]==0 && (p[511]==2 || p[511]==4));}
 else {assert(cdb[0]==0xa2 && n==frames*512 && io->din_xfer_len==n && !io->dout_xfer_len);memset((void *)(uintptr_t)io->din_xferp,0x3c,n);}
 if(transport_failure || fail_at==(int)current)io->transport_status=1;return 0;}
int main(void){uint8_t req[512]={0},res[39*512]={0};unsigned cases=0;
 setenv("APOLLO_RPMB_BSG","/dev/bsg/0:0:0:49476",1);
 for(unsigned type=0;type<256;type++){req[510]=0;req[511]=type;unsigned before=opens;stage=0;frames=type==2?1:3;int r=apollo_rpmb_ufs_read(req,frames,res,0);assert((r==0)==(type==2 || type==4));assert(opens-before==((type==2 || type==4)?1u:0u));cases++;}
 /* Counter query must have one response frame; direct calls are checked too. */
 req[511]=2;unsigned before=opens;assert(apollo_rpmb_ufs_read(req,2,res,0)==-EPERM && opens==before);cases++;
 req[511]=4;stage=0;transport_failure=1;unsigned start=ios;assert(apollo_rpmb_ufs_read(req,3,res,0)==-EIO && ios==start+1);cases++;
 transport_failure=0;before=opens;setenv("APOLLO_RPMB_BSG","/dev/sda",1);assert(apollo_rpmb_ufs_read(req,3,res,0)==-EPERM && opens==before);cases++;
 setenv("APOLLO_RPMB_BSG","/dev/bsg/0:0:0:49476suffix",1);assert(apollo_rpmb_ufs_read(req,3,res,0)==-EPERM && opens==before);cases++;
 setenv("APOLLO_RPMB_BSG","/dev/bsg/0:0:0:49476",1);write_mode=1;frames=3;
 uint8_t batch[3*512]={0};for(unsigned i=0;i<3;i++){batch[i*512+511]=3;batch[i*512+507]=3;}
 stage=0;assert(apollo_rpmb_ufs_write(batch,3,res,0)==0 && stage==4);cases++;
 for(int failure=0;failure<4;failure++){fail_at=failure;stage=0;assert(apollo_rpmb_ufs_write(batch,3,res,0)==-EIO && stage==(unsigned)failure+1);cases++;}
 fail_at=-1;batch[511]=1;before=opens;assert(apollo_rpmb_ufs_write(batch,3,res,0)==-EPERM && opens==before);cases++;
 printf("PASS %u mocked UFS ioctl/read-policy cases; no hardware opened\n",cases);return 0;}
