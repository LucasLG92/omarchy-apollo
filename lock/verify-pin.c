#define _GNU_SOURCE
#include <crypt.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <pwd.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/prctl.h>
#include <sys/random.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

/* Root-owned, fixed paths. No user-supplied filenames or hash output. */
#define PIN_ROOT "/var/lib/omarchy-apollo/pins"
#define MAX_PIN 12
struct retry_state { uint64_t failures; int64_t blocked_until; };

static int private_regular(int fd) {
  struct stat st;
  return fstat(fd, &st) == 0 && S_ISREG(st.st_mode) && st.st_uid == 0 &&
    (st.st_mode & 077) == 0 && st.st_nlink == 1;
}

static int user_directory(uid_t uid) {
  if (mkdir(PIN_ROOT, 0700) != 0 && errno != EEXIST) return -1;
  int parent = open(PIN_ROOT, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
  if (parent < 0) return -1;
  struct stat st;
  if (fstat(parent, &st) || st.st_uid != 0 || (st.st_mode & 077)) {
    close(parent); return -1;
  }
  char name[32];
  int length = snprintf(name, sizeof(name), "%lu", (unsigned long)uid);
  if (length < 1 || (size_t)length >= sizeof(name)) { close(parent); return -1; }
  if (mkdirat(parent, name, 0700) && errno != EEXIST) { close(parent); return -1; }
  int directory = openat(parent, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
  close(parent);
  if (directory < 0) return -1;
  if (fstat(directory, &st) || st.st_uid != 0 || (st.st_mode & 077)) {
    close(directory); return -1;
  }
  return directory;
}

static int read_pin(char *pin, size_t capacity) {
  size_t count = 0;
  for (;;) {
    struct pollfd ready = { .fd = STDIN_FILENO, .events = POLLIN };
    if (poll(&ready, 1, 30000) <= 0) return -1;
    unsigned char c;
    ssize_t got = read(STDIN_FILENO, &c, 1);
    if (got == 0) { pin[count] = '\0'; return (int)count; }
    if (got != 1) return -1;
    if (c == '\0' || c == '\n') { pin[count] = '\0'; return (int)count; }
    if (count + 1 >= capacity) return -1;
    pin[count++] = (char)c;
  }
}

static int valid_pin(const char *pin) {
  size_t size = strlen(pin);
  if (size < 6 || size > MAX_PIN) return 0;
  for (size_t i = 0; i < size; i++) if (pin[i] < '0' || pin[i] > '9') return 0;
  return 1;
}

static int write_all(int fd, const void *data, size_t size) {
  const char *bytes = data;
  while (size) {
    ssize_t written = write(fd, bytes, size);
    if (written < 0 && errno == EINTR) continue;
    if (written <= 0) return -1;
    bytes += written; size -= (size_t)written;
  }
  return 0;
}

static int save_state(int fd, const struct retry_state *state) {
  return lseek(fd, 0, SEEK_SET) < 0 || write_all(fd, state, sizeof(*state)) ||
    ftruncate(fd, sizeof(*state)) || fsync(fd);
}

static int constant_equal(const char *a, const char *b) {
  size_t length = strlen(a);
  if (length != strlen(b)) return 0;
  unsigned char different = 0;
  for (size_t i = 0; i < length; i++) different |= (unsigned char)a[i] ^ (unsigned char)b[i];
  return different == 0;
}

static int enroll(int directory) {
  char pin[MAX_PIN + 2] = {0}, confirmation[MAX_PIN + 2] = {0};
  unsigned char entropy[32];
  char salt[CRYPT_GENSALT_OUTPUT_SIZE];
  struct crypt_data result = {0};
  int status = 1, output = -1;
  if (read_pin(pin, sizeof(pin)) < 0 || read_pin(confirmation, sizeof(confirmation)) < 0 ||
      !valid_pin(pin) || !constant_equal(pin, confirmation)) goto out;
  if (getrandom(entropy, sizeof(entropy), 0) != (ssize_t)sizeof(entropy)) goto out;
  if (!crypt_gensalt_rn("$y$", 5, (const char *)entropy, sizeof(entropy), salt, sizeof(salt))) goto out;
  char *hash = crypt_r(pin, salt, &result);
  if (!hash || strncmp(hash, "$y$", 3)) goto out;
  output = openat(directory, "hash.new", O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
  if (output < 0 || !private_regular(output)) goto out;
  if (write_all(output, hash, strlen(hash)) || fsync(output)) goto out;
  if (renameat(directory, "hash.new", directory, "hash") || fsync(directory)) goto out;
  int state = openat(directory, "retry", O_WRONLY | O_CREAT | O_NOFOLLOW | O_CLOEXEC, 0600);
  if (state < 0 || !private_regular(state)) { if (state >= 0) close(state); goto out; }
  struct retry_state clean = {0};
  status = save_state(state, &clean) ? 1 : 0;
  close(state);
out:
  if (output >= 0) close(output);
  if (status) unlinkat(directory, "hash.new", 0);
  explicit_bzero(pin, sizeof(pin)); explicit_bzero(confirmation, sizeof(confirmation));
  explicit_bzero(entropy, sizeof(entropy)); explicit_bzero(&result, sizeof(result));
  return status;
}

static int verify(int directory) {
  char pin[MAX_PIN + 2] = {0}, stored[CRYPT_OUTPUT_SIZE] = {0};
  struct crypt_data result = {0};
  int status = 1;
  int lock = -1;
  /* Non-PIN input belongs to the independent Unix-password PAM fallback. */
  if (read_pin(pin, sizeof(pin)) < 0 || !valid_pin(pin)) goto out;
  lock = openat(directory, "retry", O_RDWR | O_CREAT | O_NOFOLLOW | O_CLOEXEC, 0600);
  if (lock < 0 || !private_regular(lock) || flock(lock, LOCK_EX)) goto out;
  struct retry_state state = {0};
  ssize_t size = pread(lock, &state, sizeof(state), 0);
  if (size != 0 && size != (ssize_t)sizeof(state)) goto out;
  time_t now = time(NULL);
  if (now < 0 || state.blocked_until > (int64_t)now) { status = 2; goto out; }
  int input = openat(directory, "hash", O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
  if (input < 0) goto out;
  if (!private_regular(input)) { close(input); goto out; }
  ssize_t count = read(input, stored, sizeof(stored) - 1);
  close(input);
  if (count < 1 || count >= (ssize_t)sizeof(stored) - 1 || strncmp(stored, "$y$", 3)) goto out;
  /* Reserve the attempt durably before hashing; storage failure fails closed. */
  if (state.failures < 100) state.failures++;
  uint64_t delay = state.failures < 5 ? 2 : (state.failures - 4) * 30;
  if (delay > 300) delay = 300;
  state.blocked_until = (int64_t)now + (int64_t)delay;
  if (save_state(lock, &state)) goto out;
  char *hash = crypt_r(pin, stored, &result);
  if (hash && constant_equal(hash, stored)) {
    struct retry_state clean = {0};
    status = save_state(lock, &clean) ? 1 : 0;
    goto out;
  }
out:
  if (lock >= 0) close(lock);
  explicit_bzero(pin, sizeof(pin)); explicit_bzero(stored, sizeof(stored));
  explicit_bzero(&result, sizeof(result));
  return status;
}

int main(int argc, char **argv) {
  struct rlimit core = {0, 0};
  if (setrlimit(RLIMIT_CORE, &core) || prctl(PR_SET_DUMPABLE, 0)) return 1;
  umask(077); alarm(35);
  uid_t caller = getuid(), target = caller;
  int enrolling = argc == 3 && !strcmp(argv[1], "--enroll");
  int checking_status = argc == 2 && !strcmp(argv[1], "--status");
  if (geteuid() != 0) return 1;
  if (enrolling) {
    if (caller != 0 || !argv[2][0] || strspn(argv[2], "0123456789") != strlen(argv[2])) return 1;
    errno = 0; unsigned long parsed = strtoul(argv[2], NULL, 10);
    if (errno || parsed < 1000 || parsed > UINT_MAX) return 1;
    target = (uid_t)parsed;
  } else if (argc != 1 && !checking_status) return 1;
  /* Polkit and sudo can launch PAM helpers with both UIDs already root.
   * Only a real-root caller may select the account named by PAM_USER.
   * A setuid invocation by an ordinary user stays bound to its real UID.
   */
  if (!enrolling && !checking_status && caller == 0) {
    const char *pam_user = getenv("PAM_USER");
    struct passwd *pam_owner = pam_user && *pam_user ? getpwnam(pam_user) : NULL;
    if (!pam_owner || pam_owner->pw_uid < 1000) return 1;
    target = pam_owner->pw_uid;
  }
  struct passwd *owner = getpwuid(target);
  if (!owner || target < 1000) return 1;
  if (!enrolling && !checking_status) {
    const char *pam_user = getenv("PAM_USER"), *pam_type = getenv("PAM_TYPE");
    if (!pam_user || strcmp(pam_user, owner->pw_name) || !pam_type || strcmp(pam_type, "auth")) return 1;
  }
  if (clearenv() || chdir("/")) return 1;
  int directory = user_directory(target);
  if (directory < 0) return 1;
  int status;
  if (checking_status) {
    int fd = openat(directory, "hash", O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    int configured = fd >= 0 && private_regular(fd);
    if (fd >= 0) close(fd);
    puts(configured ? "configured" : "missing");
    status = 0;
  } else if (enrolling) status = enroll(directory);
  else status = verify(directory);
  close(directory);
  return status;
}
