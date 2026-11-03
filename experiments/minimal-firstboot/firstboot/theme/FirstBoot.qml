// SPDX-License-Identifier: MIT
import QtQuick 2.15
Item {
    id: root
    required property var controller
    SetupWizard {
        width: 432; height: 960; anchors.centerIn: parent
        scale: Math.min(root.width / 432, root.height / 960)
        transformOrigin: Item.Center
        controller: root.controller
    }
}
