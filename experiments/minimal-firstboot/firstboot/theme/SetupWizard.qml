// SPDX-License-Identifier: MIT
// Credentials remain inside the compiled bridge; only preferences enter JS.
import QtQuick 2.15
import QtQuick.Controls 2.15
Control {
    id: root
    objectName: "firstBootForm"
    required property var controller
    palette.window: "#1a1b26"
    palette.windowText: "#c0caf5"
    palette.text: "#c0caf5"
    palette.buttonText: "#c0caf5"
    palette.button: "#24283b"
    palette.base: "#24283b"
    palette.highlight: "#a8cd76"
    palette.highlightedText: "#1a1b26"
    property int step: 0
    property bool keyboardVisible: false
    property string publicTarget: ""
    property string displayName: ""
    property string hostname: "apollo"
    property string chosenLocale: "es_ES.UTF-8"
    property string timezone: "Europe/Madrid"
    property string keyboardLayout: "es"
    property var selectedApps: []
    readonly property bool formAvailable: ["unowned", "unowned-reserved", "needs-password"].indexOf(controller.phase) >= 0
    readonly property string title: ["Bienvenido a Omarchy", "Tu administrador", "Tu contraseña", "Tu dispositivo", "Elige tus aplicaciones", "Todo preparado"][step]
    readonly property string message: {
        if (controller.errorCode === "INVALID_NAME") return "Usuario: minúsculas, números, _ o -. Empieza por letra o _."
        if (controller.errorCode === "NAME_UNAVAILABLE") return "Ese usuario no está disponible."
        if (controller.errorCode === "INVALID_PASSWORD") return "Usa entre 8 y 128 caracteres. También puedes usar letras."
        if (controller.errorCode === "MISMATCH") return "Las contraseñas no coinciden. Vuelve al paso Contraseña."
        if (controller.errorCode === "LOCALE_UNAVAILABLE") return "El idioma elegido no está preparado en esta imagen."
        if (controller.errorCode === "INVALID_PROFILE") return "Revisa el dispositivo y las preferencias."
        if (controller.errorCode) return "No se pudo completar la configuración. Revisa los datos y vuelve a intentarlo."
        if (controller.phase === "configured") return "Cuenta creada. Ya puedes iniciar sesión con tu contraseña."
        if (controller.phase === "finish-pending") return "La contraseña ya se guardó. Completa la configuración para iniciar sesión."
        if (!formAvailable) return "Comprobando la configuración local…"
        return "Paso " + (step + 1) + " de 6"
    }
    function selectField(index) { publicTarget = ""; controller.selectField(index); keyboardVisible = true; forceActiveFocus() }
    function selectPublic(target) { publicTarget = target; keyboardVisible = true; forceActiveFocus() }
    function insert(value) {
        if (publicTarget === "name") displayName = (displayName + value).slice(0, 80)
        else if (publicTarget === "host") hostname = (hostname + value.toLowerCase()).replace(/[^a-z0-9-]/g, "").slice(0, 63)
        else controller.insertText(value)
    }
    function erase() {
        if (publicTarget === "name") displayName = displayName.slice(0, -1)
        else if (publicTarget === "host") hostname = hostname.slice(0, -1)
        else controller.erase()
    }
    function advance() {
        if (step === 2 && controller.field === 1) { selectField(2); return }
        keyboardVisible = false; publicTarget = ""
        if (step < 5) step++
    }
    function toggleApp(id, enabled) {
        let copy = selectedApps.filter(function(value) { return value !== id })
        if (enabled) copy.push(id)
        selectedApps = copy
    }
    function createAccount() {
        keyboardVisible = false
        controller.setProfile(JSON.stringify({schema: 1, display_name: displayName, hostname: hostname,
            locale: chosenLocale, timezone: timezone, keyboard: keyboardLayout, apps: selectedApps}))
        controller.submit()
    }
    focus: true
    Keys.onPressed: function(event) {
        if (!formAvailable || controller.busy) return
        if (event.key === Qt.Key_Backspace) erase()
        else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) advance()
        else if (event.key === Qt.Key_Escape) keyboardVisible = false
        else if (event.text && !(event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier))) insert(event.text)
        else return
        event.accepted = true
    }
    Image {
        id: logo; source: "logo.png"
        width: Math.min(root.width - 64, 280); height: width * sourceSize.height / Math.max(1, sourceSize.width)
        anchors.top: parent.top; anchors.topMargin: 40; anchors.horizontalCenter: parent.horizontalCenter
        fillMode: Image.PreserveAspectFit; Accessible.name: "Omarchy"
    }
    Flickable {
        id: content
        anchors.top: logo.bottom; anchors.topMargin: 24
        anchors.bottom: navigation.top; anchors.bottomMargin: 12
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(root.width - 40, 440); clip: true
        contentHeight: body.height; boundsBehavior: Flickable.StopAtBounds
        Column {
            id: body; width: content.width; spacing: 12
            Text { text: root.title; color: "#c0caf5"; font.pixelSize: 24; width: parent.width; wrapMode: Text.WordWrap }
            Text { text: root.message; color: "#a9b1d6"; font.pixelSize: 14; width: parent.width; wrapMode: Text.WordWrap }
            Column {
                width: parent.width; spacing: 12; visible: root.formAvailable && root.step === 0
                Text { text: "Idioma del sistema"; color: "#c0caf5" }
                ComboBox { width: parent.width; model: ["Español", "English"]; onActivated: root.chosenLocale = currentIndex === 0 ? "es_ES.UTF-8" : "en_US.UTF-8" }
                Text { text: "Una cuenta local, sin registros externos. Tendrás permisos de administrador. Podrás añadir más aplicaciones desde Aplicaciones."; color: "#a9b1d6"; width: parent.width; wrapMode: Text.WordWrap }
            }
            Column {
                width: parent.width; spacing: 12; visible: root.formAvailable && root.step === 1
                Button { objectName: "ownerField0"; width: parent.width; height: 56; text: controller.username || "Nombre de usuario"; onClicked: root.selectField(0) }
                Button { width: parent.width; height: 56; text: root.displayName || "Tu nombre (opcional)"; onClicked: root.selectPublic("name") }
                Text { text: "El usuario será administrador mediante sudo. No se crea una contraseña de root adicional."; color: "#a9b1d6"; width: parent.width; wrapMode: Text.WordWrap }
            }
            Column {
                width: parent.width; spacing: 12; visible: root.formAvailable && root.step === 2
                Repeater {
                    model: 2
                    Button {
                        required property int index
                        objectName: "ownerField" + (index + 1); width: body.width; height: 58
                        text: index === 0 ? (controller.passwordLength ? "•".repeat(Math.min(controller.passwordLength, 20)) : "Contraseña") : (controller.confirmationLength ? "•".repeat(Math.min(controller.confirmationLength, 20)) : "Repite la contraseña")
                        Accessible.name: index === 0 ? "Contraseña" : "Repite la contraseña"
                        onClicked: root.selectField(index + 1)
                    }
                }
                Text { text: "La misma contraseña desbloquea Omarchy y autoriza sudo. Entre 8 y 128 caracteres; admite letras y símbolos. El PIN de la SIM se gestiona aparte."; color: "#a9b1d6"; width: parent.width; wrapMode: Text.WordWrap }
            }
            Column {
                width: parent.width; spacing: 10; visible: root.formAvailable && root.step === 3
                Button { width: parent.width; height: 52; text: "Dispositivo: " + root.hostname; onClicked: root.selectPublic("host") }
                Text { text: "Zona horaria"; color: "#c0caf5" }
                ComboBox { width: parent.width; model: ["Europe/Madrid", "Atlantic/Canary", "Europe/London", "America/Mexico_City", "America/Bogota", "America/Argentina/Buenos_Aires", "America/New_York", "UTC"]; onActivated: root.timezone = currentText }
                Text { text: "Distribución del teclado"; color: "#c0caf5" }
                ComboBox { width: parent.width; model: ["Español", "Latinoamericano", "English (US)"]; onActivated: root.keyboardLayout = ["es", "latam", "us"][currentIndex] }
            }
            Column {
                width: parent.width; spacing: 4; visible: root.formAvailable && root.step === 4
                Text { text: "La base incluye teléfono, mensajes, contactos, cámara, archivos, terminal, navegador y tienda. Lo siguiente es opcional. Se descargará al entrar, cuando haya Internet."; color: "#a9b1d6"; width: parent.width; wrapMode: Text.WordWrap }
                Repeater {
                    model: [{id: "org.gnome.Calculator", label: "Calculadora"}, {id: "org.gnome.Maps", label: "Mapas"}, {id: "org.gnome.TextEditor", label: "Editor de texto"}, {id: "org.gnome.Fractal", label: "Matrix · Fractal"}, {id: "de.schmidhuberj.Flare", label: "Signal · Flare (no oficial)"}]
                    CheckBox { required property var modelData; width: body.width; text: modelData.label; checked: false; onToggled: root.toggleApp(modelData.id, checked) }
                }
            }
            Text {
                visible: root.formAvailable && root.step === 5; width: parent.width
                color: "#c0caf5"; font.pixelSize: 16; wrapMode: Text.WordWrap
                text: "Administrador: " + controller.username + "\nDispositivo: " + root.hostname + "\nIdioma: " + root.chosenLocale + "\nZona: " + root.timezone + "\nAplicaciones opcionales: " + root.selectedApps.length + "\n\nLa contraseña no se muestra ni se guarda en las preferencias."
            }
            Button { objectName: "retryState"; visible: !root.formAvailable && controller.phase !== "configured"; text: controller.phase === "finish-pending" ? "Completar configuración" : "Comprobar de nuevo"; onClicked: controller.phase === "finish-pending" ? controller.submit() : controller.refresh() }
        }
    }
    Row {
        id: navigation; anchors.horizontalCenter: parent.horizontalCenter
        y: keyboard.visible ? keyboard.y - height - 12 : root.height - height - 48
        width: content.width; height: 48; spacing: 12; visible: root.formAvailable
        Button { width: (parent.width - 12) / 2; height: 48; text: "Atrás"; enabled: root.step > 0 && !controller.busy; onClicked: { root.keyboardVisible = false; root.step-- } }
        Button { objectName: "configureOwner"; width: (parent.width - 12) / 2; height: 48; text: controller.busy ? "Configurando…" : root.step === 5 ? "Crear cuenta" : "Continuar"; enabled: !controller.busy; onClicked: root.step === 5 ? root.createAccount() : root.advance() }
    }
    MobileKeyboard {
        id: keyboard; width: Math.min(root.width, 432); anchors.horizontalCenter: parent.horizontalCenter
        y: root.height - height - 56
        visible: root.keyboardVisible && root.formAvailable; busy: controller.busy; hasText: true; submitLabel: "Continuar"
        onInsertText: function(value) { root.insert(value) }
        onErase: root.erase()
        onSubmit: root.advance()
        onHideKeyboard: { root.keyboardVisible = false; root.forceActiveFocus() }
    }
}
