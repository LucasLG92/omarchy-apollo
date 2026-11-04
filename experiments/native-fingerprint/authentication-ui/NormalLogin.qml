// SPDX-License-Identifier: MIT
// Omarchy original SDDM composition, uniformly scaled for the Apollo screen.
// Original design: David Heinemeier Hansson / omacom/omarchy (MIT).
import QtQuick 2.15

Rectangle {
    id: root
    objectName: "normalLogin"
    width: 1080
    height: 2400
    color: "#1a1b26"
    property real uiScale: Math.min(width / 432, height / 960)
    property string currentUser: userModel.lastUser || (userModel.rowCount() > 0 ? userModel.data(userModel.index(0, 0), Qt.UserRole + 1).toString() : "")
    property bool loginFailed: false
    property bool busy: false
    readonly property bool fingerprintAvailable: config.boolValue("ApolloFingerprintEnabled")
    property bool fingerprintAttempt: false
    property string fingerprintMessage: "Usar huella"
    property bool keyboardVisible: false
    property bool reduceMotion: config.boolValue("ReduceMotion")
    property bool compositionReady: false
    readonly property bool assetsReady: logo.status === Image.Ready && entry.status === Image.Ready && lockImage.status === Image.Ready
    function settleComposition() {
        if (!compositionReady && assetsReady && width > 0 && height > 0) compositionSettle.restart()
    }
    onWidthChanged: settleComposition()
    onHeightChanged: settleComposition()
    onAssetsReadyChanged: settleComposition()
    Timer {
        id: compositionSettle
        interval: 100
        onTriggered: { root.compositionReady = true; password.forceActiveFocus() }
    }
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
    function submitFingerprint() {
        if (!fingerprintAvailable || !compositionReady || busy || sessionIndex < 0 || !currentUser) return
        password.text = ""
        keyboardVisible = false
        fingerprintAttempt = true
        fingerprintMessage = "Apoya el dedo en el lector lateral"
        busy = true
        loginFailed = false
        // Empty response selects the root-owned PAM fingerprint branch. It
        // never grants a session; SDDM must report successful authentication.
        sddm.login(currentUser, "", sessionIndex)
    }
    Connections {
        target: sddm
        function onLoginFailed() {
            root.busy = false
            if (root.fingerprintAttempt) root.fingerprintMessage = "No reconocida. Reintentar huella"
            root.fingerprintAttempt = false
            root.loginFailed = true
            password.text = ""
            password.forceActiveFocus()
        }
        function onLoginSucceeded() {
            root.busy = false
            root.loginFailed = false
            root.fingerprintAttempt = false
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
            visible: root.compositionReady
            opacity: root.compositionReady ? 1 : 0
            Behavior on opacity {
                enabled: !root.reduceMotion
                NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
            }
            anchors.horizontalCenter: parent.horizontalCenter
            y: Math.floor((root.keyboardVisible ? (canvas.height - keyboard.height) / 2 : canvas.height / 2) - height / 2)
            spacing: 40
            Behavior on y { enabled: root.compositionReady && !root.reduceMotion; NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
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
                    id: lockImage
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
                        enabled: root.compositionReady && !root.busy
                        inputMethodHints: Qt.ImhHiddenText | Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
                        Accessible.name: "ContraseÃ±a de acceso a Omarchy"
                        Accessible.description: root.loginFailed ? "No se ha podido acceder. Revisa la credencial." : "Pulsa para abrir el teclado tÃ¡ctil."
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
            Rectangle {
                objectName: "fingerprintLoginButton"
                visible: root.fingerprintAvailable
                width: 310
                height: visible ? 48 : 0
                radius: 6
                anchors.horizontalCenter: parent.horizontalCenter
                color: "transparent"
                border.width: 1
                border.color: "#a9b665"
                Accessible.name: root.fingerprintMessage
                Accessible.role: Accessible.Button
                Text {
                    anchors.fill: parent
                    anchors.margins: 8
                    text: root.fingerprintMessage
                    color: "#a9b665"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 14
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    wrapMode: Text.Wrap
                }
                TapHandler { enabled: !root.busy; onTapped: root.submitFingerprint() }
            }
        }
        MobileKeyboard {
            id: keyboard
            x: 0
            y: canvas.height - height - 56
            visible: root.keyboardVisible
            busy: root.busy
            hasText: password.text.length > 0
            onInsertText: function(value) { root.insertText(value) }
            onErase: root.eraseCharacter()
            onSubmit: root.submit()
            onHideKeyboard: { root.keyboardVisible = false; password.forceActiveFocus() }
        }
    }
    Component.onCompleted: settleComposition()
}
