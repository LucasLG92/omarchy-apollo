# Build from the repository root: makepkg
pkgname=omarchy-apollo
pkgver=0.1.0
pkgrel=1
pkgdesc='Experimental native Omarchy integration for Xiaomi Apollo'
arch=('aarch64')
url='https://github.com/LucasLG92/omarchy-apollo'
license=('MIT')
provides=('omarchy' 'omarchy-dev' 'omarchy-settings' 'omarchy-settings-dev' 'omarchy-security-functions')
conflicts=('omarchy' 'omarchy-dev' 'omarchy-settings' 'omarchy-settings-dev')
depends=('omarchy-keyring' 'hyprland' 'quickshell' 'uwsm' 'sddm'
  'xdg-desktop-portal-hyprland' 'wireplumber' 'pipewire' 'gnome-keyring'
  'gum' 'jq' 'git' 'perl' 'fakeroot' 'pacman-contrib' 'ttf-jetbrains-mono-nerd-basic'
  'networkmanager' 'foot' 'xdg-terminal-exec' 'hyprpolkitagent' 'hyprsunset'
  'grim' 'slurp' 'wl-clipboard' 'bluez-tools' 'qt6-virtualkeyboard'
  'qt6-multimedia' 'qt6-svg' 'qt6-5compat' 'qt6-imageformats')
makedepends=('git')
optdepends=('waydroid: Android applications without Google services'
  'chromium: web browser' 'nautilus: file manager')
_commit=573b518be16ec47547d50fe6197bc7f53e982340
_port_root=$startdir
source=("omarchy::git+https://github.com/omacom/omarchy.git#commit=$_commit")
sha256sums=('SKIP')
if [[ -n ${OMARCHY_SRC:-} ]]; then
  source=()
  sha256sums=()
fi

prepare() {
  if [[ -n ${OMARCHY_SRC:-} ]]; then
    [[ $(cat "$OMARCHY_SRC/SOURCE_COMMIT") == "$_commit" ]]
    [[ ! -e $srcdir/omarchy ]]
    cp -a "$OMARCHY_SRC" "$srcdir/omarchy"
  fi
  cd "$srcdir/omarchy"
  for change in "$_port_root"/patches/*.patch; do
    patch -Np1 -i "$change"
  done
}

package() {
  cd "$srcdir/omarchy"
  install -d "$pkgdir/usr/bin" "$pkgdir/usr/share/omarchy/bin"
  for command in bin/*; do
    [[ -f $command ]] || continue
    install -m755 "$command" "$pkgdir/usr/bin/${command##*/}"
    ln -s "/usr/bin/${command##*/}" "$pkgdir/usr/share/omarchy/bin/${command##*/}"
  done
  for tree in config default shell themes applications install migrations; do
    cp -a "$tree" "$pkgdir/usr/share/omarchy/"
  done
  for asset in version logo.txt logo.svg icon.txt icon.png; do
    install -m644 "$asset" "$pkgdir/usr/share/omarchy/$asset"
  done
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/Omarchy-LICENSE"
  install -Dm644 "$_port_root/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
  install -Dm644 default/uwsm/env.d/10-omarchy "$pkgdir/usr/share/uwsm/env.d/10-omarchy"
  install -Dm644 default/wayland-sessions/omarchy.desktop "$pkgdir/usr/share/wayland-sessions/omarchy.desktop"
  install -Dm644 default/fonts/omarchy/omarchy.ttf "$pkgdir/usr/share/fonts/omarchy/omarchy.ttf"
  install -Dm644 default/systemd/user/omarchy-sleep-lock.service "$pkgdir/usr/lib/systemd/user/omarchy-sleep-lock.service"
  install -Dm644 etc/xkb/symbols/omarchy "$pkgdir/etc/xkb/symbols/omarchy"
  install -Dm644 etc/profile.d/omarchy.sh "$pkgdir/etc/profile.d/omarchy.sh"
  install -Dm644 icon.png "$pkgdir/usr/share/icons/hicolor/256x256/apps/omarchy.png"
  install -Dm755 "$_port_root/platform/omarchy-apollo-first-run" "$pkgdir/usr/bin/omarchy-apollo-first-run"
  for operation in provision-prepare provision-commit provision-verify reset-prepare reset-verify reset-commit reset-rollback update-verify update-takeover luks-slots setup-boot setup-system setup-user post-install pre-remove enable-fingerprint disable-fingerprint; do
    install -Dm755 "$_port_root/platform/lifecycle" "$pkgdir/usr/lib/omarchy/apollo/$operation"
  done
  install -d "$pkgdir/usr/share/omarchy-apollo"
  cp -a "$_port_root/config" "$pkgdir/usr/share/omarchy-apollo/"
  printf '%s\n' "$_commit" >"$pkgdir/usr/share/omarchy-apollo/upstream-commit"
}
