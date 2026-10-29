# Apollo Linux port

Linux de escritorio **nativo** para **Xiaomi Mi 10T Pro, M2007J3SG (Apollo)**: Arch Linux ARM, KDE Plasma Wayland, kernel comunitario 7.1.0 y paquetes de integración del hardware.

El objetivo es poder usar el móvil como un ordenador y continuar el desarrollo desde el propio dispositivo. Es una **base experimental de pruebas**, con fallos conocidos. No es una edición oficial de CachyOS ni una ROM apta todavía para sustituir un teléfono de uso diario. No habilita automáticamente cualquier sistema operativo.

![KDE Wayland real en el móvil](../media/kde-desktop.png)

![Paquetes y arquitectura reales en Konsole](../media/kde-console.png)

Estas dos capturas se tomaron en el propio móvil durante el arranque temporal de la candidata. Son capturas reales, sin montaje.

![Escritorio de la instalación interna](../media/installed-desktop.png)

La tercera captura muestra el escritorio de la **base instalada r5**, con selector WiFi y teclado accesibles desde el panel. Se revisaron su contenido visible y sus metadatos antes de publicarla.

![Estado de la instalación r5 en Konsole](../media/installed-status.png)

La cuarta captura es una ventana real maximizada en la pantalla del móvil. Muestra la versión y la banda WiFi, sin nombres de redes ni credenciales. El tema y el fondo fueron elegidos por el propietario.

## Qué hay aquí

- `port-source/`: recetas de paquetes, configuración y parches; incluye los 25 parches del kernel instalado, además de los cambios de libcamera, módem, ubicación, vídeo y sensores.
- `port-source/apollo-hardware-tests/`: herramientas de diagnóstico y pruebas en el dispositivo. Sus registros de ejecución son privados y no deben publicarse sin revisar.
- `system/`: integración de teclado, primer inicio, acceso de mantenimiento por USB e instalación persistente experimental.
- [Estado del hardware](STATUS.md), [pruebas realizadas y límites](TESTS.md), [pendientes](ROADMAP.md), [compilación](BUILD.md), [instalación y recuperación](INSTALL.md), [privacidad](PRIVACY.md) y [procedencia y licencias](PROVENANCE.md).

## Estado de esta publicación

Versión instalada: **apollo-linux-test-2026.10.29-r5**, con **linux-apollo 7.1.0-23**. Kernel 23 corrige la adopción de relojes inactivos: desaparecen el fallo del PLL de pantalla y dos avisos de referencias desequilibradas. USB se configura mediante un servicio después de cambiar a la raíz definitiva. Se verificaron el arranque permanente, el paquete y la imagen leída de boot, además de las regresiones descritas en [TESTS](TESTS.md).

Los detalles de [kernel 23 / r5](CANDIDATE-23.md) incluyen las pruebas KUnit, USB y recuperación, la integración necesaria para el initramfs y sus límites. Las imágenes y copias de recuperación permanecen privadas.

En **kernel 23** se repitieron las cuatro cámaras antes y después de reposo, 100 ciclos de control del enfoque antes y 40 después, 24 ciclos de frontal y una reanudación RTC de unos 13 segundos. Las pruebas aisladas de alimentación pausaron temporalmente el observador de cámaras de WirePlumber y lo restauraron; las capturas normales funcionaron como usuario de escritorio. La prueba física de contacto del lector sigue correspondiendo a **kernel 21**. Los resultados históricos conservan su versión original.

La base **ya está instalada en el almacenamiento interno de la unidad de pruebas**, tras autorización expresa para borrar los datos de Android. La revisión actual inicia KDE, teclado, WiFi y servicios de audio; conserva archivos, identidad del sistema y claves de mantenimiento entre reinicios. El propietario confirmó el encendido físico de r5 sin cable; tras reconectarlo se verificaron un arranque nuevo, kernel/paquete/boot y persistencia. Es una base para desarrollar, con los fallos descritos abajo.

El primer arranque permanente falló por el orden de montaje de `/dev/pts` en el initramfs. La corrección está en `system/persistent-init`; se cambió solo boot, sin volver a formatear los datos. Los cambios posteriores se prueban como actualizaciones separadas y no convierten los resultados de kernel 20 en pruebas de otras versiones.

No se distribuyen imágenes de arranque, sistemas de archivos, firmware propietario, calibraciones, NV/EFS ni copias del teléfono. Parte del material de construcción debe obtenerse legalmente del propio dispositivo o de los proyectos originales. Este repositorio de fuentes aún no es un constructor de imágenes completo probado desde cero.

## Resultados principales

| Función | Resultado observado |
| --- | --- |
| KDE, pantalla y táctil | Escritorio Wayland nativo, 1080×2400 a 144 Hz |
| GPU Adreno 650 | Freedreno, OpenGL ES 3.2 y Turnip/Vulkan 1.3 detectados |
| WiFi e Internet | Selector gráfico confirmado por el usuario; detección de ambas bandas y HTTPS verificado a 5 GHz |
| Cámaras | Las cuatro entregan fotogramas; frontal sometida a aperturas repetidas |
| Enfoque | Control del motor y reposo corregidos en las tandas descritas; falta validación óptica |
| GPS | Posiciones reales a través de GeoClue, sin SIM, junto a una ventana cerrada |
| Vídeo | H.264, HEVC y VP9 mediante hardware; Clapper y búsqueda/pausa probados |
| Instalación interna | R5: persistencia entre reinicios y encendido físico sin cable confirmado |
| Audio instalado | PipeWire, compatibilidad PulseAudio y WirePlumber restaurados; volumen bajo control del propietario; rutas pendientes |
| Huellas | Contacto real del dedo detectado; prueba accesible desde el móvil. Registro, comparación y desbloqueo pendientes |
| Telefonía | Módem reconocido; llamadas/datos sin probar porque falta SIM |
| Pantalla externa | Cable USB-C directo probado: sin imagen; DisplayPort anunciado por la pantalla pero inactivo |
| Pantalla del móvil | Escala 225 %, menú compacto, ventanas nuevas maximizadas y controles de tema ampliados |
| Reinicio al cargador | Orden de software, entrada en FASTBOOT y vuelta a Linux probadas en kernel 22 |

Desde el menú del móvil están disponibles **Prueba del lector de huellas**, **Adaptar escritorio al móvil** y **Estado de Apollo Linux**. La primera solicita la contraseña local mediante sudo y solo detecta contacto; no crea una función de desbloqueo.

El trabajo parte del port de Apollo y del software de muchas personas de la comunidad. Los créditos y las licencias originales se conservan: [procedencia](PROVENANCE.md).
