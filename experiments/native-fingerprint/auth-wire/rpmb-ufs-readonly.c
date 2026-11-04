/* SPDX-License-Identifier: MIT
 * SCSI CDB and sg_io_v4 transport follow Qualcomm's pinned rpmb_ufs.c.
 * No key programming, authenticated data writes or controller queries.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "rpmb-readonly.h"
#include "rpmb-authenticated.h"
#include <errno.h>
#include <fcntl.h>
#include <linux/bsg.h>
#include <scsi/sg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>
static int transfer(int fd,int input,uint8_t *buffer,uint32_t length)
{
 uint8_t cdb[12]={0},sense[96]={0};struct sg_io_v4 io={0};
 if(input<0){cdb[0]=3;cdb[4]=18;}
 else {cdb[0]=input?0xa2:0xb5;cdb[1]=0xec;cdb[3]=1;
  for(unsigned i=0;i<4;i++)cdb[6+i]=(uint8_t)(length>>(24-8*i));}
 io.guard='Q';io.protocol=BSG_PROTOCOL_SCSI;io.subprotocol=BSG_SUB_PROTOCOL_SCSI_CMD;
 io.request_len=input<0?6:sizeof cdb;io.request=(uintptr_t)cdb;io.max_response_len=sizeof sense;io.response=(uintptr_t)sense;io.timeout=10000;
 if(input){io.din_xfer_len=length;io.din_xferp=(uintptr_t)buffer;}
 else {io.dout_xfer_len=length;io.dout_xferp=(uintptr_t)buffer;}
 int rc=ioctl(fd,SG_IO,&io),saved=errno;unsigned key=0,asc=0,ascq=0;
 unsigned format=sense[0]&0x7f;
 if((format==0x70 || format==0x71) && io.response_len>=14){key=sense[2]&15;asc=sense[12];ascq=sense[13];}
 if((format==0x72 || format==0x73) && io.response_len>=4){key=sense[1]&15;asc=sense[2];ascq=sense[3];}
 fprintf(stderr,"event=rpmb_ufs_io command=%u ioctl_status=%d errno=%d device=%u transport=%u driver=%u info=%u sense_key=%u asc=%u ascq=%u residual=%d\n",cdb[0],rc,rc<0?saved:0,io.device_status,io.transport_status,io.driver_status,io.info,key,asc,ascq,input?io.din_resid:io.dout_resid);
 explicit_bzero(sense,sizeof sense);
 if(rc<0)return -saved;
 if(rc || io.device_status || io.transport_status || io.driver_status || io.info || (input?io.din_resid:io.dout_resid))return -EIO;
 return 0;
}
static int open_rpmb(void)
{
 const char *path=getenv("APOLLO_RPMB_BSG");unsigned host,channel,target,lun;char tail;
 if(!path || strncmp(path,"/dev/bsg/",9) || sscanf(path+9,"%u:%u:%u:%u%c",&host,&channel,&target,&lun,&tail)!=4 || lun!=49476)return -EPERM;
 int fd=open(path,O_RDWR|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return -errno;
 struct stat s;int rc=fstat(fd,&s);if(rc || !S_ISCHR(s.st_mode)){close(fd);return -EPERM;}
 return fd;
}
int apollo_rpmb_ufs_read(const uint8_t request[512],uint32_t frames,uint8_t *response,void *context)
{
 (void)context;unsigned type=(unsigned)request[510]<<8|request[511];
 if((type!=2 && type!=4) || !frames || frames>(APOLLO_RPMB_BUFFER-20)/512 || (type==2 && frames!=1))return -EPERM;
 int fd=open_rpmb();if(fd<0)return fd;int rc;
 /* Qualcomm initializes the RPMB LUN with REQUEST SENSE before its first
  * security-protocol transfer. This only consumes SCSI status, not RPMB data.
  */
 uint8_t status[18]={0};rc=transfer(fd,-1,status,sizeof status);explicit_bzero(status,sizeof status);
 uint8_t frame[512];memcpy(frame,request,sizeof frame);
 if(!rc)rc=transfer(fd,0,frame,sizeof frame);explicit_bzero(frame,sizeof frame);
 if(!rc)rc=transfer(fd,1,response,frames*512);
 close(fd);return rc;
}
int apollo_rpmb_ufs_write(const uint8_t *frames,uint32_t count,uint8_t result[512],void *context)
{
 (void)context;
 if(!frames || !result || !count || count>39)return -EINVAL;
 for(uint32_t i=0;i<count;i++)if(frames[i*512+510]!=0 || frames[i*512+511]!=3 || ((unsigned)frames[i*512+506]<<8|frames[i*512+507])!=count)return -EPERM;
 int fd=open_rpmb();if(fd<0)return fd;
 uint8_t status[18]={0},request[39*512]={0},read_result[512]={0};
 int rc=transfer(fd,-1,status,sizeof status);explicit_bzero(status,sizeof status);
 memcpy(request,frames,count*512);
 if(!rc)rc=transfer(fd,0,request,count*512);explicit_bzero(request,sizeof request);
 read_result[511]=5;
 if(!rc)rc=transfer(fd,0,read_result,sizeof read_result);explicit_bzero(read_result,sizeof read_result);
 if(!rc)rc=transfer(fd,1,result,512);
 close(fd);return rc;
}
