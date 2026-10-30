#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QProcess>
#include <QRegularExpression>
#include <QFile>
#include <QDir>
#include <QTimer>
#include <QSaveFile>
#include <pwd.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>
#include <cstdlib>

class PinSetup : public QObject {
  Q_OBJECT
  Q_PROPERTY(QString message READ message NOTIFY messageChanged)
  Q_PROPERTY(bool complete READ complete NOTIFY messageChanged)
  uid_t owner;
  QString text;
  bool saved = false;
public:
  explicit PinSetup(uid_t uid) : owner(uid) {}
  QString message() const { return text; }
  bool complete() const { return saved; }
  Q_INVOKABLE bool enroll(const QString &first, const QString &second) {
    if (saved) return false;
    static const QRegularExpression digits(QStringLiteral("^[0-9]{6,12}$"));
    if (!digits.match(first).hasMatch() || first != second) {
      text = QStringLiteral("Repite el mismo PIN de 6 a 12 dígitos."); emit messageChanged(); return false;
    }
    QProcess check;
    check.start(QStringLiteral("/usr/lib/omarchy/apollo/verify-pin"), {QStringLiteral("--enroll"), QString::number(owner)});
    if (!check.waitForStarted(3000)) {
      text = QStringLiteral("No se pudo abrir el servicio del PIN."); emit messageChanged(); return false;
    }
    QByteArray input = first.toLatin1() + '\n' + second.toLatin1() + '\n';
    check.write(input); input.fill('\0'); check.closeWriteChannel();
    bool finished = check.waitForFinished(5000);
    if (!finished || check.exitStatus() != QProcess::NormalExit || check.exitCode() != 0) {
      check.kill(); check.waitForFinished(1000);
      text = QStringLiteral("No se ha podido guardar el PIN. Vuelve a intentarlo."); emit messageChanged(); return false;
    }
    QFile pamSource(QStringLiteral("/usr/share/omarchy-apollo-lock/omarchy-lock-password"));
    QSaveFile pamTarget(QStringLiteral("/etc/pam.d/omarchy-lock-password"));
    if (!pamSource.open(QIODevice::ReadOnly) || !pamTarget.open(QIODevice::WriteOnly)) {
      text = QStringLiteral("El PIN se guardó, pero falta configurar el bloqueo."); emit messageChanged(); return false;
    }
    QByteArray pam = pamSource.readAll();
    if (pam.isEmpty() || pamTarget.write(pam) != pam.size() || !pamTarget.commit()) {
      text = QStringLiteral("No se ha podido completar el bloqueo."); emit messageChanged(); return false;
    }
    QFile::setPermissions(pamTarget.fileName(), QFileDevice::ReadOwner | QFileDevice::WriteOwner | QFileDevice::ReadGroup | QFileDevice::ReadOther);
    QDir().mkpath(QStringLiteral("/var/lib/omarchy-apollo/pin-status"));
    QSaveFile marker(QStringLiteral("/var/lib/omarchy-apollo/pin-status/") + QString::number(owner));
    if (!marker.open(QIODevice::WriteOnly) || marker.write("configured\n") != 11 || !marker.commit()) {
      text = QStringLiteral("El PIN se guardó, pero falta terminar la configuración."); emit messageChanged(); return false;
    }
    QFile::setPermissions(marker.fileName(), QFileDevice::ReadOwner | QFileDevice::WriteOwner | QFileDevice::ReadGroup | QFileDevice::ReadOther);
    saved = true;
    text = QStringLiteral("PIN guardado. La contraseña de administración se conserva.");
    emit messageChanged();
    QTimer::singleShot(3000, qApp, &QCoreApplication::quit);
    return true;
  }
signals:
  void messageChanged();
};

int main(int argc, char **argv) {
  if (getuid() != 0 || geteuid() != 0 || argc != 3) return 1;
  bool valid = false;
  uint uid = QString::fromLocal8Bit(argv[1]).toUInt(&valid);
  if (!valid || uid < 1000 || !getpwuid(uid)) return 1;
  QString display = QString::fromLocal8Bit(argv[2]);
  if (!QRegularExpression(QStringLiteral("^wayland-[0-9]+$")).match(display).hasMatch()) return 1;
  QString runtime = QStringLiteral("/run/user/") + QString::number(uid);
  struct stat socket;
  if (lstat((runtime + '/' + display).toLocal8Bit().constData(), &socket) ||
      !S_ISSOCK(socket.st_mode) || socket.st_uid != uid) return 1;
  const char *adminRuntime = "/run/omarchy-apollo-root";
  if (mkdir(adminRuntime, 0700) && errno != EEXIST) return 1;
  struct stat adminDirectory;
  if (lstat(adminRuntime, &adminDirectory) || !S_ISDIR(adminDirectory.st_mode) ||
      adminDirectory.st_uid != 0 || (adminDirectory.st_mode & 077)) return 1;
  struct rlimit core = {0, 0};
  if (setrlimit(RLIMIT_CORE, &core) || prctl(PR_SET_DUMPABLE, 0) || clearenv()) return 1;
  umask(077);
  qputenv("PATH", "/usr/bin"); qputenv("HOME", "/root"); qputenv("LANG", "C.UTF-8");
  qputenv("QT_QPA_PLATFORM", "wayland"); qputenv("QT_QUICK_CONTROLS_STYLE", "Basic");
  qputenv("QT_LOGGING_RULES", "*.debug=false");
  qputenv("XDG_RUNTIME_DIR", adminRuntime);
  qputenv("WAYLAND_DISPLAY", (runtime + '/' + display).toLocal8Bit());
  int appArgc = 1;
  QGuiApplication app(appArgc, argv);
  app.setApplicationName(QStringLiteral("Apollo PIN setup"));
  PinSetup backend(uid);
  QQmlApplicationEngine engine;
  engine.rootContext()->setContextProperty(QStringLiteral("pinSetup"), &backend);
  engine.load(QUrl(QStringLiteral("qrc:/PinSetup.qml")));
  if (engine.rootObjects().isEmpty()) return 1;
  return app.exec();
}

#include "pin-setup.moc"
