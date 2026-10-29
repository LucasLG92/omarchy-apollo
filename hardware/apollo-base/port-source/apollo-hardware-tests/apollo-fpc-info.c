/* FPC bring-up and metadata queries, derived from this phone's OEM HAL.
 * fpc_tee_get_build_info: target 12, command 1; fpc_tac_transfer: 64-byte
 * request and response, payload physical address patched at request byte 4.
 * Optional sensor initialization follows fpc_hal_open's exact command order.
 * No enrollment, matching, storage, factory, image export or OTP commands.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/tee.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

struct memory { void *p; size_t size; int id; };
static volatile sig_atomic_t stopping;
static void stop_signal(int signum) { (void)signum; stopping=1; }
static int allocate(int fd, struct memory *m, size_t size) {
    struct tee_ioctl_shm_alloc_data a = { .size=size };
    int shm=ioctl(fd, TEE_IOC_SHM_ALLOC, &a);
    if (shm < 0) return -1;
    m->p=mmap(NULL,a.size,PROT_READ|PROT_WRITE,MAP_SHARED,shm,0);
    close(shm);
    if (m->p == MAP_FAILED) return -1;
    m->size=a.size; m->id=a.id;
    memset(m->p,0,m->size);
    return 0;
}
static int open_device(void) {
    for (int i=0;i<8;i++) {
        char path[32]; struct tee_ioctl_version_data v;
        snprintf(path,sizeof(path),"/dev/tee%d",i);
        int fd=open(path,O_RDWR|O_CLOEXEC);
        if (fd<0) continue;
        if (!ioctl(fd,TEE_IOC_VERSION,&v) && v.impl_id==5) return fd;
        close(fd);
    }
    errno=ENODEV; return -1;
}
static int command(int fd, uint32_t session, struct memory *header, struct memory *payload,
                   uint32_t target, uint32_t operation, uint32_t capacity, const char *label) {
    memset(header->p,0,header->size);
    memset(payload->p,0,payload->size);
    uint32_t *p=payload->p;
    p[0]=target; p[1]=operation; p[5]=capacity;
    /* OEM allocator rounds the complete payload to a 4 KiB ION buffer. */
    *(uint32_t *)header->p=4096;
    uint64_t iv[(sizeof(struct tee_ioctl_invoke_arg)+4*sizeof(struct tee_ioctl_param)+7)/8]={0};
    struct tee_ioctl_invoke_arg *a=(void *)iv;
    a->session=session; a->num_params=4;
    a->params[0]=(struct tee_ioctl_param){.attr=TEE_IOCTL_PARAM_ATTR_TYPE_MEMREF_INPUT,.b=64,.c=(uint64_t)header->id};
    a->params[1]=(struct tee_ioctl_param){.attr=TEE_IOCTL_PARAM_ATTR_TYPE_MEMREF_OUTPUT,.a=64,.b=64,.c=(uint64_t)header->id};
    a->params[2]=(struct tee_ioctl_param){.attr=TEE_IOCTL_PARAM_ATTR_TYPE_VALUE_INPUT,.a=4,.b=4};
    a->params[3]=(struct tee_ioctl_param){.attr=TEE_IOCTL_PARAM_ATTR_TYPE_MEMREF_INOUT,.b=4096,.c=(uint64_t)payload->id};
    struct tee_ioctl_buf_data d={.buf_ptr=(uintptr_t)iv,.buf_len=sizeof(iv)};
    if (ioctl(fd,TEE_IOC_INVOKE,&d)) { int saved=errno; perror(label); return -saved; }
    int32_t status; memcpy(&status,(char *)header->p+64,4);
    printf("%s transport_status=%u application_status=%d\n",label,a->ret,status);
    return a->ret ? -EIO : status;
}
int main(int argc, char **argv) {
    setvbuf(stdout,NULL,_IOLBF,0);
    signal(SIGTERM,stop_signal); signal(SIGINT,stop_signal);
    int presence = argc == 2 && !strcmp(argv[1], "--finger-presence");
    long presence_seconds = 100;
    const char *configured = getenv("APOLLO_FPC_PRESENCE_SECONDS");
    if (configured) {
        char *end;
        errno = 0;
        presence_seconds = strtol(configured, &end, 10);
        if (errno || end == configured || *end || presence_seconds < 30 || presence_seconds > 600) {
            fprintf(stderr, "Presence timeout must be an integer from 30 to 600 seconds\n");
            return 2;
        }
    }
    int initialize = presence || (argc == 2 && !strcmp(argv[1], "--sensor-init-info"));
    int sensor_info = initialize || (argc == 2 && !strcmp(argv[1], "--sensor-info"));
    if (argc > 2 || (argc == 2 && !sensor_info)) return 2;
    struct memory name={0}, header={0}, payload={0};
    uint64_t os[(sizeof(struct tee_ioctl_open_session_arg)+sizeof(struct tee_ioctl_param)+7)/8]={0};
    struct tee_ioctl_open_session_arg *o=(void *)os;
    struct tee_ioctl_buf_data d={.buf_ptr=(uintptr_t)os,.buf_len=sizeof(os)};
    int fd=open_device(), result=1;
    uint32_t session=0;
    int sensor_opened=0;
    if (fd<0) { perror("QSEE client"); return 1; }
    if (allocate(fd,&name,64)||allocate(fd,&header,128)||allocate(fd,&payload,4096)) {
        perror("shared memory"); goto out;
    }
    memcpy(name.p,"fpcapo",7);
    o->num_params=1;
    o->params[0]=(struct tee_ioctl_param){.attr=TEE_IOCTL_PARAM_ATTR_TYPE_MEMREF_INPUT,.b=7,.c=(uint64_t)name.id};
    if (ioctl(fd,TEE_IOC_OPEN_SESSION,&d)) { perror("attach fpcapo"); goto out; }
    session=o->session;
    printf("fpcapo attached=1\n");
    if (initialize) {
        FILE *power=fopen("/sys/devices/platform/apollo-fpc-test/enable","r");
        int enabled=power?fgetc(power):0;
        if (power) fclose(power);
        if (enabled!='1') { fprintf(stderr,"Verified sensor power must be enabled first\n"); goto out; }
        /* fpc_hal_open -> fpc_tee_sensor_init -> fpc_tee_bio_init.
         * Confirmed from this phone's HAL: sensor target10/op0, op5;
         * bio target11/op0 (ELF rodata 0x44920 is {11,0}). */
        if (command(fd,session,&header,&payload,10,0,0,"sensor_open")) goto out;
        sensor_opened=1;
        if (command(fd,session,&header,&payload,10,5,0,"sensor_prepare")) goto out;
        if (command(fd,session,&header,&payload,11,0,0,"bio_initialize")) goto out;
    }
    if (presence) {
        if (command(fd,session,&header,&payload,10,3,0,"finger_wait_arm")) goto out;
        struct timespec start,now;
        clock_gettime(CLOCK_MONOTONIC,&start);
        int initial_count=-1, low_seen=0;
        printf("finger_presence waiting=1 timeout_seconds=%ld require_low_then_rising=1\n",presence_seconds);
        while (!stopping) {
            FILE *irq=fopen("/sys/devices/platform/apollo-fpc-test/irq","r");
            int level=-1,count=-1;
            if (irq) { fscanf(irq,"level=%d count=%d",&level,&count); fclose(irq); }
            if (initial_count<0 && count>=0) initial_count=count;
            if (level==0) low_seen=1;
            if (low_seen && level==1 && count>initial_count) {
                printf("finger_presence detected=1 irq_before=%d irq_after=%d\n",initial_count,count);
                result=0; break;
            }
            clock_gettime(CLOCK_MONOTONIC,&now);
            if (now.tv_sec-start.tv_sec>=presence_seconds) {
                printf("finger_presence detected=0 low_seen=%d irq_before=%d irq_after=%d\n",low_seen,initial_count,count);
                break;
            }
            usleep(100000);
        }
        goto out;
    }
    int status=command(fd,session,&header,&payload,sensor_info?6:12,sensor_info?2:1,sensor_info?0:1024,sensor_info?"sensor_info":"build_info");
    if (status) goto out;
    uint32_t *p=payload.p;
    if (sensor_info) {
        uint16_t width,height; memcpy(&width,(char *)payload.p+8,2); memcpy(&height,(char *)payload.p+10,2);
        printf("sensor_info width=%u height=%u\n",width,height);
        if (width && height) result=0;
        goto out;
    }
    printf("build_info response_fields=%u,%u,%u,%u capacity=%u\n",p[0],p[1],p[2],p[3],p[5]);
    if (!status) {
        /* OEM response text starts after the 24-byte response header. */
        char text[257]; size_t j=0;
        const unsigned char *src=(unsigned char *)payload.p+24;
        for (;j<256 && src[j];j++) text[j]=(src[j]>=32 && src[j]<=126)?(char)src[j]:'.';
        text[j]=0;
        printf("build_info text=%s\n",text);
        result=0;
    }
out:
    if (sensor_opened) command(fd,session,&header,&payload,10,5,0,"sensor_release");
    if (session) { struct tee_ioctl_close_session_arg c={.session=session}; ioctl(fd,TEE_IOC_CLOSE_SESSION,&c); }
    if (payload.p && payload.p!=MAP_FAILED) munmap(payload.p,payload.size);
    if (header.p && header.p!=MAP_FAILED) munmap(header.p,header.size);
    if (name.p && name.p!=MAP_FAILED) munmap(name.p,name.size);
    close(fd); return result;
}
