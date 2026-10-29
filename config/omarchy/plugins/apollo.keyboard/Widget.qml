import QtQuick
import Quickshell
import qs.Ui
import qs.Commons as Commons

BarWidget {
  id: root
  moduleName: "apollo.keyboard"
  implicitWidth: 48
  implicitHeight: 48
  Text {
    anchors.centerIn: parent
    text: "⌨"
    font.pixelSize: 24
    color: Commons.Color.foreground
  }
  MouseArea {
    anchors.fill: parent
    onClicked: Quickshell.execDetached(["omarchy-apollo-keyboard-toggle"])
  }
}
