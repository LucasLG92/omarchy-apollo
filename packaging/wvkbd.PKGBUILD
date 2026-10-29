pkgname=wvkbd-mobintl-apollo
pkgver=0.20
pkgrel=1
pkgdesc='Mobile international Wayland keyboard for the Apollo touch profile'
arch=('aarch64')
url='https://github.com/jjsullivan5196/wvkbd'
license=('GPL-3.0-or-later')
depends=('cairo' 'pango' 'wayland' 'libxkbcommon')
makedepends=('git' 'wayland-protocols')
provides=('wvkbd' 'wvkbd-mobintl')
conflicts=('wvkbd' 'wvkbd-mobintl')
source=('wvkbd::git+https://github.com/jjsullivan5196/wvkbd.git#commit=6b41504a0cb58fd1163fa44692398fbd61f8905f')
sha256sums=('SKIP')
build() {
  cd "$srcdir/wvkbd"
  make -j2 wvkbd-mobintl
}
package() {
  cd "$srcdir/wvkbd"
  install -Dm755 wvkbd-mobintl "$pkgdir/usr/bin/wvkbd-mobintl"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
