/* SPDX-License-Identifier: MIT */
#ifndef APOLLO_TIME_LISTENER_H
#define APOLLO_TIME_LISTENER_H
#include <stddef.h>
#include <stdint.h>
struct qs_store;
/* Qualcomm numeric service11; UTC wall time, not an authentication clock.
 * The TA must continue to use its secure clock for lockout and token expiry.
 */
int apollo_time_reply(void *buffer,size_t size,int64_t seconds,int32_t nanoseconds);
int apollo_time_dispatch(struct qs_store *unused,void *buffer,size_t size);
#endif
