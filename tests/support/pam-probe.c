#define _GNU_SOURCE
#include <security/pam_appl.h>
#include <pwd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
static char token[513];
static int conversation(int count, const struct pam_message **messages, struct pam_response **out, void *unused) {
  (void)unused;
  struct pam_response *reply = calloc((size_t)count, sizeof(*reply));
  if (!reply) return PAM_BUF_ERR;
  for (int i = 0; i < count; i++) {
    if (messages[i]->msg_style == PAM_PROMPT_ECHO_OFF) reply[i].resp = strdup(token);
    else if (messages[i]->msg_style == PAM_PROMPT_ECHO_ON) reply[i].resp = strdup("");
    else if (messages[i]->msg_style != PAM_TEXT_INFO && messages[i]->msg_style != PAM_ERROR_MSG) {
      for (int j=0; j<i; j++) free(reply[j].resp);
      free(reply); return PAM_CONV_ERR;
    }
  }
  *out = reply; return PAM_SUCCESS;
}
int main(int argc, char **argv) {
  if (argc != 2 || !fgets(token, sizeof(token), stdin)) return 2;
  token[strcspn(token, "\n")] = '\0';
  struct passwd *owner = getpwuid(getuid());
  if (!owner) return 2;
  struct pam_conv conv = { conversation, NULL };
  pam_handle_t *handle = NULL;
  int status = pam_start(argv[1], owner->pw_name, &conv, &handle);
  if (status == PAM_SUCCESS) status = pam_authenticate(handle, 0);
  if (handle) pam_end(handle, status);
  explicit_bzero(token, sizeof(token));
  return status == PAM_SUCCESS ? 0 : 1;
}
