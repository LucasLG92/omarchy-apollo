#include "nested-wayland-output.h"
#include "wlr-virtual-pointer-unstable-v1-client-protocol.h"
#include <errno.h>
#include <linux/input-event-codes.h>
#include <time.h>

static struct zwlr_virtual_pointer_manager_v1 *manager;
static void extra_global(struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version) {
    if (!strcmp(interface,zwlr_virtual_pointer_manager_v1_interface.name) && version>=2)
        manager=wl_registry_bind(registry,name,&zwlr_virtual_pointer_manager_v1_interface,2);
}
int main(int argc,char **argv) {
    if (argc!=5 || !connect_nested() || !manager) return 2;
    uint32_t values[4];
    for (unsigned i=0;i<4;i++) {
        char *end=NULL; errno=0; unsigned long value=strtoul(argv[i+1],&end,10);
        if (errno || !end || *end || value>16384) return 2;
        values[i]=value;
    }
    if (!values[2] || !values[3] || values[0]>=values[2] || values[1]>=values[3]) return 2;
    struct timespec now; clock_gettime(CLOCK_MONOTONIC,&now);
    uint32_t stamp=(uint64_t)now.tv_sec*1000+now.tv_nsec/1000000;
    struct zwlr_virtual_pointer_v1 *pointer=
        zwlr_virtual_pointer_manager_v1_create_virtual_pointer_with_output(manager,NULL,output);
    /* The headless seat may gain its first pointer here. Allow other clients
     * to receive capabilities and bind wl_pointer before the first event. */
    if (wl_display_roundtrip(display)<0) return 1;
    usleep(150000);
    /* Start outside the keyboard so an unchanged absolute position cannot
     * suppress enter/motion after a layer or pointer was recreated. */
    zwlr_virtual_pointer_v1_motion_absolute(pointer,stamp,0,0,values[2],values[3]);
    zwlr_virtual_pointer_v1_frame(pointer);
    if (wl_display_roundtrip(display)<0) return 1;
    zwlr_virtual_pointer_v1_motion_absolute(pointer,stamp,values[0],values[1],values[2],values[3]);
    zwlr_virtual_pointer_v1_frame(pointer);
    if (wl_display_roundtrip(display)<0) return 1;
    usleep(50000);
    zwlr_virtual_pointer_v1_button(pointer,stamp,BTN_LEFT,WL_POINTER_BUTTON_STATE_PRESSED);
    zwlr_virtual_pointer_v1_frame(pointer);
    zwlr_virtual_pointer_v1_button(pointer,stamp+1,BTN_LEFT,WL_POINTER_BUTTON_STATE_RELEASED);
    zwlr_virtual_pointer_v1_frame(pointer);
    if (wl_display_roundtrip(display)<0) return 1;
    zwlr_virtual_pointer_v1_destroy(pointer);
    wl_display_flush(display);wl_display_disconnect(display);
    return 0;
}
