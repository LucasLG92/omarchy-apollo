# Fuentes y construcción

Este repositorio conserva las recetas y modificaciones de la unidad probada. La imagen de desarrollo se construyó con un entorno Linux anfitrión, compilación cruzada del kernel con LLVM y un rootfs Arch Linux ARM aarch64 ejecutado mediante QEMU/binfmt para empaquetar. **Todavía falta repetir una construcción completa desde un checkout limpio.** No se anuncia una imagen reproducible bit a bit.

## Kernel

`port-source/linux-apollo/build-kernel.sh` fija el archivo original `apollo-7.1.0-r12` y su SHA512, aplica los parches 0001–0025 con comprobaciones, usa la configuración contigua y produce Image.gz, DTB y módulos. La receta actual corresponde al kernel 23 instalado en r5. El parche 0025 y su validación nativa están descritos en [CANDIDATE-23.md](CANDIDATE-23.md). Habilita los backends Zstd usados por SquashFS/zram y Landlock; sus dependencias de seguridad se seleccionan mediante Kconfig. Necesita LLVM/Clang, lld, make, utilidades del kernel, Python, curl, tar y patch.

Variables públicas:

```sh
export APOLLO_REPO="$PWD"
export APOLLO_BUILD="$PWD/build/kernel"
export APOLLO_REFERENCE="/ruta/privada/referencias"
bash port-source/linux-apollo/build-kernel.sh
```

La referencia privada esperada incluye `firmware-xiaomi-apollo/firmware-xiaomi-apollo-1.1.tar.gz`, cotejada por SHA512 en el script. Se usa para las entradas `CONFIG_EXTRA_FIRMWARE`. No está en este repositorio. Su procedencia y permiso de redistribución deben comprobarse por separado; no sustituirla por calibración de otro teléfono.

`PKGBUILD` consume un archivo local `apollo-kernel-assets-7.1.0-23.tar.xz` generado a partir del resultado, con `assets/boot/apollo/{Image.gz,sm8250-xiaomi-apollo.dtb,config}`, `assets/lib/modules/7.1.0/` y `assets/COPYING`. Quitar enlaces `build`/`source` del árbol instalado y actualizar el checksum de la receta al archivo construido. El checksum conservado corresponde a la compilación privada comprobada, no a cualquier reconstrucción.

Los archivos `wled-upstream-*.patch` son referencias de procedencia. La serie aplicada por el constructor es la serie numerada 0001–0025; no aplicar además las referencias sobre ella.

## Paquetes aarch64

Cada carpeta de `port-source` contiene un `PKGBUILD`. Usar un entorno de construcción aarch64, como usuario sin privilegios y con las dependencias indicadas por la receta. Revisar fuentes/checksums antes de `makepkg`. Varias recetas requieren archivos locales ausentes de forma deliberada:

| Receta | Entrada local excluida |
| --- | --- |
| linux-apollo | Activos compilados del kernel |
| apollo-board-data | Bundle de firmware/calibración de voz de procedencia original |
| apollo-dsp | Activos DSP/sensores originales |
| apollo-modem | Firmware SDX55; nunca incluir EFS de una unidad |

Las dependencias QRTR, PD mapper, libssc, proxy de sensores, ModemManager y libcamera mantienen sus versiones/revisiones y checksums en las recetas. Instalar primero las dependencias de cada `PKGBUILD`. Los cambios de los paquetes de cámara y vídeo son distintos de los del kernel.

Para la base de escritorio se usaron paquetes oficiales de Arch Linux ARM: KDE Plasma/SDDM, Konsole, Dolphin, Firefox, Mesa/Turnip, NetworkManager, OpenSSH, sudo y herramientas de construcción. La candidata añade plasma-keyboard y kdialog. No instalar kernel-aarch64 sobre linux-apollo ni confundir una actualización de paquetes con actualizar la imagen de arranque del teléfono.

## Pruebas y rootfs

Los scripts de hardware son herramientas de desarrollo, no un instalador automático. Los arneses del host conservan la estructura histórica `work/` y `outputs/arch-apollo/`: requieren preparar un directorio privado de trabajo, copias de recuperación, claves propias y herramientas Android. `APOLLO_SERIAL`, `APOLLO_PLATFORM_TOOLS` y `APOLLO_TEST_PASSWORD_FILE` sustituyen los valores de la unidad original. No se suministra una contraseña compartida. Algunas fases WiFi requieren además un proveedor local de perfil privado; no está incluido.

Antes de reutilizar un arnés, revisar sus rutas y dependencias auxiliares. Los scripts se han trasladado y parametrizado para publicación; esa variante pública aún no ha completado una ejecución de principio a fin. Los resultados de hardware documentados proceden de la variante privada ensayada, no de CI.

`system/persistent-init` monta una base SquashFS local con overlay ext4 persistente. El arranque interno y la persistencia de r5 están probados en la unidad; USB usa un servicio posterior al cambio de raíz. **Instalar y habilitar primero su integración USB**, según [CANDIDATE-23.md](CANDIDATE-23.md). Construir el initramfs con las utilidades y controladores necesarios, el checksum de **la propia** base en `/etc/apollo-live.sha256` y el auxiliar de reinicio de procedencia conocida. La imagen Android de arranque usa cabecera v2, página 4096 y DTB de Apollo. No usar un DTB de otro modelo.

Los controles gráficos de red y pantalla requieren `plasma-nm` y `kscreen`; la instalación de r4 añadió sus dependencias desde paquetes oficiales con firma verificada. `system/apollo-mobile-display.py` se ejecuta como usuario de escritorio, guarda una copia privada de su configuración y aplica el perfil de pantalla; `apollo-mobile-panels.js` usa la API de Plasma. La modificación de controles WhiteSur se limita a una copia local ya instalada por el propietario: el tema y su fondo no se distribuyen aquí.

La prueba local de huella requiere compilar `apollo-fpc-info.c` y los auxiliares QSEE fijados, instalar el overlay de estado y aprovisionar el firmware firmado de **la propia unidad** de forma privada. El lanzador no contiene firmware, credenciales ni una excepción nueva de sudo. Solo comprueba contacto.

La base publicada es código y documentación. No contiene el rootfs ensayado, claves, perfiles de conexión ni firmware. Probar primero con `fastboot boot` y preparar recuperación antes de modificar almacenamiento.
