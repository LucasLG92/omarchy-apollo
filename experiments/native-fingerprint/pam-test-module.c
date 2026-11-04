// Test fixture only. NEVER packaged or installed on the phone.
#define PAM_SM_AUTH
#define PAM_SM_ACCOUNT
#include <security/pam_modules.h>
#include <security/pam_ext.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh,int flags,int argc,const char **argv) {
 (void)flags;
 if(argc!=2)return PAM_SERVICE_ERR;
 FILE *log=fopen("/test/route.log","a");if(!log)return PAM_SYSTEM_ERR;
 fputs(argv[0],log);fputc('\n',log);fclose(log);
 if(!strcmp(argv[0],"password")) {
  const char *token=NULL;
  int r=pam_get_authtok(pamh,PAM_AUTHTOK,&token,NULL);
  if(r!=PAM_SUCCESS || !token || strcmp(token,"test-only-correct"))return PAM_AUTH_ERR;
 }
 return atoi(argv[1]);
}
PAM_EXTERN int pam_sm_setcred(pam_handle_t *pamh,int flags,int argc,const char **argv) {
 (void)pamh;(void)flags;(void)argc;(void)argv;return PAM_SUCCESS;
}
PAM_EXTERN int pam_sm_acct_mgmt(pam_handle_t *pamh,int flags,int argc,const char **argv) {
 (void)pamh;(void)flags;if(argc!=2)return PAM_SERVICE_ERR;return atoi(argv[1]);
}
