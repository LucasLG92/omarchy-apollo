// SPDX-License-Identifier: MIT
import QtQuick
import Quickshell
import Quickshell.Bluetooth
import Quickshell.Io
import Quickshell.Networking
import Quickshell.Services.UPower
import Quickshell.Wayland
import qs.Commons
import qs.Commons as Commons
import "StatusModel.js" as StatusModel

// Phone status bar, a full `bar` option that replaces omarchy.bar.
//
// The phone has no window list, tray or workspaces to show, so this bar only
// reports state: the clock on the left and unread notifications,
// connectivity, do-not-disturb and battery on the right. The middle stays empty for the camera cutout. The
// whole strip is one touch target: a tap or a downward pull opens the quick
// settings sheet.
Item {
  id: root

  // Injected by the host (see shell.qml configureBar).
  property string omarchyPath: Quickshell.env("OMARCHY_PATH")
  property var shell: null
  property var manifest: null
  property var barWidgetRegistry: null
  property var pluginRegistry: null
  property var barConfig: ({})

  // Scalar bar state the host mirrors to other plugins (notifications and the
  // OSD place themselves clear of the bar with these).
  readonly property bool barHidden: false
  readonly property string position: "top"
  readonly property bool vertical: false
  readonly property string fontFamily: Style.font.family
  // Preserve the portrait touch/cutout inset. On the side, keep the same
  // text and icon fonts while reserving only the height their line needs.
  property var screenInfo: Quickshell.screens.length > 0 ? Quickshell.screens[0] : null
  readonly property int portraitBarSize: Math.max(44, Style.bar.sizeHorizontal)
  FontMetrics {
    id: statusFontMetrics
    font.family: root.fontFamily
    font.pixelSize: Math.max(Style.font.title, Style.font.iconLarge, Style.font.body)
  }
  readonly property int compactBarSize: Math.max(32, Math.ceil(statusFontMetrics.height) + 8)
  function barHeightFor(screen) {
    return screen && screen.width > screen.height ? compactBarSize : portraitBarSize
  }
  readonly property int barSize: barHeightFor(screenInfo)

  // Output geometry and layer configure arrive separately during rotation.
  // Finish polish and request one frame after the last geometry notification,
  // including when the bar's contents themselves have not changed.
  component SettledPanel: PanelWindow {
    id: panel
    property int geometryRefreshes: 0
    onWidthChanged: geometryRepaint.restart()
    onHeightChanged: geometryRepaint.restart()
    onVisibleChanged: geometryRepaint.restart()
    Component.onCompleted: geometryRepaint.restart()
    Connections {
      target: panel.screen
      function onGeometryChanged() { geometryRepaint.restart() }
    }
    Timer {
      id: geometryRepaint
      interval: 32
      onTriggered: {
        if (!panel.visible || !panel.updatesEnabled) return
        panel.contentItem.ensurePolished()
        const window = panel.contentItem.Window.window
        if (window) window.update()
        panel.geometryRefreshes++
      }
    }
  }

  readonly property color foreground: Commons.Color.bar.text
  readonly property color background: Commons.Color.bar.background
  readonly property color urgent: Commons.Color.bar.active

  function setting(name, fallback) {
    var value = barConfig ? barConfig[name] : undefined
    return value === undefined || value === null || value === "" ? fallback : value
  }

  readonly property string clockFormat: String(setting("clockFormat", "HH:mm"))
  readonly property bool showBatteryPercent: setting("showBatteryPercent", true) !== false
  readonly property string quickSettingsId: String(setting("quickSettings", "omamobile.quicksettings"))

  // A full bar may read the notification service's do-not-disturb state
  // through the host's narrow proxy.
  readonly property var notifications: shell && typeof shell.firstPartyServiceFor === "function"
    ? shell.firstPartyServiceFor("omarchy.notifications") : null
  readonly property bool doNotDisturb: notifications ? notifications.doNotDisturb === true : false

  // ---------------------------------------------------------------- state

  SystemClock {
    id: clock
    precision: SystemClock.Minutes
  }

  readonly property var networkDevices: Networking.devices ? Networking.devices.values : []
  readonly property var wifiDevice: StatusModel.findDevice(networkDevices, DeviceType.Wifi)
  readonly property var wiredDevice: StatusModel.findDevice(networkDevices, DeviceType.Wired)
  readonly property var wifiNetwork: StatusModel.connectedNetwork(wifiDevice && wifiDevice.networks ? wifiDevice.networks.values : [])
  readonly property string networkKind: {
    if (wiredDevice && wiredDevice.connected) return "ethernet"
    if (wifiNetwork) return "wifi"
    return wifiDevice && !Networking.wifiEnabled ? "off" : "disconnected"
  }
  readonly property string networkIcon: StatusModel.networkIcon(networkKind,
    wifiNetwork ? Math.round((wifiNetwork.signalStrength || 0) * 100) : -1)

  // The mobile network, from ModemManager's API through
  // bin/omamobile-cell-watch (omamobile-mmd serves it on the Pixel 7 Pro).
  // No modem, no icon.
  property var cell: null
  readonly property string cellGlyph: StatusModel.cellGlyph(cell)
  readonly property string cellText: StatusModel.cellText(cell)

  Process {
    id: cellWatch
    command: ["omamobile-cell-watch"]
    running: true
    stdout: SplitParser {
      onRead: function(line) {
        var c = StatusModel.parseCell(line)
        if (c) root.cell = c
      }
    }
    onExited: { root.cell = null; cellRestart.restart() }
  }
  Timer { id: cellRestart; interval: 5000; onTriggered: cellWatch.running = true }

  // A call in progress: a chip with its time beside the clock. omatel's
  // agent through bin/omamobile-call-watch --observe (the call card runs
  // the waking, name-holding copy).
  property string callLine: ""
  property double nowMs: Date.now()
  readonly property string callChip: StatusModel.callChip(callLine, nowMs) || ""

  Process {
    id: callWatch
    command: ["omamobile-call-watch", "--observe"]
    running: true
    stdout: SplitParser { onRead: function(line) { root.callLine = String(line) } }
    onExited: { root.callLine = ""; callRestart.restart() }
  }
  Timer { id: callRestart; interval: 5000; onTriggered: callWatch.running = true }
  Timer {
    interval: 1000
    repeat: true
    running: root.callChip !== ""
    onTriggered: root.nowMs = Date.now()
  }

  // Watch 4.5's store files for changes, but ask the daemon for its count:
  // its in-memory store includes pending closes and its retention/redaction.
  property double seenStamp: 0
  property int unread: 0
  property bool unreadAgain: false
  property double unreadQueryStamp: 0
  readonly property string notificationsStore: Quickshell.env("HOME") + "/.local/state/omarchy/notifications/"
  FileView {
    path: root.notificationsStore + "live.json"
    watchChanges: true
    printErrors: false
    onLoaded: root.countUnread()
    onFileChanged: reload()
  }
  FileView {
    path: root.notificationsStore + "history.json"
    watchChanges: true
    printErrors: false
    onLoaded: root.countUnread()
    onFileChanged: reload()
  }
  function countUnread() {
    if (unreadRead.running) { unreadAgain = true; return }
    unreadQueryStamp = seenStamp
    unreadRead.command = ["qs", "ipc", "-p", Quickshell.shellDir, "call", "notifications", "unread", String(seenStamp)]
    unreadRead.running = true
  }
  Process {
    id: unreadRead
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var count = Number(text.trim())
        if (root.unreadQueryStamp === root.seenStamp && isFinite(count) && count >= 0 && count <= 100)
          root.unread = Math.floor(count)
      }
    }
    onExited: {
      if (root.unreadAgain) { root.unreadAgain = false; Qt.callLater(root.countUnread) }
    }
  }

  function markSeen(value) {
    var stamp = StatusModel.parseStamp(value)
    if (stamp > seenStamp) seenStamp = stamp
    countUnread()
  }

  FileView {
    path: Quickshell.env("HOME") + "/.local/state/omamobile/notifications-seen"
    printErrors: false
    watchChanges: true
    onLoaded: root.markSeen(text())
    onFileChanged: reload()
  }

  readonly property var btAdapter: Bluetooth.defaultAdapter
  readonly property bool bluetoothConnected: {
    var devices = Bluetooth.devices ? Bluetooth.devices.values : []
    for (var i = 0; i < devices.length; i++)
      if (devices[i] && devices[i].connected) return true
    return false
  }

  readonly property var battery: UPower.displayDevice
  readonly property bool hasBattery: !!battery && battery.isPresent === true
  readonly property int batteryPercent: hasBattery ? Math.round(battery.percentage * 100) : -1
  readonly property bool charging: hasBattery && !UPower.onBattery
  readonly property string batteryIcon: StatusModel.batteryIcon(batteryPercent, charging,
    hasBattery && battery.state === UPowerDeviceState.FullyCharged)

  // ---------------------------------------------------------------- host API

  // The host calls these on whatever bar is active. A phone bar hosts no
  // widget panels, so every per-widget route answers "not here".
  function summonBarWidget(id) { return false }
  function hideBarWidget(id) { return false }
  function isBarWidgetOpen(id) { return false }
  function panelWidgetIdAt(section, index) { return "" }
  function debugBarGeometry() { return [{ position: position, size: barSize }] }

  function openQuickSettings() {
    if (shell && typeof shell.summon === "function")
      shell.summon(quickSettingsId, JSON.stringify({ source: "bar" }))
  }

  function toggleQuickSettings() {
    if (shell && typeof shell.toggle === "function")
      shell.toggle(quickSettingsId, JSON.stringify({ source: "bar" }))
  }

  // IPC for scripts and tests: `omarchy-shell omamobile.bar pullDown`. No
  // gesture or key binds it yet (docs/TOUCH-PLAN.md 1.2 and 3.7).
  IpcHandler {
    target: "omamobile.bar"

    function geometry(): string {
      return JSON.stringify({ height: root.barSize, portraitHeight: root.portraitBarSize,
        compactHeight: root.compactBarSize, contentLineHeight: statusFontMetrics.height,
        textFont: Style.font.title, iconFont: Style.font.iconLarge,
        surfaces: Array.from(barWindows.instances).map(function(window) {
          return { width: window.width, height: window.height, visible: window.visible,
            implicitHeight: window.implicitHeight, geometryRefreshes: window.geometryRefreshes,
            updatesEnabled: window.updatesEnabled }
        }) })
    }

    function pullDown(): string {
      root.openQuickSettings()
      return "ok"
    }

    function toggleQuickSettings(): string {
      root.toggleQuickSettings()
      return "ok"
    }

    // Quick settings' shade calls this with the newest notification it has
    // shown; returns how many are still unread.
    function notificationsSeen(stamp: string): string {
      root.markSeen(stamp)
      return String(root.unread)
    }

    function unread(): string {
      return String(root.unread)
    }
  }

  // ---------------------------------------------------------------- surface

  Variants {
    id: barWindows
    model: Quickshell.screens

    SettledPanel {
      id: barWindow

      required property var modelData
      screen: modelData

      anchors { top: true; left: true; right: true }
      implicitHeight: root.barHeightFor(screen)
      exclusionMode: ExclusionMode.Auto
      color: root.background
      WlrLayershell.namespace: "omarchy-bar"
      WlrLayershell.layer: WlrLayer.Top

      // Above the strip's touch area (below), so the call chip takes its
      // own taps; nothing else in here handles touches, so the rest still
      // reaches the pull-down.
      Item {
        z: 1
        anchors.fill: parent
        anchors.leftMargin: Style.spacing.huge
        anchors.rightMargin: Style.spacing.huge

        Text {
          id: clockText
          anchors.left: parent.left
          anchors.verticalCenter: parent.verticalCenter
          textFormat: Text.PlainText
          text: Qt.formatDateTime(clock.date, root.clockFormat)
          color: root.foreground
          font.family: root.fontFamily
          font.pixelSize: Style.font.title
          font.bold: true
        }

        // The call in progress, beside the clock; a tap opens the Phone
        // app's in-call screen (the bar is never shown over the lock).
        Rectangle {
          id: callChipPill
          objectName: "callChip"
          visible: root.callChip !== ""
          z: 2
          anchors.left: clockText.right
          anchors.leftMargin: Style.spacing.lg
          anchors.verticalCenter: parent.verticalCenter
          height: Math.max(chipRow.implicitHeight + Style.spacing.xs * 2, Math.round(barWindow.height * 0.66))
          width: chipRow.implicitWidth + Style.spacing.lg * 2
          radius: height / 2
          color: chipTap.pressed ? Qt.darker("#1e9e53", 1.2) : "#1e9e53"

          Row {
            id: chipRow
            anchors.centerIn: parent
            spacing: Style.spacing.xs
            Text { anchors.verticalCenter: parent.verticalCenter; textFormat: Text.PlainText; text: String.fromCodePoint(0xF03F2); color: "white"; font.family: root.fontFamily; font.pixelSize: Style.font.body }
            Text { anchors.verticalCenter: parent.verticalCenter; textFormat: Text.PlainText; text: root.callChip; color: "white"; font.family: root.fontFamily; font.pixelSize: Style.font.body; font.bold: true }
          }

          // The bar's full current height, rather than just the pill, so a tap
          // just above or below the chip opens the call, not quick settings.
          MouseArea {
            id: chipTap
            anchors.centerIn: parent
            width: parent.width
            height: Math.max(parent.height, barWindow.height)
            onClicked: Quickshell.execDetached(["omaphone", "--in-call"])
          }
        }

        Row {
          id: status
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.spacing.xl

          // Notifications not yet seen in the quick-settings shade: a
          // count in an accent pill. The strip's tap opens the shade.
          Rectangle {
            objectName: "unreadNotifications"
            visible: root.unread > 0
            anchors.verticalCenter: parent.verticalCenter
            height: Math.max(18, Math.ceil(unreadText.implicitHeight) + 4, Math.round(barWindow.height * 0.45))
            width: Math.max(height, unreadText.implicitWidth + Style.spacing.md * 2)
            radius: height / 2
            color: Commons.Color.accent

            Text {
              id: unreadText
              anchors.centerIn: parent
              textFormat: Text.PlainText
              text: String(root.unread)
              color: root.background
              font.family: root.fontFamily
              font.pixelSize: Style.font.body
              font.bold: true
            }
          }

          StatusGlyph {
            visible: root.doNotDisturb
            text: "󰂛"
          }

          StatusGlyph {
            visible: !!root.btAdapter && root.btAdapter.enabled
            text: root.bluetoothConnected ? "󰂱" : "󰂯"
          }

          Row {
            visible: root.cellGlyph !== ""
            spacing: Style.spacing.xs
            anchors.verticalCenter: parent.verticalCenter
            opacity: root.cell && root.cell.state === "searching" ? 0.55 : 1

            StatusGlyph { text: root.cellGlyph }
            Text {
              visible: text !== ""
              anchors.verticalCenter: parent.verticalCenter
              textFormat: Text.PlainText
              text: root.cellText
              color: root.foreground
              font.family: root.fontFamily
              font.pixelSize: Style.font.body
              font.bold: true
            }
          }

          StatusGlyph {
            visible: root.networkIcon !== ""
            text: root.networkIcon
            opacity: root.networkKind === "off" || root.networkKind === "disconnected" ? 0.55 : 1
          }

          Row {
            visible: root.hasBattery
            spacing: Style.spacing.xs
            anchors.verticalCenter: parent.verticalCenter

            StatusGlyph {
              text: root.batteryIcon
              color: root.batteryPercent >= 0 && root.batteryPercent <= 10 && !root.charging ? root.urgent : root.foreground
            }

            Text {
              visible: root.showBatteryPercent
              anchors.verticalCenter: parent.verticalCenter
              textFormat: Text.PlainText
              text: root.batteryPercent + "%"
              color: root.foreground
              font.family: root.fontFamily
              font.pixelSize: Style.font.body
            }
          }
        }
      }

      // The whole strip is the touch target. A downward pull past a small
      // threshold opens the sheet; a tap toggles it.
      MouseArea {
        id: touch
        anchors.fill: parent
        property real pressY: 0
        property bool pulled: false
        readonly property real pullThreshold: Style.space(14)

        onPressed: function(mouse) { pressY = mouse.y; pulled = false }
        onPositionChanged: function(mouse) {
          if (!pulled && mouse.y - pressY > pullThreshold) {
            pulled = true
            root.openQuickSettings()
          }
        }
        onClicked: if (!pulled) root.toggleQuickSettings()
      }
    }
  }

  component StatusGlyph: Text {
    anchors.verticalCenter: parent ? parent.verticalCenter : undefined
    textFormat: Text.PlainText
    color: root.foreground
    font.family: root.fontFamily
    font.pixelSize: Style.font.iconLarge
  }
}
