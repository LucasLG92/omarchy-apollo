// SPDX-License-Identifier: MIT
import QtQuick 2.15
import org.apollo.FirstBoot 1.0

Rectangle {
    id: root
    objectName: "firstbootTheme"
    width: 1080; height: 2400; color: "#1a1b26"
    OwnerSetup { id: setup; objectName: "ownerController" }
    Loader {
        anchors.fill: parent
        sourceComponent: setup.phase === "ready" ? normal : initial
    }
    Component { id: normal; NormalLogin {} }
    Component { id: initial; FirstBoot { controller: setup } }
}
