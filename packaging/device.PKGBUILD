# Build in a staging copy of this repository. No credentials are packaged.
pkgname=omarchy-apollo-device
pkgver=0.1.0
pkgrel=6
pkgdesc='Clean-image device services and initial owner setup for Omarchy Apollo'
arch=('aarch64')
license=('MIT' 'GPL-2.0-only')
depends=('omarchy-apollo-mobile>=0.1.0-10' 'omarchy-apollo-lock>=0.1.0-3'
  'python' 'python-gobject' 'gtk4' 'systemd' 'networkmanager' 'openssh' 'sudo' 'zenity')
options=('!strip' '!debug')
package() {
  local files="$startdir/hardware/apollo-base/system"
  install -Dm755 "$files/apollo-usb-gadget.py" "$pkgdir/usr/local/sbin/apollo-usb-gadget"
  install -Dm644 "$files/apollo-usb-gadget.service" "$pkgdir/usr/lib/systemd/system/apollo-usb-gadget.service"
  install -Dm644 "$files/70-apollo-usb-gadget.rules" "$pkgdir/usr/lib/udev/rules.d/70-apollo-usb-gadget.rules"
  install -Dm644 "$files/20-apollo-usb.network" "$pkgdir/usr/lib/systemd/network/20-apollo-usb.network"
  install -Dm644 "$files/20-apollo-usb-unmanaged.conf" "$pkgdir/usr/lib/NetworkManager/conf.d/20-apollo-usb-unmanaged.conf"
  install -Dm644 "$files/60-apollo-usb-ssh.conf" "$pkgdir/etc/ssh/sshd_config.d/60-apollo-usb-ssh.conf"
  install -Dm644 "$files/30-apollo-sshd-usb-retry.conf" "$pkgdir/usr/lib/systemd/system/sshd.service.d/30-apollo-usb-retry.conf"
  for component in firstboot-password firstboot-pin password-dialog owner-pin-setup pin-ready-lock enable-pin-administration; do
    install -Dm755 "$startdir/platform/omarchy-apollo-$component" "$pkgdir/usr/lib/omarchy/apollo/$component"
  done
  install -Dm644 "$startdir/platform/omarchy-apollo-owner-pin-setup.service" "$pkgdir/usr/lib/systemd/system/omarchy-apollo-owner-pin-setup.service"
  install -Dm644 "$startdir/platform/omarchy-apollo-pin-ready-lock.service" "$pkgdir/usr/lib/systemd/system/omarchy-apollo-pin-ready-lock.service"
  install -Dm644 "$startdir/platform/omarchy-apollo-owner-setup.service" "$pkgdir/usr/lib/systemd/user/omarchy-apollo-owner-setup.service"
  install -Dm755 "$startdir/platform/omarchy-apollo-setup" "$pkgdir/usr/bin/omarchy-apollo-setup"
  install -Dm644 "$startdir/platform/omarchy-apollo-setup.desktop" "$pkgdir/usr/share/applications/omarchy-apollo-setup.desktop"
  install -Dm755 "$startdir/platform/omarchy-apollo-clock" "$pkgdir/usr/lib/omarchy/apollo/clock"
  for unit in clock-restore.service clock-save.service clock-save.timer; do
    install -Dm644 "$startdir/platform/omarchy-apollo-$unit" "$pkgdir/usr/lib/systemd/system/omarchy-apollo-$unit"
  done
  install -Dm644 "$startdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
