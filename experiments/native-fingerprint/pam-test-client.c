// Test fixture only, with synthetic credentials and synthetic user database.
#define _GNU_SOURCE
#include <security/pam_appl.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
static const char *response;
static void synthetic_delay(int result,unsigned int microseconds,void *data) {
 (void)result;(void)microseconds;(void)data;
}
static int conversation(int count,const struct pam_message **messages,
                        struct pam_response **answers,void *data) {
 (void)data;
 struct pam_response *result=calloc((size_t)count,sizeof(*result));
 if(!result)return PAM_BUF_ERR;
 for(int i=0;i<count;i++) {
  if(messages[i]->msg_style==PAM_PROMPT_ECHO_OFF || messages[i]->msg_style==PAM_PROMPT_ECHO_ON) {
   result[i].resp=strdup(response);
   if(!result[i].resp){for(int j=0;j<i;j++)free(result[j].resp);free(result);return PAM_BUF_ERR;}
  }
 }
 *answers=result;return PAM_SUCCESS;
}
int main(int argc,char **argv) {
 if(argc!=4)return 2;
 response=argv[3];struct pam_conv conv={conversation,NULL};pam_handle_t *pamh=NULL;
 int start=pam_start_confdir(argv[1],argv[2],&conv,"/test/pam.d",&pamh);
 int auth=start,account=-1,cred=-1;
 if(start==PAM_SUCCESS) {
  // This isolated fixture has no real account. Avoid sleeping for mocked
  // authentication failures; production's faillock/delays remain unchanged.
  pam_set_item(pamh,PAM_FAIL_DELAY,(const void *)synthetic_delay);
  auth=pam_authenticate(pamh,0);
  if(auth==PAM_SUCCESS){account=pam_acct_mgmt(pamh,0);cred=pam_setcred(pamh,PAM_ESTABLISH_CRED);}
  pam_end(pamh,auth);
 }
 printf("{\"auth\":%d,\"account\":%d,\"cred\":%d}\n",auth,account,cred);return 0;
}
