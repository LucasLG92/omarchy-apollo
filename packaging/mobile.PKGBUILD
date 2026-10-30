# Copy this recipe to PKGBUILD inside a staging copy of this repository.
pkgname=omarchy-apollo-mobile
pkgver=0.1.0
pkgrel=6
pkgdesc='Touch profile, keyboard controls and native camera for Omarchy Apollo'
arch=('aarch64')
license=('MIT')
depends=('omarchy-apollo' 'wvkbd-mobintl-apollo' 'libcamera-apollo>=0.7.2-3' 'snapshot' 'gst-plugin-pipewire')
options=('!strip' '!debug')
package() {
  install -d "$pkgdir/usr/share/omarchy-apollo-mobile"
  cp -a "$startdir/config" "$pkgdir/usr/share/omarchy-apollo-mobile/"
  install -Dm755 "$startdir/platform/omarchy-apollo-keyboard-toggle" "$pkgdir/usr/bin/omarchy-apollo-keyboard-toggle"
  install -Dm644 "$startdir/platform/omarchy-apollo-keyboard.service" "$pkgdir/usr/lib/systemd/user/omarchy-apollo-keyboard.service"
  install -Dm644 "$startdir/config/wireplumber/90-omarchy-apollo-cameras.conf" "$pkgdir/usr/share/wireplumber/wireplumber.conf.d/90-omarchy-apollo-cameras.conf"
  install -Dm644 "$startdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
