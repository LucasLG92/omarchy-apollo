// SPDX-License-Identifier: MIT
// Self-contained touch input. No credential copies, network, clipboard or IME.
import QtQuick 2.15
import QtQuick.Controls 2.15
Rectangle {
    id: root
    objectName: "touchKeyboard"
    width: 432
    height: 304
    color: "#1a1b26"
    property bool busy: false
    property bool hasText: false
    signal insertText(string value)
    signal erase()
    signal submit()
    signal hideKeyboard()
    property bool keyboardShift: false
    property bool keyboardSymbols: false
    property bool keyboardSymbolPage: false
    property bool keyboardAccents: false
    readonly property var keyboardRows: keyboardAccents ? [
        ["á", "é", "í", "ó", "ú", "à", "è", "ì", "ò", "ù"],
        ["ä", "ë", "ï", "ö", "ü", "â", "ê", "î", "ô", "û"],
        ["shift", "ñ", "ç", "ã", "õ", "æ", "œ", "erase"]
    ] : keyboardSymbols ? (keyboardSymbolPage ? [
        ["[", "]", "{", "}", "#", "%", "^", "*", "+", "="],
        ["_", "\\", "|", "~", "<", ">", "$", "€", "`", "&"],
        ["shift", ";", ":", "-", "/", "(", ")", "erase"]
    ] : [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["@", "#", "€", "_", "&", "-", "+", "(", ")", "/"],
        ["shift", ".", ",", "?", "!", "'", "\"", "erase"]
    ]) : [
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ñ"],
        ["shift", "z", "x", "c", "v", "b", "n", "m", "erase"]
    ]
    function keyboardLabel(value) {
        if (value === "shift") return keyboardSymbols && !keyboardAccents ? "#+=" : "⇧"
        if (value === "erase") return "⌫"
        if (value === "enter") return "→"
        if (value === "space") return "Espacio"
        if (value === "symbols") return keyboardSymbols ? "ABC" : "123"
        if (value === "accents") return keyboardAccents ? "ABC" : "áéí"
        return keyboardShift && (!keyboardSymbols || keyboardAccents) ? value.toUpperCase() : value
    }
    function pressPasswordKey(value) {
        if (busy) return
        if (value === "shift") {
            if (keyboardSymbols && !keyboardAccents) keyboardSymbolPage = !keyboardSymbolPage
            else keyboardShift = !keyboardShift
        } else if (value === "erase") root.erase()
        else if (value === "enter") root.submit()
        else if (value === "symbols") {
            keyboardSymbols = !keyboardSymbols
            keyboardAccents = false
            keyboardShift = false
        } else if (value === "accents") {
            keyboardAccents = !keyboardAccents
            keyboardSymbols = false
            keyboardShift = false
        } else {
            root.insertText(value === "space" ? " " : keyboardLabel(value))
            if (!keyboardSymbols || keyboardAccents) keyboardShift = false
        }
    }
    component TouchKey: Button {
        id: touchKey
        property string value: ""
        text: root.keyboardLabel(value)
        height: 52
        focusPolicy: Qt.TabFocus
        enabled: !root.busy && (value !== "enter" || root.hasText)
        autoRepeat: value === "erase"
        autoRepeatDelay: 400
        autoRepeatInterval: 100
        Accessible.name: value === "erase" ? "Borrar último carácter" : value === "enter" ? "Iniciar sesión" : value === "shift" ? "Mayúsculas o segunda página de símbolos" : value === "space" ? "Espacio" : value === "symbols" ? "Letras o números y símbolos" : value === "accents" ? "Letras con acento" : text
        background: Rectangle {
            radius: 8
            color: touchKey.down ? "#414868" : touchKey.value === "enter" ? "#a8cd76" : touchKey.value === "shift" && (root.keyboardShift || root.keyboardSymbolPage) ? "#414868" : "#24283b"
            opacity: touchKey.enabled ? 1 : 0.4
            border.width: touchKey.activeFocus ? 1 : 0
            border.color: "#a8cd76"
        }
        contentItem: Text {
            text: touchKey.text
            color: touchKey.value === "enter" ? "#1a1b26" : "#c0caf5"
            font.pixelSize: touchKey.value === "space" ? 13 : touchKey.value === "symbols" || touchKey.value === "accents" ? 16 : 21
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        onClicked: root.pressPasswordKey(value)
    }

    Rectangle { x: 0; y: 0; width: parent.width; height: 1; color: "#292e42" }
    Button {
        x: parent.width - 94; y: 2; width: 88; height: 44
        text: "Ocultar"; flat: true; enabled: !root.busy
        Accessible.name: "Ocultar teclado táctil"
        onClicked: root.hideKeyboard()
        contentItem: Text { text: parent.text; color: "#a9b1d6"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { color: "transparent"; border.color: parent.activeFocus ? "#a8cd76" : "transparent"; radius: 4 }
    }
        Column {
            x: 8
            y: 48
            width: 416
            spacing: 8
            Repeater {
                model: root.keyboardRows
                Row {
                    id: keyboardRow
                    required property var modelData
                    property var characters: modelData
                    spacing: 4
                    Repeater {
                        model: keyboardRow.characters
                        TouchKey {
                            required property string modelData
                            value: modelData
                            width: (416 - 4 * (keyboardRow.characters.length - 1)) / keyboardRow.characters.length
                        }
                    }
                }
            }
            Row {
                spacing: 6
                TouchKey { width: 64; value: "symbols" }
                TouchKey { width: 52; value: "accents" }
                TouchKey { width: 218; value: "space" }
                TouchKey { width: 64; value: "enter" }
            }
        }
}
