/* SPDX-License-Identifier: MIT */
/* Snapshot a RAM splash via read-only KMS queries and a read-only mapping.
 * No modeset, authentication change, input injection, or DRM master request.
 */
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <xf86drm.h>
#include <xf86drmMode.h>
#include <drm_fourcc.h>
#include <drm_mode.h>
#include <png.h>

int main(int argc, char **argv)
{
    if (argc == 2 && !strcmp(argv[1], "--help")) {
        puts("Capture only the native Apollo RAM boot splash as PNG on stdout.");
        return 0;
    }
    if (argc != 1 || access("/etc/apollo/ram-splash-probe", F_OK)) return 2;
    char compatible[512] = {0};
    int dt = open("/sys/firmware/devicetree/base/compatible", O_RDONLY | O_CLOEXEC);
    if (dt < 0) return 2;
    ssize_t size = read(dt, compatible, sizeof(compatible)-1); close(dt);
    if (size <= 0 || !memmem(compatible, size, "xiaomi,apollo", 13)) return 2;
    int fd = open("/dev/dri/card0", O_RDWR | O_CLOEXEC);
    if (fd < 0) { perror("DRM open"); return 3; }
    drmModeRes *resources = drmModeGetResources(fd);
    if (!resources) { perror("DRM resources"); close(fd); return 3; }
    uint32_t id = 0;
    for (int i = 0; i < resources->count_crtcs; i++) {
        drmModeCrtc *crtc = drmModeGetCrtc(fd, resources->crtcs[i]);
        if (crtc) {
            if (crtc->mode_valid && crtc->buffer_id) id = crtc->buffer_id;
            drmModeFreeCrtc(crtc);
        }
        if (id) break;
    }
    drmModeFreeResources(resources);
    drmModeFB2 *fb = id ? drmModeGetFB2(fd, id) : NULL;
    if (!fb || !fb->handles[0]) { fprintf(stderr, "No readable active splash buffer\n"); close(fd); return 4; }
    int reverse = fb->pixel_format == DRM_FORMAT_XRGB8888 || fb->pixel_format == DRM_FORMAT_ARGB8888;
    int direct = fb->pixel_format == DRM_FORMAT_XBGR8888 || fb->pixel_format == DRM_FORMAT_ABGR8888;
    uint64_t bytes = (uint64_t)fb->pitches[0] * fb->height + fb->offsets[0];
    if ((!reverse && !direct) || fb->modifier != DRM_FORMAT_MOD_LINEAR ||
        !fb->width || !fb->height || fb->width > 4096 || fb->height > 4096 ||
        fb->pitches[0] < fb->width * 4 || bytes > 128*1024*1024) {
        fprintf(stderr, "Unsupported splash buffer geometry/format\n"); drmModeFreeFB2(fb); close(fd); return 4;
    }
    struct drm_mode_map_dumb map = {.handle = fb->handles[0]};
    if (ioctl(fd, DRM_IOCTL_MODE_MAP_DUMB, &map)) { perror("DRM read mapping"); drmModeFreeFB2(fb); close(fd); return 4; }
    const unsigned char *pixels = mmap(NULL, bytes, PROT_READ, MAP_SHARED, fd, map.offset);
    if (pixels == MAP_FAILED) { perror("mmap read"); drmModeFreeFB2(fb); close(fd); return 4; }
    unsigned char *rgb = malloc((size_t)fb->width * fb->height * 3);
    if (!rgb) { munmap((void *)pixels, bytes); drmModeFreeFB2(fb); close(fd); return 5; }
    for (uint32_t y = 0; y < fb->height; y++) {
        const unsigned char *row = pixels + fb->offsets[0] + (size_t)y*fb->pitches[0];
        for (uint32_t x = 0; x < fb->width; x++) {
            unsigned char *out = rgb + ((size_t)y*fb->width+x)*3;
            out[0] = row[x*4+(reverse?2:0)]; out[1] = row[x*4+1]; out[2] = row[x*4+(reverse?0:2)];
        }
    }
    png_image image = {0}; image.version = PNG_IMAGE_VERSION;
    image.width = fb->width; image.height = fb->height; image.format = PNG_FORMAT_RGB;
    int ok = png_image_write_to_stdio(&image, stdout, 0, rgb, 0, NULL);
    if (!ok) fprintf(stderr, "PNG write failed: %s\n", image.message);
    else fprintf(stderr, "Native splash PNG: %ux%u\n", fb->width, fb->height);
    png_image_free(&image); free(rgb); munmap((void *)pixels, bytes);
    drmModeFreeFB2(fb); close(fd);
    return ok ? 0 : 5;
}
