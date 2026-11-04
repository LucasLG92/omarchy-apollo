/* SPDX-License-Identifier: MIT */
#ifndef APOLLO_AUTH_CHECK_H
#define APOLLO_AUTH_CHECK_H
#include <stdbool.h>
#include <stdint.h>
struct apollo_auth_check {
    const char *phase;
    int code;
    bool FPC_version_verified, wrapped_key_imported, fresh_challenge_verified;
    bool keymaster_version_queried, keymaster_protocol_negotiated;
    uint32_t keymaster_version[4];
};
/* No enrollment, verification, credential provisioning or template operations.
 * Secret/wrapped blobs and nonce values never leave this function.
 */
int apollo_auth_check(struct apollo_auth_check *report);
int apollo_auth_version(void);
#endif
