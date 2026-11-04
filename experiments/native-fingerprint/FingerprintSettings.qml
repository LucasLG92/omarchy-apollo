import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

ShellRoot {
 id: root
 property string page: "loading"
 property bool configured: false
 property bool busy: false
 property bool verification: false
 property bool matched: false
 property bool finished: false
 property int stages: 0
 property string message: ""
 Process {
  id: client
  property string operation: "list"
  command: ["/usr/bin/python3", "-I", "/usr/lib/apollo/fingerprint/native-fprint-client", operation]
  stdinEnabled: true
  stdout: SplitParser { onRead: function(line) { root.handle(line) } }
  onExited: {
   root.busy = false
   if (!root.finished && root.page !== "intro") {root.page = "error"; root.message = "No se pudo completar la operación."}
  }
 }
 function handle(line) {
  let e
  try {e = JSON.parse(line)} catch (_) {return}
  if (e.event === "fingers") {
   configured = Array.isArray(e.fingers) && e.fingers.length > 0
   if (client.operation === "list") {page = "intro"; finished = true}
  } else if (e.event === "claimed") {page = "working"}
  else if (e.event === "started") {page = "working"}
  else if (e.event === "status") {
   if (e.result === "enroll-stage-passed") stages++
   message = e.result.indexOf("retry") >= 0 || e.result.indexOf("remove") >= 0
    ? "Retira el dedo y vuelve a apoyarlo cambiando un poco la zona de contacto." : ""
  } else if (e.event === "done") {
   finished = true; busy = false; matched = e.matched === true
   page = e.ok ? "done" : "error"
   if (e.result === "enroll-completed") configured = true
   message = e.result === "canceled" ? "Operación cancelada." : e.ok ? "" : "No se ha completado. Puedes volver a intentarlo."
  } else if (e.event === "error") {
   finished = true; busy = false; page = "error"
   message = e.kind === "busy" ? "El lector está ocupado. Espera y vuelve a intentarlo."
    : e.kind === "denied" ? "No se ha autorizado la operación."
    : e.kind === "no-device" ? "El lector no está disponible. Se conserva el acceso con contraseña."
    : "No se ha podido completar la operación."
  }
 }
 function begin(verify) {
  if (client.running) return
  verification = verify; finished = false; busy = true; stages = 0; message = ""; page = "authorizing"
  client.operation = verify ? "verify" : "enroll"; client.running = true
 }
 function cancel() {if (client.running) client.write('{"cmd":"cancel"}\n')}
 Component.onCompleted: {client.running = true}
 FloatingWindow {
  id: window
  title: "Huellas · Omarchy"
  color: "#1a1b26"
  implicitWidth: Math.min(390, Quickshell.screens[0].width - 32)
  implicitHeight: Math.min(540, Quickshell.screens[0].height - 100)
  Flickable {
   anchors.fill: parent; clip: true; contentWidth: width; contentHeight: Math.max(height, form.implicitHeight + 48)
   ColumnLayout {
    id: form
    x: 24; y: 24; width: parent.width - 48; height: Math.max(implicitHeight, window.height - 48); spacing: 16
    Text {text: "OMARCHY"; color: "#9ece6a"; font.family: "CaskaydiaMono Nerd Font"; font.pixelSize: 20; Layout.alignment: Qt.AlignHCenter}
    Item {Layout.fillHeight: true; Layout.maximumHeight: 22}
    Text {text: String.fromCodePoint(0xF0237); color: "#9ece6a"; font.family: "CaskaydiaMono Nerd Font"; font.pixelSize: 60; Layout.alignment: Qt.AlignHCenter}
    Text {
     text: root.page === "intro" ? "Huella dactilar" : root.page === "loading" ? "Comprobando…"
      : root.page === "authorizing" ? "Autoriza en el móvil"
      : root.page === "working" ? "Apoya y retira el dedo"
      : root.page === "done" ? (root.verification ? (root.matched ? "Huella reconocida" : "Huella no reconocida") : "Huella guardada") : "Operación detenida"
     color: "#c0caf5"; font.pixelSize: 21; font.bold: true; wrapMode: Text.WordWrap
     horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true
    }
    Text {
     text: root.message || (root.page === "intro" ? (root.configured ? "Índice derecho configurado. Puedes comprobarlo desde aquí."
       : "Registra el índice derecho para usar el lector lateral. La contraseña seguirá disponible.")
      : root.page === "working" ? (root.verification ? "Apoya el dedo que quieras comprobar, sin pulsar el botón."
       : "Usa el índice derecho. Levántalo entre muestras y cambia ligeramente la zona de contacto.")
      : root.page === "authorizing" ? "Si solicita autorización, introduce tu contraseña sólo en el móvil."
      : root.page === "done" ? "La información biométrica permanece protegida en este dispositivo." : "")
     color: "#a9b1d6"; font.pixelSize: 15; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true
    }
    Text {visible: root.busy && !root.verification && root.stages > 0; text: "Muestras aceptadas: " + root.stages; color: "#9ece6a"; font.pixelSize: 15; Layout.alignment: Qt.AlignHCenter}
    Item {Layout.fillHeight: true}
    Rectangle {
     visible: !root.busy && root.page !== "loading"; color: "#9ece6a"; radius: 8; implicitHeight: 50; Layout.fillWidth: true
     Text {anchors.centerIn: parent; text: root.configured ? "Comprobar huella" : "Registrar índice derecho"; color: "#1a1b26"; font.pixelSize: 16; font.bold: true}
     MouseArea {anchors.fill: parent; onClicked: root.begin(root.configured)}
    }
    Rectangle {
     color: "#292e42"; radius: 8; implicitHeight: 46; Layout.fillWidth: true
     Text {anchors.centerIn: parent; text: root.busy ? "Cancelar" : "Cerrar"; color: "#c0caf5"; font.pixelSize: 15}
     MouseArea {anchors.fill: parent; onClicked: {if (root.busy)root.cancel(); else Quickshell.quit()}}
    }
   }
  }
 }
}
