/* SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include "apollo-auth-check.h"
#include "qsee-transport.h"
#include <errno.h>
#include <stdint.h>
#include <string.h>

static uint32_t le32(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static uint64_t le64(const uint8_t *p)
{ return le32(p)|(uint64_t)le32(p+4)<<32; }
static void put32(uint8_t *p,uint32_t n)
{ for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i)); }

static int fpc_command(struct fpc_qsee_session *session,uint8_t *payload,size_t len)
{
    int32_t outer=INT32_MIN;
    int rc=fpc_qsee_command(session,payload,len,&outer);
    return rc?rc:outer;
}

int apollo_auth_version(void)
{
    struct fpc_qsee_session fpc={.fd=-1};
    uint8_t payload[4096]={0};
    int rc=fpc_qsee_open(&fpc,"fpcapo");
    if(!rc){
        put32(payload,12);put32(payload+4,1);put32(payload+20,1024);
        rc=fpc_command(&fpc,payload,sizeof payload);
        if(!rc && (le32(payload+8)!=6 || le32(payload+12)!=0 || le32(payload+16)!=5))rc=-EPROTO;
    }
    explicit_bzero(payload,sizeof payload);fpc_qsee_close(&fpc);return rc;
}

int apollo_auth_check(struct apollo_auth_check *report)
{
    struct fpc_qsee_session fpc={.fd=-1},keymaster={.fd=-1};
    uint8_t request[64]={0},response[40956]={0},payload[4096]={0};
    uint64_t challenge=0,previous=0;
    int rc=-EINVAL;
    if(!report)return rc;
    memset(report,0,sizeof *report);
    report->phase="open-fpc";
    rc=fpc_qsee_open(&fpc,"fpcapo");if(rc)goto done;
    report->phase="FPC-version";
    put32(payload,12);put32(payload+4,1);put32(payload+20,1024);
    rc=fpc_command(&fpc,payload,sizeof payload);if(rc)goto done;
    if(le32(payload+8)!=6 || le32(payload+12)!=0 || le32(payload+16)!=5){rc=-EPROTO;goto done;}
    report->FPC_version_verified=true;
    explicit_bzero(payload,sizeof payload);
    report->phase="open-resident-keymaster";
    rc=fpc_qsee_open(&keymaster,"keymaster64");if(rc)goto done;

    /* Apollo's fpc_tee_init_hw_auth: command517/version2, 64/960 bytes.
     * Import the sealed result inside this process; never print or persist it.
     */
    report->phase="request-wrapped-auth-key";
    put32(request,517);put32(request+4,2);put32(response,(uint32_t)INT32_MIN);
    rc=fpc_qsee_exchange(&keymaster,request,sizeof request,response,960,NULL,0,0);
    if(rc)goto done;
    rc=(int32_t)le32(response);if(rc)goto done;
    uint32_t offset=le32(response+4),size=le32(response+8);
    if(offset<12 || offset>960 || !size || size>960-offset || size>sizeof payload-12){rc=-EPROTO;goto done;}
    put32(payload,3);put32(payload+4,5);put32(payload+8,size);
    memcpy(payload+12,response+offset,size);
    explicit_bzero(response,sizeof response);explicit_bzero(request,sizeof request);
    report->phase="import-wrapped-auth-key";
    rc=fpc_command(&fpc,payload,sizeof payload);
    explicit_bzero(payload,sizeof payload);if(rc)goto done;
    report->wrapped_key_imported=true;
    for(unsigned i=0;i<2;i++){
        report->phase="fresh-enrollment-challenge";
        put32(payload,3);put32(payload+4,2);
        rc=fpc_command(&fpc,payload,sizeof payload);if(rc)goto done;
        challenge=le64(payload+8);
        if(!challenge || challenge==previous){rc=-EPROTO;goto done;}
        previous=challenge;explicit_bzero(payload,sizeof payload);
    }
    report->fresh_challenge_verified=true;

    /* Read/negotiation requests independently confirmed in Apollo's HAL.
     * Neither is a Gatekeeper enrollment or credential verification request.
     */
    report->phase="keymaster-version";
    put32(request,512);put32(response,(uint32_t)INT32_MIN);
    rc=fpc_qsee_exchange(&keymaster,request,4,response,sizeof response,NULL,0,0);
    if(rc)goto done;
    rc=(int32_t)le32(response);if(rc)goto done;
    for(unsigned i=0;i<4;i++)report->keymaster_version[i]=le32(response+4+4*i);
    if(!report->keymaster_version[0]){rc=-EPROTO;goto done;}
    report->keymaster_version_queried=true;
    explicit_bzero(request,sizeof request);explicit_bzero(response,sizeof response);
    report->phase="keymaster-protocol-negotiation";
    const uint32_t negotiation[]={519,4,5,4,5,0};
    for(unsigned i=0;i<6;i++)put32(request+4*i,negotiation[i]);
    put32(response,(uint32_t)INT32_MIN);
    rc=fpc_qsee_exchange(&keymaster,request,24,response,40936,NULL,0,0);
    if(rc)goto done;
    rc=(int32_t)le32(response);if(rc)goto done;
    report->keymaster_protocol_negotiated=true;
    report->phase="complete";
done:
    report->code=rc;
    fpc_qsee_close(&keymaster);fpc_qsee_close(&fpc);
    explicit_bzero(request,sizeof request);explicit_bzero(response,sizeof response);
    explicit_bzero(payload,sizeof payload);explicit_bzero(&challenge,sizeof challenge);
    explicit_bzero(&previous,sizeof previous);
    return rc;
}
