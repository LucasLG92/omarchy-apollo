/* Test-only: refuse ordinary runtime directories and physical display outputs. */
#define _GNU_SOURCE
#include <wayland-client.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static struct wl_display *display;
static struct wl_output *output;
static unsigned output_count;
static char output_name[256];
static void extra_global(struct wl_registry *, uint32_t, const char *, uint32_t);
static void output_geometry(void *d, struct wl_output *o, int32_t x, int32_t y,
    int32_t pw, int32_t ph, int32_t subpixel, const char *make, const char *model, int32_t transform) {}
static void output_mode(void *d, struct wl_output *o, uint32_t flags, int32_t w, int32_t h, int32_t refresh) {}
static void output_done(void *d, struct wl_output *o) {}
static void output_scale(void *d, struct wl_output *o, int32_t scale) {}
static void output_description(void *d, struct wl_output *o, const char *text) {}
static void output_named(void *d, struct wl_output *o, const char *name) {
    snprintf(output_name, sizeof(output_name), "%s", name);
}
static const struct wl_output_listener output_listener = {
    .geometry=output_geometry, .mode=output_mode, .done=output_done, .scale=output_scale,
    .name=output_named, .description=output_description,
};
static void global(void *d, struct wl_registry *registry, uint32_t name,
    const char *interface, uint32_t version) {
    if (!strcmp(interface, wl_output_interface.name)) {
        ++output_count;
        if (output_count == 1 && version >= 4) {
            output=wl_registry_bind(registry,name,&wl_output_interface,4);
            wl_output_add_listener(output,&output_listener,NULL);
        }
    } else extra_global(registry,name,interface,version);
}
static void removed(void *d, struct wl_registry *r, uint32_t name) {}
static const struct wl_registry_listener registry_listener={.global=global,.global_remove=removed};
static bool connect_nested(void) {
    const char *runtime=getenv("XDG_RUNTIME_DIR"), *socket_name=getenv("WAYLAND_DISPLAY");
    char prefix[64]; struct stat info;
    snprintf(prefix,sizeof(prefix),"/run/user/%u/",getuid());
    if (getuid()<1000 || !runtime || strncmp(runtime,prefix,strlen(prefix)) ||
        !runtime[strlen(prefix)] || !socket_name || strchr(socket_name,'/') ||
        lstat(runtime,&info) || !S_ISDIR(info.st_mode) || info.st_uid!=getuid() || (info.st_mode&077))
        return false;
    display=wl_display_connect(NULL);
    if (!display) return false;
    struct wl_registry *registry=wl_display_get_registry(display);
    wl_registry_add_listener(registry,&registry_listener,NULL);
    if (wl_display_roundtrip(display)<0 || wl_display_roundtrip(display)<0) return false;
    if (output_count!=1 || !output || strncmp(output_name,"WAYLAND-",8)) return false;
    return true;
}
