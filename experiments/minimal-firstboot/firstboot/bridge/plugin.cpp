// SPDX-License-Identifier: MIT
#include "OwnerSetup.h"
#include <QQmlExtensionPlugin>
class ApolloFirstBootPlugin final : public QQmlExtensionPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlExtensionInterface_iid)
public:
    void registerTypes(const char *uri) override { qmlRegisterType<OwnerSetup>(uri, 1, 0, "OwnerSetup"); }
};
#include "plugin.moc"
