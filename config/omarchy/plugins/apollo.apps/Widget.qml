import QtQuick
import Quickshell
import qs.Ui

BarWidget {
  id: root
  moduleName: "apollo.apps"
  implicitWidth: 48
  implicitHeight: barSize

  BarIconButton {
    anchors.fill: parent
    bar: root.bar
    fixedWidth: 48
    text: "\udb80\udc3b"
    tooltipText: "Aplicaciones"
    Accessible.role: Accessible.Button
    Accessible.name: "Abrir aplicaciones"
    onPressed: function(button) {
      if (button === Qt.LeftButton)
        Quickshell.execDetached(["omarchy-shell", "omarchy.dock", "apps"])
    }
  }
}
