// SPDX-License-Identifier: MIT
// Isolated synthetic D-Bus service, never the production account broker.
#include <QGuiApplication>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQuickView>
#include <QQuickItem>
#include <QInputMethod>
#include <QMetaProperty>
#include <QAbstractListModel>
#include <QDBusConnection>
#include <QElapsedTimer>
#include <QThread>
#include <QTextStream>
#include <QTest>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <functional>

class MockProvisioner : public QObject {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.apollo.OwnerProvisioning1")
public:
    QString phase = "unowned";
    QString expectedName, expectedCredential;
    int calls = 0;
    bool exact = false;
    bool profileExact = false;
public slots:
    QString GetState() { return phase; }
    QString Configure(const QString &name, const QString &credential) {
        ++calls;
        exact = name == expectedName && credential == expectedCredential;
        // No logging, file or actual account/PAM sink exists in this mock.
        return exact ? "configured" : "NEEDS_ADMIN";
    }
    QString ConfigureProfile(const QString &name, const QString &credential, const QString &profile) {
        auto p = QJsonDocument::fromJson(profile.toUtf8()).object();
        profileExact = p.value("schema").toInt() == 1 && p.value("hostname").toString() == "apollo" && p.value("apps").toArray().isEmpty();
        return profileExact ? Configure(name, credential) : "INVALID_PROFILE";
    }
};
class MockModel : public QAbstractListModel {
    Q_OBJECT
    Q_PROPERTY(QString lastUser READ lastUser CONSTANT)
    Q_PROPERTY(int lastIndex READ lastIndex CONSTANT)
public:
    QString lastUser() const { return {}; } // clean installation has no lastUser
    int lastIndex() const { return 0; }
    int rowCount(const QModelIndex &parent = {}) const override { return parent.isValid() ? 0 : 1; }
    QVariant data(const QModelIndex &, int role) const override {
        if (role == Qt::DisplayRole) return "hyprland-uwsm";
        if (role == Qt::UserRole + 1) return "alice"; // SDDM v0.21 NameRole
        return {};
    }
};
class MockConfig : public QObject {
    Q_OBJECT
public:
    Q_INVOKABLE bool boolValue(const QString &) { return true; }
    Q_INVOKABLE QString stringValue(const QString &) { return {}; }
};
class MockSddm : public QObject {
    Q_OBJECT
public:
    int logins = 0;
    QString lastName;
    int credentialLength = 0;
    Q_INVOKABLE void login(const QString &name, const QString &credential, int) {
        ++logins; lastName = name; credentialLength = credential.size();
    }
signals:
    void loginFailed();
    void loginSucceeded();
};

int main(int argc, char **argv) {
    QGuiApplication app(argc, argv);
    // The runner supplies a disposable session daemon as the SYSTEM address;
    // bwrap exposes no host system bus and no production account backend.
    if (!qEnvironmentVariable("DBUS_SYSTEM_BUS_ADDRESS").startsWith("unix:")) return 2;
    MockProvisioner broker;
    auto bus = QDBusConnection::systemBus();
    if (!bus.registerService("org.apollo.OwnerProvisioning1") ||
        !bus.registerObject("/org/apollo/OwnerProvisioning1", &broker, QDBusConnection::ExportAllSlots)) return 3;
    int checks = 0;
    auto check = [&](bool value, const char *label) {
        if (!value) { QTextStream(stderr) << "FAILED " << label << Qt::endl; ::exit(1); }
        ++checks;
    };
    auto wait = [&](const std::function<bool()> &predicate) {
        QElapsedTimer timer; timer.start();
        while (!predicate() && timer.elapsed() < 10000) { app.processEvents(); QThread::msleep(2); }
        return predicate();
    };
    MockModel users, sessions; MockConfig config; MockSddm sddm;
    QQuickView view;
    view.setResizeMode(QQuickView::SizeRootObjectToView);
    view.engine()->addImportPath("/work/pkg/usr/lib/qt6/qml");
    view.rootContext()->setContextProperty("userModel", &users);
    view.rootContext()->setContextProperty("sessionModel", &sessions);
    view.rootContext()->setContextProperty("config", &config);
    view.rootContext()->setContextProperty("sddm", &sddm);
    view.setSource(QUrl::fromLocalFile("/work/pkg/usr/share/sddm/themes/omarchy-apollo-firstboot/Main.qml"));
    check(view.status() == QQuickView::Ready, "qml-load");
    view.resize(432, 960); view.show();
    check(QTest::qWaitForWindowExposed(&view), "offscreen-window-exposed");
    auto root = view.rootObject();
    check(wait([&]{ return root->width() == 432 && root->height() == 960; }), "portrait-viewport");
    std::function<QQuickItem *(QQuickItem *, const QString &)> visual = [&](QQuickItem *item, const QString &name) -> QQuickItem * {
        if (item->objectName() == name) return item;
        for (auto *child : item->childItems()) if (auto *found = visual(child, name)) return found;
        return nullptr;
    };
    auto controller = root->findChild<QObject *>("ownerController");
    check(controller && wait([&]{ return controller->property("phase") == "unowned"; }), "private-bus-state");
    auto invokeText = [&](const QString &text) { return QMetaObject::invokeMethod(controller, "insertText", Q_ARG(QString, text)); };
    auto select = [&](int field) { return QMetaObject::invokeMethod(controller, "selectField", Q_ARG(int, field)); };
    auto call = [&](const char *method) { return QMetaObject::invokeMethod(controller, method); };
    check(root->findChild<QObject *>("firstBootForm") != nullptr, "initial-form");
    auto wizard = root->findChild<QObject *>("firstBootForm");
    check(wizard->setProperty("step", 2), "wizard-password-step");
    auto keyboard = root->findChild<QObject *>("touchKeyboard");
    check(keyboard && !keyboard->property("visible").toBool(), "keyboard-initially-hidden");
    check(wait([&]{ return visual(root, "ownerField1") != nullptr; }), "password-button");
    auto field = visual(root, "ownerField1");
    view.grabWindow(); // Complete positioner polish before deriving touch coordinates.
    auto location = field->mapToScene(QPointF(field->width()/2, field->height()/2)).toPoint();
    QTest::mouseClick(&view, Qt::LeftButton, Qt::NoModifier, location);
    check(wait([&]{ return controller->property("field").toInt() == 1 && keyboard->property("visible").toBool(); }), "touch-password-focus");
    check(!QGuiApplication::inputMethod()->isVisible(), "no-system-ime-surface");
    check(select(0) && invokeText("alice"), "name-entry");
    check(select(1) && invokeText(QString::fromUtf8(" \xc3\xa1:Demo9!")), "unicode-spaces-colon-entry");
    check(controller->property("passwordLength").toInt() == 9, "codepoint-count");
    auto second = visual(root, "ownerField2");
    view.grabWindow();
    location = second->mapToScene(QPointF(second->width()/2, second->height()/2)).toPoint();
    QTest::mouseClick(&view, Qt::LeftButton, Qt::NoModifier, location);
    check(wait([&]{ return controller->property("field").toInt() == 2; }), "second-field-touch-focus");
    check(invokeText("different8") && call("submit"), "mismatch-submit");
    check(controller->property("errorCode") == "MISMATCH" && broker.calls == 0, "mismatch-no-rpc");
    check(call("clear") && controller->property("passwordLength").toInt() == 0 && controller->property("confirmationLength").toInt() == 0, "both-clear");
    select(1); invokeText(QString(129, 'a')); select(2); invokeText(QString(129, 'a')); call("submit");
    check(controller->property("errorCode") == "INVALID_PASSWORD" && broker.calls == 0, "overflow-not-truncated-to-valid");
    call("clear"); select(1); invokeText(QString::fromUtf8("1234567\xf0\x9f\x94\x92"));
    check(controller->property("passwordLength").toInt() == 8, "supplementary-codepoint");
    call("erase"); check(controller->property("passwordLength").toInt() == 7, "erase-entire-surrogate-pair");
    call("clear"); select(1); invokeText("abc\ndefgh9");
    check(controller->property("passwordLength").toInt() == 0, "newline-rejected");
    for (int i = 0; i < controller->metaObject()->propertyCount(); ++i) {
        QByteArray property = controller->metaObject()->property(i).name();
        check(property != "password" && property != "credential" && property != "confirmation", "no-secret-property");
    }
    broker.expectedName = "alice"; broker.expectedCredential = QString::fromUtf8(" \xc3\xa1:Demo9!");
    select(1); invokeText(broker.expectedCredential); select(2); invokeText(broker.expectedCredential);
    call("submit");
    check(controller->property("passwordLength").toInt() == 0 && controller->property("confirmationLength").toInt() == 0, "clear-before-bus-response");
    check(wait([&]{ return controller->property("phase") == "configured"; }) && broker.calls == 1 && broker.exact, "fixed-rpc-only");
    check(sddm.logins == 0, "no-password-replay-autologin");
    broker.phase = "finish-pending"; broker.expectedName.clear(); broker.expectedCredential.clear();
    call("refresh"); check(wait([&]{ return controller->property("phase") == "finish-pending"; }), "recovery-state");
    call("submit"); check(wait([&]{ return broker.calls == 2 && controller->property("phase") == "configured"; }) && broker.exact, "recovery-no-new-secret");
    broker.phase = "ready"; call("refresh");
    check(wait([&]{ return controller->property("phase") == "ready"; }), "owned-readonly-state");
    check(wait([&]{ return root->findChild<QObject *>("credentialInput") != nullptr; }), "normal-login-loaded");
    call("submit"); check(broker.calls == 2, "owned-no-configure");
    check(sddm.logins == 0, "normal-pam-waits-for-human");
    auto input = visual(root, "credentialInput");
    view.grabWindow();
    location = input->mapToScene(QPointF(input->width()/2, input->height()/2)).toPoint();
    QTest::mouseClick(&view, Qt::LeftButton, Qt::NoModifier, location);
    auto normalKeyboard = root->findChild<QObject *>("touchKeyboard");
    check(wait([&]{ return normalKeyboard && normalKeyboard->property("visible").toBool(); }), "owned-manual-keyboard-focus");
    check(QMetaObject::invokeMethod(normalKeyboard, "pressPasswordKey", Q_ARG(QVariant, QVariant("a"))), "owned-letter-key");
    check(input->property("text") == "a", "owned-letter-input");
    auto loginForm = root->findChild<QObject *>("normalLogin");
    check(users.lastUser().isEmpty(), "clean-install-empty-last-user");
    check(loginForm && QMetaObject::invokeMethod(loginForm, "submit"), "normal-manual-submit");
    check(sddm.logins == 1 && sddm.lastName == "alice" && sddm.credentialLength == 1, "custom-name-role257-pam-mock");
    QMetaObject::invokeMethod(&sddm, "loginFailed");
    check(input->property("text").toString().isEmpty(), "owned-failed-login-clears-input");
    broker.phase = "unavailable"; call("refresh");
    check(wait([&]{ return controller->property("phase") == "unavailable"; }), "unavailable-state");
    check(wait([&]{ return visual(root, "retryState") != nullptr; }), "unavailable-retry-present");
    call("submit"); check(broker.calls == 2, "unavailable-no-configure");
    check(!visual(root, "configureOwner")->isVisible(), "unavailable-no-create-button");
    broker.phase = "unowned"; call("refresh");
    check(wait([&]{ return controller->property("phase") == "unowned"; }), "unavailable-retry-recovers");
    wizard = root->findChild<QObject *>("firstBootForm");
    for (int step = 0; step < 6; ++step) {
        wizard->setProperty("step", step); wizard->setProperty("keyboardVisible", false);
        view.grabWindow().save("/work/review/step-" + QString::number(step) + ".png");
        auto button = visual(root, "configureOwner");
        auto bottom = button->mapToScene(QPointF(button->width(), button->height()));
        check(button->isVisible() && bottom.x() <= view.width() && bottom.y() <= view.height(), "wizard-action-fits-portrait");
    }
    broker.expectedName = "alice"; broker.expectedCredential = "Synthetic9!";
    view.resize(1080, 2400);
    check(wait([&]{return root->width()==1080 && root->height()==2400;}), "native-panel-viewport");
    view.grabWindow();
    wizard->setProperty("step", 2); wizard->setProperty("keyboardVisible", true); view.grabWindow();
    auto touch = visual(root, "touchKeyboard");
    auto left = touch->mapToScene(QPointF(0,0)); auto right = touch->mapToScene(QPointF(touch->width(),touch->height()));
    if (!(left.x() >= -1 && right.x() <= 1081 && right.y() <= 2300 && right.x()-left.x() >= 1000))
        QTextStream(stderr) << "Synthetic keyboard bounds " << left.x() << "," << left.y() << " -> " << right.x() << "," << right.y() << Qt::endl;
    check(left.x() >= -1 && right.x() <= 1081 && right.y() <= 2300 && right.x()-left.x() >= 1000, "native-panel-touch-keyboard-fits-and-clears-bottom");
    view.resize(432,960); wizard->setProperty("keyboardVisible",false); wizard->setProperty("step",5); view.grabWindow();
    select(1); invokeText(broker.expectedCredential); select(2); invokeText(broker.expectedCredential);
    check(QMetaObject::invokeMethod(wizard, "createAccount"), "wizard-final-action");
    check(wait([&]{return broker.calls == 3 && controller->property("phase") == "configured";}) && broker.profileExact, "profile-rpc-used");
    QTextStream(stdout) << "{\"architecture\":\"aarch64\",\"qt\":\"" << qVersion() << "\",\"checks\":" << checks << ",\"passed\":true,\"native_panel_checked\":true,\"real_account_attempts\":0,\"real_pam_attempts\":0,\"radio_attempts\":0}" << Qt::endl;
    return 0;
}
#include "arm_ui.moc"
