/* SPDX-License-Identifier: MIT
 * Apollo early-boot selector. State is DATA, never shell code.
 * A fixed kernel is intentionally required until mobile kexec is validated.
 */
#define _GNU_SOURCE
#include <sys/file.h>
#include <sys/random.h>
#include <sys/stat.h>
#include <sys/utsname.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct { char good[66], previous[66], trial[66], launched[66], token[66];
    unsigned tries, failures; unsigned long long sequence; } State;
static int store, lockfd;
static void die(const char *why) { fprintf(stderr,"Apollo selector: %s\n",why); exit(1); }
static int ident(const char *s) {
    size_t n=strlen(s); if (!n || n>64 || !strcmp(s,".") || !strcmp(s,"..")) return 0;
    for (size_t i=0;i<n;i++) if (!((s[i]>='a'&&s[i]<='z')||(s[i]>='0'&&s[i]<='9')||s[i]=='-'||s[i]=='_')) return 0;
    return 1;
}
static int hash(const char *s) {
    if (strlen(s)!=64) return 0;
    for(int i=0;i<64;i++) if (!((s[i]>='0'&&s[i]<='9')||(s[i]>='a'&&s[i]<='f'))) return 0;
    return 1;
}
static int trusted(int fd, int dir) {
    struct stat st; return fd>=0 && !fstat(fd,&st) && st.st_uid==0 && !(st.st_mode&0022)
        && (dir?S_ISDIR(st.st_mode):(S_ISREG(st.st_mode)&&st.st_nlink==1));
}
static void acquire(const char *path) {
    if (geteuid()!=0 || path[0]!='/') die("root and an absolute store are required");
    int fd=open("/",O_RDONLY|O_DIRECTORY|O_CLOEXEC); char *copy=strdup(path), *part, *save;
    if(!copy) die("allocation");
    for(part=strtok_r(copy,"/",&save);part;part=strtok_r(NULL,"/",&save)) {
        if (!strcmp(part,".")||!strcmp(part,"..")) die("noncanonical store");
        int next=openat(fd,part,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
        close(fd); if(!trusted(next,1)) die("untrusted store path"); fd=next;
    }
    free(copy); store=fd;
    lockfd=openat(store,"selector.lock",O_RDWR|O_CREAT|O_NOFOLLOW|O_CLOEXEC,0600);
    if(!trusted(lockfd,0)||flock(lockfd,LOCK_EX)) die("lock unavailable");
}
static int line(FILE *f,char *out,size_t cap) {
    if(!fgets(out,(int)cap,f)) return 0;
    size_t n=strlen(out); if(!n||out[n-1]!='\n') return 0; out[n-1]=0; return 1;
}
static int number(const char *s,unsigned long long max,unsigned long long *out) {
    if(!*s || (s[0]=='0'&&s[1])) return 0;
    for(const char *p=s;*p;p++) if(*p<'0'||*p>'9') return 0;
    errno=0; char *end; unsigned long long v=strtoull(s,&end,10);
    if(errno||*end||v>max) return 0;
    *out=v; return 1;
}
static void load(State *s) {
    int fd=openat(store,"state-v1",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
    if(!trusted(fd,0)) die("untrusted state");
    struct stat st; if(fstat(fd,&st)||st.st_size>1024) die("oversized state");
    FILE *f=fdopen(fd,"r"); if(!f) die("state unavailable");
    char magic[32],tries[32],failures[32],sequence[32]; unsigned long long n;
    if(!line(f,magic,sizeof magic)||strcmp(magic,"APOLLO_STATE_1")||
       !line(f,s->good,sizeof s->good)||!line(f,s->previous,sizeof s->previous)||
       !line(f,s->trial,sizeof s->trial)||!line(f,tries,sizeof tries)||
       !line(f,s->launched,sizeof s->launched)||!line(f,s->token,sizeof s->token)||
       !line(f,failures,sizeof failures)||!line(f,sequence,sizeof sequence)||fgetc(f)!=EOF) die("invalid state");
    fclose(f);
    if(!ident(s->good)||!ident(s->previous)||!ident(s->trial)||!ident(s->launched)||
       (strcmp(s->token,"-")&&!hash(s->token))||!number(tries,2,&n)) die("invalid state fields");
    s->tries=(unsigned)n; if(!number(failures,2,&n)) die("invalid failures"); s->failures=(unsigned)n;
    if(!number(sequence,INT64_MAX,&s->sequence)) die("invalid sequence");
    if((!strcmp(s->trial,"-")&&s->tries)||(!strcmp(s->launched,"-")!=!strcmp(s->token,"-"))) die("inconsistent state");
}
static void randomhex(char *out) {
    unsigned char b[32]; size_t done=0;
    /* Early boot must fall back instead of waiting indefinitely for entropy. */
    while(done<sizeof b) { ssize_t n=getrandom(b+done,sizeof b-done,GRND_NONBLOCK); if(n<0&&errno==EINTR) continue; if(n<=0) die("random source not ready"); done+=(size_t)n; }
    for(int i=0;i<32;i++) sprintf(out+i*2,"%02x",b[i]);
    out[64]=0;
}
static void save(State *s) {
    char rand[65],name[96],body[1024]; randomhex(rand); snprintf(name,sizeof name,".state-%s",rand);
    int fd=openat(store,name,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(fd<0) die("cannot stage state");
    int len=snprintf(body,sizeof body,"APOLLO_STATE_1\n%s\n%s\n%s\n%u\n%s\n%s\n%u\n%llu\n",
        s->good,s->previous,s->trial,s->tries,s->launched,s->token,s->failures,s->sequence);
    if(len<0||(size_t)len>=sizeof body) die("state overflow");
    size_t done=0; while(done<(size_t)len) { ssize_t n=write(fd,body+done,(size_t)len-done);
        if(n<0&&errno==EINTR) continue;
        if(n<=0) die("state write");
        done+=(size_t)n; }
    if(fsync(fd)||close(fd)||renameat(store,name,store,"state-v1")||fsync(store)) die("state commit");
}
static int ready(const char *id) {
    if(!strcmp(id,"-")||!ident(id)) return 0;
    int deps=openat(store,"deployments",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(!trusted(deps,1)) { if(deps>=0) close(deps); return 0; }
    int d=openat(deps,id,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC); close(deps);
    if(!trusted(d,1)) { if(d>=0) close(d); return 0; }
    int fd=openat(d,"ready-v1",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
    if(!trusted(fd,0)) { if(fd>=0) close(fd); close(d); return 0; }
    FILE *f=fdopen(fd,"r"); char magic[32],record_id[80],kernel[128],digest[80]; struct utsname u;
    int ok=f&&line(f,magic,sizeof magic)&&(!strcmp(magic,"APOLLO_DEPLOYMENT_1")||!strcmp(magic,"APOLLO_DEPLOYMENT_2"))&&
        line(f,record_id,sizeof record_id)&&!strcmp(record_id,id)&&line(f,kernel,sizeof kernel)&&
        !uname(&u)&&!strcmp(kernel,u.release)&&line(f,digest,sizeof digest)&&hash(digest)&&fgetc(f)==EOF;
    if(f) fclose(f); else close(fd);
    const char *dirs[]={"usr","opt","pacman-local","adapter-state"};
    unsigned count=ok&&!strcmp(magic,"APOLLO_DEPLOYMENT_2")?4:3;
    for(unsigned i=0;i<count;i++) { int child=openat(d,dirs[i],O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
        if(!trusted(child,1)) ok=0;
        if(child>=0) close(child); }
    close(d); return ok;
}
int main(int argc,char **argv) {
    if(argc<3) die("usage: selector STORE init|select|status|seed|queue|bless|rollback");
    acquire(argv[1]); State s={0};
    if(!strcmp(argv[2],"init")&&argc==3) {
        struct stat st; if(!fstatat(store,"state-v1",&st,AT_SYMLINK_NOFOLLOW)||errno!=ENOENT) die("state already exists");
        strcpy(s.good,"-"); strcpy(s.previous,"-"); strcpy(s.trial,"-"); strcpy(s.launched,"-"); strcpy(s.token,"-"); save(&s); return 0;
    }
    load(&s);
    if(!strcmp(argv[2],"status")&&argc==3) {
        printf("%s\n%s\n%s\n%u\n%s\n%s\n%u\n%llu\n",s.good,s.previous,s.trial,s.tries,s.launched,s.token,s.failures,s.sequence); return 0;
    }
    if(!strcmp(argv[2],"seed")&&argc==4) {
        if(strcmp(s.good,"-")||strcmp(s.trial,"-")||strcmp(s.launched,"-")||!ready(argv[3])) die("cannot seed");
        strcpy(s.good,argv[3]); save(&s); return 0;
    }
    if(!strcmp(argv[2],"reseed")&&argc==4) {
        if(s.sequence||strcmp(s.trial,"-")||strcmp(s.launched,"-")||!ready(argv[3])) die("initial preparation is already in use");
        strcpy(s.previous,s.good);strcpy(s.good,argv[3]);s.failures=0;save(&s);return 0;
    }
    if(!strcmp(argv[2],"queue")&&argc==5) {
        unsigned long long sequence;
        if(!ident(argv[3])||!ready(argv[3])||!strcmp(argv[3],s.good)||strcmp(s.trial,"-")||
           strcmp(s.launched,"-")||!number(argv[4],INT64_MAX,&sequence)||sequence<=s.sequence) die("candidate not queueable");
        strcpy(s.trial,argv[3]); s.tries=2; s.sequence=sequence; save(&s); return 0;
    }
    if(!strcmp(argv[2],"select")&&argc==3) {
        if(strcmp(s.launched,"-")&&!strcmp(s.launched,s.good)&&s.failures<2) s.failures++;
        strcpy(s.launched,"-"); strcpy(s.token,"-");
        const char *selected="-";
        if(strcmp(s.trial,"-")&&s.tries&&ready(s.trial)) { selected=s.trial; s.tries--; }
        else { strcpy(s.trial,"-"); s.tries=0; if(s.failures<2&&ready(s.good)) selected=s.good; }
        char id[65]; strcpy(id,selected);
        if(strcmp(id,"-")) { strcpy(s.launched,id); randomhex(s.token); }
        save(&s); printf("%s\n%s\n",id,s.token); return 0;
    }
    if(!strcmp(argv[2],"bless")&&argc==5) {
        if(!ident(argv[3])||!hash(argv[4])||strcmp(s.launched,argv[3])||strcmp(s.token,argv[4])||!ready(argv[3])) die("stale or invalid boot proof");
        if(!strcmp(s.trial,argv[3])) { strcpy(s.previous,s.good); strcpy(s.good,s.trial); strcpy(s.trial,"-"); s.tries=0; }
        else if(strcmp(s.good,argv[3])) die("unexpected deployment");
        strcpy(s.launched,"-"); strcpy(s.token,"-"); s.failures=0; save(&s); return 0;
    }
    if(!strcmp(argv[2],"rollback")&&argc==3) {
        if(strcmp(s.launched,"-")||!ready(s.previous)) die("previous deployment unavailable");
        /* Keep current good until the rollback itself passes health. The
         * pending trial also prevents package writes before that reboot. */
        strcpy(s.trial,s.previous); s.tries=2; s.failures=0; save(&s); return 0;
    }
    die("invalid command");
}
