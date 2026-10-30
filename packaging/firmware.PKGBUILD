# Local image-build input only. Proprietary archives are not stored in the repo.
pkgname=apollo-device-firmware
pkgver=1.0
pkgrel=2
pkgdesc='Xiaomi Apollo model firmware for local device image builds'
arch=('any')
url='https://github.com/royka1/Xiaomi-Apollo-pmOS-packages'
license=('LicenseRef-proprietary')
depends=('linux-firmware-qcom')
options=('!strip' '!debug')
source=(
  "firmware-xiaomi-apollo-1.1.tar.gz::file://$startdir/private-inputs/firmware-xiaomi-apollo-1.1.tar.gz"
  "apollo-dsp-fw-1.0.tar.gz::file://$startdir/private-inputs/apollo-dsp-fw-1.0.tar.gz")
sha512sums=(
  'c484de15c12a776735a152efadbf9182bbd6ba3940a6672d38d441627bc07d2ead4b816ef63d5b0aad4ee3de09f1c5dc176a38a7d85aaf6f379884a527680722'
  '8c00a497f5d7a0d708109dd311505f3807b6cf45ad143f8f7fcf76c07a1a5c4d1e607eb4afd3f29b98e0d0ba8c5612c35c0d17c3bf4bf35f4ea7fa6a508f8874')
package() {
  while IFS= read -r name; do
    [[ -n $name && $name != \#* ]] || continue
    # Linux searches firmware/updates before the generic firmware directory.
    # Keep the tested model variants without taking ownership of files in
    # linux-firmware-qcom or linux-firmware-cirrus.
    case "$name" in
      qcom/a650_gmu.bin|qcom/a650_sqe.fw|cirrus/cs35l41-dsp1-spk-prot.bin|cirrus/cs35l41-dsp1-spk-prot.wmfw)
        install -Dm644 "$srcdir/$name" "$pkgdir/usr/lib/firmware/updates/$name" ;;
      *) install -Dm644 "$srcdir/$name" "$pkgdir/usr/lib/firmware/$name" ;;
    esac
  done < "$startdir/packaging/firmware-model/files.txt"
  install -d "$pkgdir/usr/lib/firmware"
  cp -a --no-preserve=ownership "$srcdir/sm8250" "$pkgdir/usr/lib/firmware/"
  # Device-specific modem identity is extracted privately into RAM at runtime.
  # It is never an input to this firmware package or the public source tree.
  ! find "$pkgdir" -type f \( -name 'efs1.bin' -o -name 'efs2.bin' -o -name 'efs3.bin' -o -name 'modemst1' -o -name 'modemst2' \) -print | grep .
}
