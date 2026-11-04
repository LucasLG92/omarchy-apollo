/* SPDX-License-Identifier: MIT */
#ifndef APOLLO_RPMB_READONLY_H
#define APOLLO_RPMB_READONLY_H
#include <stddef.h>
#include <stdint.h>
#include "rpmb-observer.h"
struct apollo_rpmb_read_metadata {uint32_t operation,frames,request_type;int storage_status;};
typedef int (*apollo_rpmb_read_fn)(const uint8_t request[512],uint32_t frames,uint8_t *response,void *context);
int apollo_rpmb_readonly(void *buffer,size_t size,apollo_rpmb_read_fn reader,void *context,struct apollo_rpmb_read_metadata *metadata);
int apollo_rpmb_ufs_read(const uint8_t request[512],uint32_t frames,uint8_t *response,void *context);
#endif
