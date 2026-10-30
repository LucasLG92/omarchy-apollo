pkgname=omarchy-apollo-android
pkgver=0.1.0
pkgrel=10
pkgdesc='On-demand Android integration and installer flavor selection for Apollo'
arch=('aarch64')
license=('MIT')
depends=('omarchy-apollo' 'waydroid' 'lxc' 'python-dbus' 'python-gobject' 'gtk4' 'util-linux' 'libnotify' 'xdg-utils' 'polkit' 'zenity')
options=('!strip' '!debug')
package() {
  install -Dm644 "$startdir/platform/var-lib-waydroid.mount" "$pkgdir/usr/lib/systemd/system/var-lib-waydroid.mount"
  install -Dm644 "$startdir/platform/waydroid-apollo-storage.conf" "$pkgdir/usr/lib/systemd/system/waydroid-container.service.d/50-apollo-storage.conf"
  install -Dm755 "$startdir/platform/omarchy-apollo-android" "$pkgdir/usr/bin/omarchy-apollo-android"
  install -Dm644 "$startdir/platform/omarchy-apollo-android.desktop" "$pkgdir/usr/share/applications/omarchy-apollo-android.desktop"
  install -Dm644 "$startdir/platform/omarchy-apollo-apk-install.desktop" "$pkgdir/usr/share/applications/omarchy-apollo-apk-install.desktop"
  install -Dm755 "$startdir/platform/omarchy-setup-apollo-android" "$pkgdir/usr/bin/omarchy-setup-apollo-android"
  install -Dm755 "$startdir/platform/omarchy-apollo-initialize-android" "$pkgdir/usr/lib/omarchy/apollo/initialize-android"
  install -Dm755 "$startdir/platform/omarchy-apollo-select-android" "$pkgdir/usr/bin/omarchy-apollo-select-android"
  install -Dm755 "$startdir/platform/omarchy-apollo-install-android" "$pkgdir/usr/bin/omarchy-apollo-install-android"
  install -Dm644 "$startdir/platform/omarchy-apollo-install-android.desktop" "$pkgdir/usr/share/applications/omarchy-apollo-install-android.desktop"
  install -Dm644 "$startdir/config/install/android-flavors.json" "$pkgdir/usr/share/omarchy-apollo-android/install/android-flavors.json"
  for component in apk-service android-client; do
    install -Dm755 "$startdir/platform/$component" "$pkgdir/usr/lib/omarchy/apollo/$component"
  done
  install -Dm644 "$startdir/platform/omarchy-apollo-apk.service" "$pkgdir/usr/lib/systemd/system/omarchy-apollo-apk.service"
  install -Dm644 "$startdir/platform/org.omarchy.Apollo.Android.service" "$pkgdir/usr/share/dbus-1/system-services/org.omarchy.Apollo.Android.service"
  install -Dm644 "$startdir/platform/org.omarchy.Apollo.Android.conf" "$pkgdir/usr/share/dbus-1/system.d/org.omarchy.Apollo.Android.conf"
  install -Dm644 "$startdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
