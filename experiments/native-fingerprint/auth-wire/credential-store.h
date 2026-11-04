/* SPDX-License-Identifier: MIT */
#ifndef APOLLO_CREDENTIAL_STORE_H
#define APOLLO_CREDENTIAL_STORE_H
#include <stddef.h>
#include <stdint.h>
#define APOLLO_CREDENTIAL_SECRET_SIZE 32u
/* Caller holds an exclusive lock on a trusted, root-owned mode0700 directory.
 * 0 = complete credential, 1 = empty namespace, 2 = recoverable committed
 * handle with pending secret. Any ambiguous interrupted provisioning fails.
 */
int apollo_credential_load(int directory,uint8_t secret[32],uint8_t handle[512],size_t *handle_size);
int apollo_credential_begin(int directory,const uint8_t secret[32]);
int apollo_credential_save_handle(int directory,const uint8_t *handle,size_t size);
int apollo_credential_finish(int directory);
/* Explicit root recovery of a credential that has never reached BIO enrollment.
 * Consumes a root-only one-use marker; refuses any completed handle/secret.
 */
int apollo_credential_retry_unenrolled(int directory,uint8_t secret[32]);
#endif
