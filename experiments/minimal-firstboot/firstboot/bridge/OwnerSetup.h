// SPDX-License-Identifier: MIT
#pragma once
#include <QObject>
#include <QString>
#include <QtQml/qqml.h>

class OwnerSetup : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString phase READ phase NOTIFY changed)
    Q_PROPERTY(QString username READ username NOTIFY changed)
    Q_PROPERTY(QString errorCode READ errorCode NOTIFY changed)
    Q_PROPERTY(bool busy READ busy NOTIFY changed)
    Q_PROPERTY(int field READ field NOTIFY changed)
    Q_PROPERTY(int passwordLength READ passwordLength NOTIFY changed)
    Q_PROPERTY(int confirmationLength READ confirmationLength NOTIFY changed)
public:
    explicit OwnerSetup(QObject *parent = nullptr);
    ~OwnerSetup() override;
    QString phase() const { return m_phase; }
    QString username() const { return m_name; }
    QString errorCode() const { return m_error; }
    bool busy() const { return m_busy; }
    int field() const { return m_field; }
    int passwordLength() const;
    int confirmationLength() const;
    Q_INVOKABLE void refresh();
    Q_INVOKABLE void selectField(int field);
    Q_INVOKABLE void insertText(const QString &value);
    Q_INVOKABLE void erase();
    Q_INVOKABLE void advance();
    Q_INVOKABLE void submit();
    Q_INVOKABLE void setProfile(const QString &json);
    Q_INVOKABLE void clear();
signals:
    void changed();
private:
    QString m_phase = QStringLiteral("loading"), m_name, m_password, m_confirmation, m_error, m_profile;
    int m_field = 0;
    bool m_busy = false;
    QString &selected();
    static void discard(QString &value);
    static int length(const QString &value);
    static bool validCredential(const QString &value);
};
