// SPDX-License-Identifier: MIT
#include "OwnerSetup.h"
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusPendingCallWatcher>
#include <QDBusPendingReply>
#include <QRegularExpression>
#include <QSet>
#include <QTimer>
#include <QJsonDocument>
#include <QJsonObject>

namespace {
constexpr auto service = "org.apollo.OwnerProvisioning1";
constexpr auto path = "/org/apollo/OwnerProvisioning1";
QDBusMessage request(const QString &method) {
    return QDBusMessage::createMethodCall(QString::fromLatin1(service), QString::fromLatin1(path),
                                         QString::fromLatin1(service), method);
}
const QSet<QString> phases = {"unowned", "unowned-reserved", "needs-password", "finish-pending", "ready", "needs-admin", "denied", "unavailable"};
const QSet<QString> errors = {"INVALID_PROFILE", "LOCALE_UNAVAILABLE", "PROFILE_APPLY_FAILED", "INVALID_NAME", "INVALID_PASSWORD", "NAME_UNAVAILABLE", "IDENTITY_ALREADY_RESERVED", "PASSWORD_REJECTED", "DENIED", "BUSY", "ALREADY_OWNED", "OWNER_ALREADY_ACTIVE", "OWNER_STATE_CHANGED", "UNAVAILABLE", "FINISH_WITHOUT_NEW_CREDENTIAL"};
}

OwnerSetup::OwnerSetup(QObject *parent) : QObject(parent) { QTimer::singleShot(0, this, &OwnerSetup::refresh); }
OwnerSetup::~OwnerSetup() { discard(m_password); discard(m_confirmation); }
void OwnerSetup::discard(QString &value) {
    // Best effort only: Qt/D-Bus/PAM may retain internal temporary allocations.
    value.fill(QChar(0)); value.clear(); value.squeeze();
}
int OwnerSetup::length(const QString &value) { return value.toUcs4().size(); }
int OwnerSetup::passwordLength() const { return length(m_password); }
int OwnerSetup::confirmationLength() const { return length(m_confirmation); }
bool OwnerSetup::validCredential(const QString &value) {
    const int count = length(value);
    if (count < 8 || count > 128) return false;
    for (QChar c : value) if (c == QChar(0) || c == '\r' || c == '\n') return false;
    return QString::fromUtf8(value.toUtf8()) == value;
}
QString &OwnerSetup::selected() { return m_field == 0 ? m_name : m_field == 1 ? m_password : m_confirmation; }
void OwnerSetup::selectField(int field) {
    if (!m_busy && field >= 0 && field <= 2) { m_field = field; m_error.clear(); emit changed(); }
}
void OwnerSetup::insertText(const QString &value) {
    if (m_busy || value.isEmpty() || value.contains(QChar(0)) || value.contains('\r') || value.contains('\n')) return;
    QString &target = selected();
    // Retain an overflow sentinel (129/33 code points); never accept truncation
    // of an oversized pasted credential as the credential the owner intended.
    const int limit = m_field == 0 ? 33 : 129;
    auto points = target.toUcs4();
    for (auto point : value.toUcs4()) { if (points.size() >= limit) break; points.append(point); }
    target = QString::fromUcs4(points.constData(), points.size());
    m_error.clear(); emit changed();
}
void OwnerSetup::erase() {
    if (m_busy) return;
    auto points = selected().toUcs4();
    if (!points.isEmpty()) points.removeLast();
    selected() = QString::fromUcs4(points.constData(), points.size());
    m_error.clear(); emit changed();
}
void OwnerSetup::advance() { if (m_field < 2) selectField(m_field + 1); else submit(); }
void OwnerSetup::clear() {
    discard(m_password); discard(m_confirmation); m_error.clear(); emit changed();
}
void OwnerSetup::setProfile(const QString &json) {
    if (m_busy) return;
    const auto document = QJsonDocument::fromJson(json.toUtf8());
    if (json.toUtf8().size() > 8192 || !document.isObject()) {
        m_error = "INVALID_PROFILE"; emit changed(); return;
    }
    m_profile = QString::fromUtf8(document.toJson(QJsonDocument::Compact));
}
void OwnerSetup::refresh() {
    if (m_busy) return;
    m_busy = true; emit changed();
    auto *watcher = new QDBusPendingCallWatcher(QDBusConnection::systemBus().asyncCall(request("GetState"), 5000), this);
    connect(watcher, &QDBusPendingCallWatcher::finished, this, [this, watcher] {
        QDBusPendingReply<QString> reply = *watcher;
        m_phase = !reply.isError() && phases.contains(reply.value()) ? reply.value() : QStringLiteral("unavailable");
        if (m_phase != "unowned" && m_phase != "unowned-reserved" && m_phase != "needs-password") {
            discard(m_password); discard(m_confirmation);
        }
        if (m_phase == "finish-pending" || m_phase == "ready") m_error.clear();
        m_busy = false; emit changed(); watcher->deleteLater();
    });
}
void OwnerSetup::submit() {
    if (m_busy) return;
    const bool finishing = m_phase == "finish-pending";
    if (!finishing && m_phase != "unowned" && m_phase != "unowned-reserved" && m_phase != "needs-password") return;
    if (!finishing) {
        static const QRegularExpression namePattern(QStringLiteral("^[a-z_][a-z0-9_-]{0,31}$"));
        if (!namePattern.match(m_name).hasMatch()) { m_error = "INVALID_NAME"; emit changed(); return; }
        if (!validCredential(m_password)) { m_error = "INVALID_PASSWORD"; emit changed(); return; }
        if (m_password != m_confirmation) { m_error = "MISMATCH"; emit changed(); return; }
    }
    auto message = request(m_profile.isEmpty() ? "Configure" : "ConfigureProfile");
    if (m_profile.isEmpty()) message.setArguments({finishing ? QString() : m_name, finishing ? QString() : m_password});
    else message.setArguments({finishing ? QString() : m_name, finishing ? QString() : m_password, finishing ? QString() : m_profile});
    m_busy = true; m_error.clear();
    // Clear both frontend buffers before sending. The bus necessarily retains
    // its bounded serialized message until delivery; never export it as state.
    discard(m_password); discard(m_confirmation); emit changed();
    auto *watcher = new QDBusPendingCallWatcher(QDBusConnection::systemBus().asyncCall(message, 60000), this);
    message.setArguments({});
    connect(watcher, &QDBusPendingCallWatcher::finished, this, [this, watcher] {
        QDBusPendingReply<QString> reply = *watcher;
        m_busy = false;
        if (!reply.isError() && reply.value() == "configured") m_phase = "configured";
        else {
            m_error = !reply.isError() && errors.contains(reply.value()) ? reply.value() : QStringLiteral("NEEDS_ADMIN");
            // A server error may follow successful PAM and precede the final
            // metadata commit. Requery the enum so recovery never asks to set
            // another credential that the backend correctly refuses to reset.
            QTimer::singleShot(0, this, &OwnerSetup::refresh);
        }
        emit changed(); watcher->deleteLater();
    });
}
