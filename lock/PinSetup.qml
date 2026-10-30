import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
  id: root
  visible: true
  visibility: Window.FullScreen
  title: "Omarchy Apollo · PIN"
  color: "#1a1b26"
  property string first: ""
  property string second: ""
  property bool confirming: false
  readonly property string current: confirming ? second : first
  function clearInput() { first = ""; second = ""; confirming = false }
  function press(value) {
    if (pinSetup.complete) return
    if (value === "←") {
      if (confirming) second = second.slice(0, -1)
      else first = first.slice(0, -1)
    } else if (value === "✓") {
      if (current.length < 6) return
      if (!confirming) confirming = true
      else {
        var ok = pinSetup.enroll(first, second)
        clearInput()
      }
    } else if (current.length < 12) {
      if (confirming) second += value
      else first += value
    }
  }
  ColumnLayout {
    anchors.centerIn: parent
    width: Math.min(360, parent.width - 40)
    spacing: 22
    Text {
      Layout.fillWidth: true
      text: "OMARCHY APOLLO"
      color: "#7aa2f7"
      font.pixelSize: 16
      font.letterSpacing: 2
      horizontalAlignment: Text.AlignHCenter
    }
    Text {
      Layout.fillWidth: true
      text: pinSetup.complete ? "PIN guardado" : (root.confirming ? "Confirma tu PIN" : "Crea tu PIN")
      color: "#c0caf5"
      font.pixelSize: 30
      font.bold: true
      horizontalAlignment: Text.AlignHCenter
    }
    Text {
      Layout.fillWidth: true
      text: "Entre 6 y 12 dígitos.\nIntrodúcelo solo en este móvil."
      color: "#a9b1d6"
      font.pixelSize: 16
      horizontalAlignment: Text.AlignHCenter
    }
    Rectangle {
      Layout.fillWidth: true
      Layout.preferredHeight: 64
      radius: 12
      color: "#24283b"
      border.color: "#7aa2f7"
      Text {
        anchors.centerIn: parent
        text: "●".repeat(root.current.length)
        color: "#c0caf5"
        font.pixelSize: 26
        font.letterSpacing: 6
      }
    }
    Text {
      Layout.fillWidth: true
      text: root.current.length < 6 ? "Mínimo 6 dígitos · faltan " + (6 - root.current.length) : "Pulsa ✓ para continuar"
      color: root.current.length < 6 ? "#a9b1d6" : "#9ece6a"
      horizontalAlignment: Text.AlignHCenter
      font.pixelSize: 15
    }
    GridLayout {
      Layout.fillWidth: true
      columns: 3
      rowSpacing: 10
      columnSpacing: 10
      Repeater {
        model: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "←", "0", "✓"]
        Button {
          required property string modelData
          Layout.fillWidth: true
          Layout.preferredHeight: 68
          enabled: !pinSetup.complete && (modelData !== "✓" || root.current.length >= 6)
          text: modelData
          font.pixelSize: 28
          contentItem: Text {
            text: parent.text
            color: parent.enabled ? "#c0caf5" : "#565f89"
            font: parent.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
          }
          background: Rectangle { radius: 12; color: parent.down ? "#414868" : "#24283b" }
          onClicked: root.press(modelData)
        }
      }
    }
    Text {
      Layout.fillWidth: true
      Layout.preferredHeight: 60
      text: pinSetup.message.length ? pinSetup.message : "La contraseña de administración seguirá siendo la misma."
      color: pinSetup.complete ? "#9ece6a" : "#a9b1d6"
      wrapMode: Text.WordWrap
      horizontalAlignment: Text.AlignHCenter
      font.pixelSize: 15
    }
    Button {
      Layout.alignment: Qt.AlignHCenter
      text: root.confirming ? "Volver a empezar" : "Cancelar"
      enabled: !pinSetup.complete
      onClicked: {
        if (root.confirming) root.clearInput()
        else { root.clearInput(); Qt.quit() }
      }
    }
  }
  onClosing: root.clearInput()
}
