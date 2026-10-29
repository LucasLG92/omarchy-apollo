# Procedencia y licencias

Este trabajo integra y modifica software existente. No atribuye a este repositorio la creación del port comunitario original de Apollo, del kernel Linux, de sus controladores, de libcamera, Mesa o KDE.

- [Roy Kaandorp / kernel Apollo](https://gitlab.postmarketos.org/royka1/linux), archivo base `apollo-7.1.0-r12`, con hash fijado en el constructor.
- [Paquetes comunitarios Xiaomi Apollo de Roy Kaandorp](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages): base de integración y parches de cámaras, AF por contraste, DSP, módem y audio. Se conservan autores en los parches.
- [Arch Linux ARM](https://archlinuxarm.org/): rootfs y paquetes aarch64.
- [postmarketOS](https://postmarketos.org/) y [bootmac](https://gitlab.postmarketos.org/postmarketOS/bootmac): trabajo previo del dispositivo e integración de direcciones desde el arranque.
- [Linux MSM](https://github.com/linux-msm): QRTR, PD mapper, FastRPC/Hexagon y servicios Qualcomm.
- [libssc de Dylan Van Assche](https://codeberg.org/DylanVanAssche/libssc), [iio-sensor-proxy](https://gitlab.freedesktop.org/hadess/iio-sensor-proxy), [ModemManager](https://gitlab.freedesktop.org/mobile-broadband/ModemManager), [GeoClue](https://gitlab.freedesktop.org/geoclue/geoclue), [libcamera](https://libcamera.org/), [Mesa](https://www.mesa3d.org/) y [KDE](https://kde.org/).

Las revisiones de dependencias y checksums están en cada `PKGBUILD`. Los 25 parches de la base instalada se aplican sobre la base comunitaria; los archivos de referencia WLED no son una segunda serie que deba aplicarse de nuevo. El parche 0024 usa el modo de cargador del DTS SM8250 MTP y el valor `PON_RESTART_REASON_BOOTLOADER` del [kernel de LineageOS fijado](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/3a0fc935fe41b56669466a1ef17420d099c2eeb2/include/linux/input/qpnp-power-on.h). El parche 0025 y sus pruebas del CCF se desarrollaron sobre esa fuente fijada; se probó en UML y se contrastó después en el teléfono. La integración USB sigue la interfaz configfs documentada por Linux. Véase [CANDIDATE-23.md](CANDIDATE-23.md).

La integración QSEE parte del [controlador de Wrobelda](https://github.com/wrobelda/linux/tree/qcom-qseecom-tee) y sus [auxiliares](https://github.com/wrobelda/qsee-supplicant), con revisiones fijadas en los materiales de construcción. No convierte su soporte de otros sensores en registro FPC funcional. Landlock y sus interfaces proceden del kernel Linux; la prueba incluida solo usa archivos sintéticos propios en un proceso hijo.

`LICENSE` contiene GPL-2.0 para las aportaciones nuevas de diagnóstico/instalación que lo indiquen. **No cambia las licencias de terceros.** Las recetas declaran, según componente, GPL/LGPL, MIT, BSD y LicenseRef-proprietary. Los encabezados, autores y licencias originales de archivos y parches tienen prioridad para esas partes. Las fuentes completas de terceros se obtienen desde los orígenes fijados por las recetas, no se incluyen enteras en este árbol.

Los archivos propietarios referenciados por ciertas recetas se han excluido. No se concede aquí permiso para redistribuirlos ni para publicar firmware o calibraciones extraídos de una unidad. Un paquete o imagen binaria requiere una revisión adicional de licencias y de la obligación de entregar sus fuentes correspondientes.

La documentación y los resúmenes nuevos de esta publicación pueden reutilizarse bajo CC-BY-4.0, atribuyendo a este proyecto. Las capturas muestran KDE y las personalizaciones elegidas por el propietario, incluido [WhiteSur KDE](https://github.com/vinceliuice/WhiteSur-kde). No se atribuyen al port el diseño, los iconos o el fondo representados; sus licencias no cambian. Se publican capturas funcionales, no los archivos de esos temas o fondos.
