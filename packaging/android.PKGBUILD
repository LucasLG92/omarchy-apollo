pkgname=omarchy-apollo-android
pkgver=0.1.0
pkgrel=1
pkgdesc='On-demand Google-free Android integration for Apollo'
arch=('aarch64')
license=('MIT')
depends=('omarchy-apollo' 'waydroid' 'lxc')
options=('!strip' '!debug')
package() {
  install -Dm644 "$startdir/platform/var-lib-waydroid.mount" "$pkgdir/usr/lib/systemd/system/var-lib-waydroid.mount"
  install -Dm644 "$startdir/platform/waydroid-apollo-storage.conf" "$pkgdir/usr/lib/systemd/system/waydroid-container.service.d/50-apollo-storage.conf"
  install -Dm755 "$startdir/platform/omarchy-apollo-android" "$pkgdir/usr/bin/omarchy-apollo-android"
  install -Dm644 "$startdir/platform/omarchy-apollo-android.desktop" "$pkgdir/usr/share/applications/omarchy-apollo-android.desktop"
  install -Dm644 "$startdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
