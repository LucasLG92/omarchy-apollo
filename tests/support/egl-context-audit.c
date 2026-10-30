/* SPDX-License-Identifier: MIT */
/* Test-only interposer: counts successful context creation/destruction.
 * It logs no handles, application data, file names or image contents.
 */
#define _GNU_SOURCE
#include <EGL/egl.h>
#include <dlfcn.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static EGLContext (*create_context)(EGLDisplay, EGLConfig, EGLContext, const EGLint *);
static EGLBoolean (*destroy_context)(EGLDisplay, EGLContext);
static atomic_ulong created, destroyed;

__attribute__((constructor)) static void resolve_functions(void)
{
    create_context = dlsym(RTLD_NEXT, "eglCreateContext");
    destroy_context = dlsym(RTLD_NEXT, "eglDestroyContext");
    if (!create_context || !destroy_context)
        abort();
}

static void report(void)
{
    char line[128];
    int length = snprintf(line, sizeof line,
        "APOLLO_EGL_AUDIT created=%lu destroyed=%lu\n",
        atomic_load(&created), atomic_load(&destroyed));
    if (length > 0 && (size_t)length < sizeof line)
        (void)write(STDERR_FILENO, line, (size_t)length);
}

EGLContext eglCreateContext(EGLDisplay display, EGLConfig config,
                            EGLContext share, const EGLint *attributes)
{
    EGLContext context = create_context(display, config, share, attributes);
    if (context != EGL_NO_CONTEXT) {
        atomic_fetch_add(&created, 1);
        report();
    }
    return context;
}

EGLBoolean eglDestroyContext(EGLDisplay display, EGLContext context)
{
    EGLBoolean result = destroy_context(display, context);
    if (result == EGL_TRUE && context != EGL_NO_CONTEXT) {
        atomic_fetch_add(&destroyed, 1);
        report();
    }
    return result;
}
