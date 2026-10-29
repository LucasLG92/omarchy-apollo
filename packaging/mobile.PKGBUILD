# Copy this recipe to PKGBUILD inside a staging copy of this repository.
pkgname=omarchy-apollo-mobile
pkgver=0.1.0
pkgrel=2
pkgdesc='Touch profile and keyboard controls for Omarchy Apollo'
arch=('aarch64')
license=('MIT')
depends=('omarchy-apollo' 'wvkbd-mobintl-apollo')
options=('!strip' '!debug')
package() {
  install -d "$pkgdir/usr/share/omarchy-apollo-mobile"
  cp -a "$startdir/config" "$pkgdir/usr/share/omarchy-apollo-mobile/"
  install -Dm755 "$startdir/platform/omarchy-apollo-keyboard-toggle" "$pkgdir/usr/bin/omarchy-apollo-keyboard-toggle"
  install -Dm644 "$startdir/platform/omarchy-apollo-keyboard.service" "$pkgdir/usr/lib/systemd/user/omarchy-apollo-keyboard.service"
  install -Dm644 "$startdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
