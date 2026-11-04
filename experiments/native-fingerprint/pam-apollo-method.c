// SPDX-License-Identifier: MIT
// Select a PAM conversation. This module NEVER authenticates a user by itself.
// An empty response selects pam_fprintd; a typed password uses the saved stack.
#define PAM_SM_AUTH
#define _GNU_SOURCE
#include <security/pam_modules.h>
#include <security/pam_ext.h>
#include <pwd.h>
#include <string.h>

PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh, int flags,
                                  int argc, const char **argv) {
    (void)flags;
    if (argc != 1) return PAM_SERVICE_ERR;
    if (strcmp(argv[0], "select-fingerprint")) return PAM_SERVICE_ERR;

    const char *service = NULL, *user = NULL, *token = NULL;
    int result = pam_get_item(pamh, PAM_SERVICE, (const void **)&service);
    if (result != PAM_SUCCESS || !service) return PAM_IGNORE;
    if (strcmp(service, "sddm") && strcmp(service, "sudo") &&
        strcmp(service, "polkit-1")) return PAM_IGNORE;
    result = pam_get_user(pamh, &user, NULL);
    if (result != PAM_SUCCESS || !user || !*user) return PAM_IGNORE;
    struct passwd entry, *found = NULL;
    char buffer[16384];
    if (getpwnam_r(user, &entry, buffer, sizeof buffer, &found) ||
        !found || entry.pw_uid != 1000) return PAM_IGNORE;
    // PAM owns and erases the token. Never copy, log, export, or persist it.
    result = pam_get_authtok(pamh, PAM_AUTHTOK, &token, NULL);
    if (result != PAM_SUCCESS || token == NULL) return PAM_IGNORE;
    return token[0] == '\0' ? PAM_SUCCESS : PAM_IGNORE;
}

PAM_EXTERN int pam_sm_setcred(pam_handle_t *pamh, int flags,
                            int argc, const char **argv) {
    (void)pamh; (void)flags; (void)argc; (void)argv;
    // Authentication has already selected a verified branch. Like other
    // method selectors, this module has no credentials of its own to set.
    return PAM_SUCCESS;
}
