/* SPDX-License-Identifier: MIT */
#ifndef APOLLO_RPMB_OBSERVER_H
#define APOLLO_RPMB_OBSERVER_H
#include <stddef.h>
#include <stdint.h>
#define APOLLO_RPMB_SERVICE 8192u
/* The wire protocol needs 20040 bytes; TEE shared allocations are page rounded. */
#define APOLLO_RPMB_BUFFER 20480u
/* Diagnostic only. Never reads frames, opens storage or reports success. */
int apollo_rpmb_observe(void *buffer,size_t size,uint32_t *operation);
#endif
