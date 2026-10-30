#include "nested-wayland-output.h"
#include "ext-session-lock-v1-client-protocol.h"
#include <poll.h>
#include <sys/mman.h>

static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct ext_session_lock_manager_v1 *manager;
static struct wl_surface *surface;
static const char *report;
static bool locked,finished;
static void extra_global(struct wl_registry *registry,uint32_t name,const char *interface,uint32_t version) {
    if (!strcmp(interface,wl_compositor_interface.name))
        compositor=wl_registry_bind(registry,name,&wl_compositor_interface,4);
    else if (!strcmp(interface,wl_shm_interface.name))
        shm=wl_registry_bind(registry,name,&wl_shm_interface,1);
    else if (!strcmp(interface,ext_session_lock_manager_v1_interface.name))
        manager=wl_registry_bind(registry,name,&ext_session_lock_manager_v1_interface,1);
}
static void write_state(const char *state) {
    FILE *file=fopen(report,"w");
    if (!file) exit(3);
    fprintf(file,"%s\n",state);fclose(file);
}
static void buffer_released(void *data,struct wl_buffer *buffer) { wl_buffer_destroy(buffer); }
static const struct wl_buffer_listener buffer_listener={.release=buffer_released};
static void configured(void *data,struct ext_session_lock_surface_v1 *lock_surface,
    uint32_t serial,uint32_t width,uint32_t height) {
    if (!width || !height || width>8192 || height>8192) exit(4);
    ext_session_lock_surface_v1_ack_configure(lock_surface,serial);
    size_t length=(size_t)width*height*4;
    int fd=memfd_create("apollo-private-lock-fixture",MFD_CLOEXEC);
    if (fd<0 || ftruncate(fd,length)) exit(4);
    uint32_t *pixels=mmap(NULL,length,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
    if (pixels==MAP_FAILED) exit(4);
    for (size_t i=0;i<(size_t)width*height;i++) pixels[i]=0xff18202a;
    struct wl_shm_pool *pool=wl_shm_create_pool(shm,fd,length);
    struct wl_buffer *buffer=wl_shm_pool_create_buffer(pool,0,width,height,width*4,WL_SHM_FORMAT_XRGB8888);
    wl_buffer_add_listener(buffer,&buffer_listener,NULL);
    wl_shm_pool_destroy(pool);munmap(pixels,length);close(fd);
    wl_surface_attach(surface,buffer,0,0);
    wl_surface_damage(surface,0,0,width,height);wl_surface_commit(surface);
}
static const struct ext_session_lock_surface_v1_listener surface_listener={.configure=configured};
static void lock_acquired(void *d,struct ext_session_lock_v1 *lock) { locked=true;write_state("locked"); }
static void lock_finished(void *d,struct ext_session_lock_v1 *lock) { finished=true;write_state("finished"); }
static const struct ext_session_lock_v1_listener lock_listener={.locked=lock_acquired,.finished=lock_finished};
int main(int argc,char **argv) {
    umask(077);
    if (argc!=2 || !connect_nested() || !manager || !compositor || !shm) return 2;
    report=argv[1];write_state("starting");
    struct ext_session_lock_v1 *lock=ext_session_lock_manager_v1_lock(manager);
    ext_session_lock_v1_add_listener(lock,&lock_listener,NULL);
    surface=wl_compositor_create_surface(compositor);
    struct ext_session_lock_surface_v1 *lock_surface=ext_session_lock_v1_get_lock_surface(lock,surface,output);
    ext_session_lock_surface_v1_add_listener(lock_surface,&surface_listener,NULL);
    while (!finished) {
        while (wl_display_prepare_read(display)!=0)
            if (wl_display_dispatch_pending(display)<0) return 1;
        if (wl_display_flush(display)<0) { wl_display_cancel_read(display);return 1; }
        struct pollfd descriptors[2]={{.fd=wl_display_get_fd(display),.events=POLLIN},{.fd=STDIN_FILENO,.events=POLLIN}};
        int ready=poll(descriptors,2,30000);
        if (ready<=0) { wl_display_cancel_read(display);return 1; }
        if (descriptors[0].revents&POLLIN) {
            if (wl_display_read_events(display)<0) return 1;
        } else wl_display_cancel_read(display);
        if (wl_display_dispatch_pending(display)<0) return 1;
        if (descriptors[1].revents&POLLIN) {
            char command[32]={0};ssize_t size=read(STDIN_FILENO,command,sizeof(command)-1);
            if (size>0 && !strcmp(command,"unlock\n") && locked) {
                ext_session_lock_v1_unlock_and_destroy(lock);
                if (wl_display_roundtrip(display)<0) return 1;
                write_state("unlocked");wl_display_disconnect(display);return 0;
            }
            return 1;
        }
        if (descriptors[1].revents&(POLLHUP|POLLERR)) return 1;
    }
    wl_display_disconnect(display);return 1;
}
