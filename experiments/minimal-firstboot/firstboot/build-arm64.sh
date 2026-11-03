#!/usr/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mkdir -p build pkg/usr/lib/qt6/qml/org/apollo/FirstBoot
read -r -a cflags <<< "$(pkg-config --cflags Qt6Core Qt6Gui Qt6DBus Qt6Qml Qt6Quick)"
/usr/lib/qt6/moc "${cflags[@]}" bridge/OwnerSetup.h -o build/moc_OwnerSetup.cpp
/usr/lib/qt6/moc "${cflags[@]}" bridge/plugin.cpp -o build/plugin.moc
read -r -a flags <<< "$(pkg-config --cflags --libs Qt6Core Qt6Gui Qt6DBus Qt6Qml Qt6Quick)"
g++ -std=c++17 -O2 -fPIC -shared -fvisibility=hidden -Wl,-z,relro,-z,now -Ibridge -Ibuild bridge/OwnerSetup.cpp build/moc_OwnerSetup.cpp bridge/plugin.cpp "${flags[@]}" -o pkg/usr/lib/qt6/qml/org/apollo/FirstBoot/libApolloFirstBootPlugin.so
strip --strip-unneeded pkg/usr/lib/qt6/qml/org/apollo/FirstBoot/libApolloFirstBootPlugin.so
printf 'module org.apollo.FirstBoot\nplugin ApolloFirstBootPlugin\n' > pkg/usr/lib/qt6/qml/org/apollo/FirstBoot/qmldir
read -r -a testcflags <<< "$(pkg-config --cflags Qt6Core Qt6Gui Qt6DBus Qt6Qml Qt6Quick Qt6Test)"
/usr/lib/qt6/moc "${testcflags[@]}" tests/arm_ui.cpp -o build/arm_ui.moc
read -r -a testflags <<< "$(pkg-config --cflags --libs Qt6Core Qt6Gui Qt6DBus Qt6Qml Qt6Quick Qt6Test)"
g++ -std=c++17 -O2 -Ibuild tests/arm_ui.cpp "${testflags[@]}" -o build/arm-ui
