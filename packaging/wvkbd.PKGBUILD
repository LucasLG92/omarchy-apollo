pkgname=wvkbd-mobintl-apollo
pkgver=0.20
pkgrel=2
pkgdesc='Mobile international Wayland keyboard for the Apollo touch profile'
arch=('aarch64')
url='https://github.com/jjsullivan5196/wvkbd'
license=('GPL-3.0-or-later' 'BSD-3-Clause')
depends=('cairo' 'pango' 'wayland' 'libxkbcommon' 'systemd-libs')
makedepends=('git' 'wayland-protocols')
provides=('wvkbd' 'wvkbd-mobintl')
conflicts=('wvkbd' 'wvkbd-mobintl')
source=('wvkbd::git+https://github.com/jjsullivan5196/wvkbd.git#commit=6b41504a0cb58fd1163fa44692398fbd61f8905f'
  'hyprland-lock-notify-v1.xml::https://raw.githubusercontent.com/hyprwm/hyprland-protocols/5c2317e086324053d97f5e0aa8a5132dfef5e013/protocols/hyprland-lock-notify-v1.xml'
  "0001-mobile-input-lifecycle.patch::file://$startdir/packaging/wvkbd-apollo/0001-mobile-input-lifecycle.patch")
sha256sums=('SKIP'
  '360589bc58a0a82768b477564f429dc4a8c016ae8311efad12e03f249ac704fc'
  '43b08c22cc0c944b7c93fd458f5e1b130ddc32a1b5e95b424f29b538ffdc4801')
prepare() {
  cd "$srcdir/wvkbd"
  cp "$srcdir/hyprland-lock-notify-v1.xml" proto/
  patch -Np1 -i "$srcdir/0001-mobile-input-lifecycle.patch"
}
build() {
  cd "$srcdir/wvkbd"
  make -j2 wvkbd-mobintl
}
package() {
  cd "$srcdir/wvkbd"
  install -Dm755 wvkbd-mobintl "$pkgdir/usr/bin/wvkbd-mobintl"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
  install -Dm644 "$srcdir/hyprland-lock-notify-v1.xml" "$pkgdir/usr/share/licenses/$pkgname/hyprland-lock-notify-v1.xml"
}
