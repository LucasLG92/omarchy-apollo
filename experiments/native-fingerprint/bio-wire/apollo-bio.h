/* SPDX-License-Identifier: MIT */
#pragma once
#include <stddef.h>
#include <stdint.h>
#define APOLLO_BIO_BYTES 4096u
#define APOLLO_BIO_MAX_IDS 25u
struct apollo_bio_result {int transport;int32_t outer;};
typedef int (*apollo_bio_exchange)(void *,void *,size_t,int32_t *);
struct apollo_bio {void *context;apollo_bio_exchange exchange;};
int apollo_bio_init(struct apollo_bio *);
int apollo_bio_group(struct apollo_bio *,uint32_t);
int apollo_bio_ids(struct apollo_bio *,uint32_t [APOLLO_BIO_MAX_IDS],uint32_t *);
int apollo_bio_begin(struct apollo_bio *);
int apollo_bio_sample(struct apollo_bio *,uint32_t *);
int apollo_bio_end(struct apollo_bio *,uint32_t *);
int apollo_sensor_command(struct apollo_bio *,uint32_t,uint32_t *);
#define APOLLO_BIO_DB_MAX (4u*1024u*1024u)
/* Only the TA-wrapped authenticated database, never raw templates/images. */
int apollo_bio_export(struct apollo_bio *,uint8_t **,size_t *);
int apollo_bio_import(struct apollo_bio *,const uint8_t *,size_t);
int apollo_bio_wrapped_database(const uint8_t *,size_t);
int apollo_bio_identify(struct apollo_bio *,uint32_t *);
int apollo_bio_challenge(struct apollo_bio *,uint64_t);
int apollo_bio_fresh_result(struct apollo_bio *,uint64_t);
/* Match semantics intentionally not supplied until observed against Apollo TA. */
