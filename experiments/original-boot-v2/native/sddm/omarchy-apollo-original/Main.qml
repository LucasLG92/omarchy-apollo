// SPDX-License-Identifier: MIT
// Omarchy original SDDM composition, uniformly scaled for the Apollo screen.
// Original design: David Heinemeier Hansson / omacom/omarchy (MIT).
import QtQuick 2.15

Rectangle {
    id: root
    width: 1080
    height: 2400
    color: "#1a1b26"
    property real uiScale: Math.min(width / 432, height / 960)
    property string currentUser: userModel.lastUser || config.stringValue("User") || "omarchy"
    property bool loginFailed: false
    property bool busy: false
    property bool keyboardVisible: false
    property bool reduceMotion: config.boolValue("ReduceMotion")
    property int sessionIndex: {
        for (var i = 0; i < sessionModel.rowCount(); i++) {
            var name = (sessionModel.data(sessionModel.index(i, 0), Qt.DisplayRole) || "").toString()
            if (name.indexOf("uwsm") !== -1) return i
        }
        return sessionModel.lastIndex
    }
    function insertText(value) {
        if (!busy) password.text += value
    }
    function eraseCharacter() {
        if (!busy) password.text = Array.from(password.text).slice(0, -1).join("")
    }
    function submit() {
        if (busy || password.text.length === 0 || sessionIndex < 0) return
        busy = true
        loginFailed = false
        sddm.login(currentUser, password.text, sessionIndex)
        password.text = ""
    }
    Connections {
        target: sddm
        function onLoginFailed() {
            root.busy = false
            root.loginFailed = true
            password.text = ""
            password.forceActiveFocus()
        }
        function onLoginSucceeded() {
            root.busy = false
            root.loginFailed = false
            password.text = ""
        }
    }
    Item {
        id: canvas
        width: 432
        height: 960
        anchors.centerIn: parent
        scale: root.uiScale
        transformOrigin: Item.Center
        Column {
            id: originalComposition
            objectName: "originalComposition"
            anchors.horizontalCenter: parent.horizontalCenter
            y: Math.floor((root.keyboardVisible ? (canvas.height - keyboard.height) / 2 : canvas.height / 2) - height / 2)
            spacing: 40
            Behavior on y { enabled: !root.reduceMotion; NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
            Image {
                id: logo
                source: "logo.png"
                width: Math.min(sourceSize.width, canvas.width * 0.8)
                height: sourceSize.width > 0 ? Math.round(width * sourceSize.height / sourceSize.width) : 0
                fillMode: Image.PreserveAspectFit
                anchors.horizontalCenter: parent.horizontalCenter
                Accessible.name: "Omarchy"
                Accessible.role: Accessible.Graphic
            }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 15
                Image {
                    source: root.loginFailed ? "lock-failed.png" : "lock.png"
                    width: 34
                    height: 38
                    fillMode: Image.PreserveAspectFit
                    anchors.verticalCenter: parent.verticalCenter
                }
                Item {
                    width: entry.width
                    height: entry.height
                    Image {
                        id: entry
                        source: root.loginFailed ? "entry-failed.png" : "entry.png"
                        anchors.centerIn: parent
                    }
                    Row {
                        anchors.left: parent.left
                        anchors.leftMargin: 20
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 5
                        Repeater {
                            model: Math.min(password.text.length, 21)
                            Image { source: "bullet.png"; width: 7; height: 7 }
                        }
                    }
                    TextInput {
                        id: password
                        objectName: "credentialInput"
                        anchors.fill: parent
                        anchors.leftMargin: 20
                        anchors.rightMargin: 20
                        verticalAlignment: TextInput.AlignVCenter
                        echoMode: TextInput.Password
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 24
                        font.letterSpacing: 5
                        passwordCharacter: "\u2022"
                        color: "transparent"
                        selectionColor: "transparent"
                        selectedTextColor: "transparent"
                        cursorDelegate: Item {}
                        focus: true
                        enabled: !root.busy
                        inputMethodHints: Qt.ImhHiddenText | Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
                        Accessible.name: "Contraseña de acceso a Omarchy"
                        Accessible.description: root.loginFailed ? "No se ha podido acceder. Revisa la credencial." : "Pulsa para abrir el teclado táctil."
                        onTextChanged: root.loginFailed = false
                        Keys.onPressed: function(event) {
                            if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                root.submit()
                                event.accepted = true
                            } else if (event.key === Qt.Key_Escape) {
                                root.keyboardVisible = false
                                event.accepted = true
                            }
                        }
                        TapHandler { onTapped: { root.keyboardVisible = true; password.forceActiveFocus() } }
                    }
                }
            }
        }
        MobileKeyboard {
            id: keyboard
            x: 0
            y: canvas.height - height
            visible: root.keyboardVisible
            busy: root.busy
            hasText: password.text.length > 0
            onInsertText: function(value) { root.insertText(value) }
            onErase: root.eraseCharacter()
            onSubmit: root.submit()
            onHideKeyboard: { root.keyboardVisible = false; password.forceActiveFocus() }
        }
    }
    Component.onCompleted: password.forceActiveFocus()
}
