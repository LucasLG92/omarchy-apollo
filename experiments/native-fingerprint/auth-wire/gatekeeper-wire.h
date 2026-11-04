/* SPDX-License-Identifier: MIT */
#ifndef APOLLO_GATEKEEPER_WIRE_H
#define APOLLO_GATEKEEPER_WIRE_H
#include <stddef.h>
#include <stdint.h>
#define APOLLO_GK_MAX_MESSAGE 2048u
#define APOLLO_GK_MAX_HANDLE 512u
#define APOLLO_GK_HAT_SIZE 69u
/* Reserved Linux-only credential namespace. Never reuse Android UID0. */
#define APOLLO_GK_UID_FIRST UINT32_C(0x4f4d0000)
#define APOLLO_GK_UID_LAST UINT32_C(0x4f4dffff)
int apollo_gk_encode_enroll(uint32_t uid,const uint8_t *secret,size_t secret_len,
 const uint8_t *old_handle,size_t handle_len,const uint8_t *old_secret,size_t old_secret_len,
 uint8_t *output,size_t capacity,size_t *length);
int apollo_gk_encode_verify(uint32_t uid,uint64_t challenge,const uint8_t *handle,size_t handle_len,
 const uint8_t *secret,size_t secret_len,uint8_t *output,size_t capacity,size_t *length);
int apollo_gk_decode_handle(const uint8_t *response,size_t size,uint8_t *handle,size_t capacity,size_t *length);
/* Decode a real secure-world response, bind it to the requested nonce and
 * preserve the HAL's byte order. This does NOT validate the HMAC or authorize
 * a fingerprint enrollment: the FPC trusted application must do that.
 */
int apollo_gk_decode_token(const uint8_t *response,size_t size,uint64_t expected_challenge,
 uint8_t token[APOLLO_GK_HAT_SIZE]);
/* Apollo's observed Keymaster4.0 selects the HAL's legacy binary protocol.
 * Never select CBOR merely because the global negotiation was accepted.
 */
int apollo_gk_encode_legacy_enroll(uint32_t uid,const uint8_t *secret,size_t secret_len,
 const uint8_t *old_handle,size_t handle_len,const uint8_t *old_secret,size_t old_secret_len,
 uint8_t *output,size_t capacity,size_t *length);
int apollo_gk_encode_legacy_verify(uint32_t uid,uint64_t challenge,const uint8_t *handle,size_t handle_len,
 const uint8_t *secret,size_t secret_len,uint8_t *output,size_t capacity,size_t *length);
int apollo_gk_decode_legacy_handle(const uint8_t *response,size_t size,uint8_t *handle,size_t capacity,size_t *length);
int apollo_gk_decode_legacy_token(const uint8_t *response,size_t size,uint64_t expected_challenge,
 uint8_t token[APOLLO_GK_HAT_SIZE]);
#endif
