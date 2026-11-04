/* SPDX-License-Identifier: MIT */
#ifndef APOLLO_RPMB_AUTHENTICATED_H
#define APOLLO_RPMB_AUTHENTICATED_H
#include "rpmb-readonly.h"
typedef int (*apollo_rpmb_write_fn)(const uint8_t *frames,uint32_t count,uint8_t result[512],void *context);
int apollo_rpmb_authenticated(void *buffer,size_t size,apollo_rpmb_read_fn reader,apollo_rpmb_write_fn writer,void *context,struct apollo_rpmb_read_metadata *metadata);
int apollo_rpmb_ufs_write(const uint8_t *frames,uint32_t count,uint8_t result[512],void *context);
#endif
