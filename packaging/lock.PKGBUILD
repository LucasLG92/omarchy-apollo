pkgname=omarchy-apollo-lock
pkgver=0.1.0
pkgrel=4
pkgdesc='Trusted touch PIN setup and rate-limited PAM verification for Apollo'
arch=('aarch64')
license=('MIT')
depends=('omarchy-apollo' 'libxcrypt' 'pam' 'qt6-base' 'qt6-declarative' 'qt6-virtualkeyboard')
makedepends=('cmake' 'gcc')
options=('!strip' '!debug')
build() {
  cmake -S "$startdir/lock" -B "$srcdir/build" -DCMAKE_BUILD_TYPE=Release
  cmake --build "$srcdir/build" -j2
}
package() {
  install -Dm4755 "$srcdir/build/verify-pin" "$pkgdir/usr/lib/omarchy/apollo/verify-pin"
  install -Dm755 "$srcdir/build/omarchy-apollo-pin-setup" "$pkgdir/usr/lib/omarchy/apollo/pin-setup"
  install -Dm755 "$startdir/platform/omarchy-setup-apollo-pin" "$pkgdir/usr/bin/omarchy-setup-apollo-pin"
  install -Dm644 "$startdir/lock/omarchy-lock-password" "$pkgdir/usr/share/omarchy-apollo-lock/omarchy-lock-password"
  install -Dm644 "$startdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
