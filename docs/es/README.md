# Omarchy Apollo

Omarchy funcionando de forma nativa en el Xiaomi Mi 10T Pro: escritorio Linux, interfaz adaptada al tacto y Android sin Google para instalar APK.

El escritorio ya arranca desde la instalación interna. Tanto Hyprland como Android utilizan la Adreno 650. Se han instalado una barra simplificada y un teclado táctil. La prueba de APK incluye F-Droid con firma verificada y descarga de su catálogo.

Es un port experimental. El código del PIN táctil ha pasado 15 comprobaciones de autenticación en el dispositivo y el teclado numérico ya se dibuja en la pantalla. Falta que el propietario cree el PIN en el propio móvil y se compruebe el desbloqueo real. No se ha validado el uso diario de todas las funciones. Las huellas no permiten aún registrar ni desbloquear; las llamadas, SMS y datos esperan una SIM de pruebas. El cable USB-C directo no dio imagen en la pantalla externa.

El objetivo es conservar el uso normal de Omarchy y añadir lo necesario para manejar el teléfono. La [matriz principal](../../README.md) distingue lo comprobado, lo heredado de la base anterior y lo pendiente. Las [pruebas](../validation.md) incluyen los límites de cada resultado.

La protección del kernel, firmware y cámaras ha pasado 24 pruebas con el gestor de paquetes real en instalaciones desechables. Las aplicaciones normales se pueden instalar, actualizar y quitar en esas pruebas. El actualizador completo para PC se detiene antes de modificar el sistema: falta terminar y validar el proceso específico de actualización y recuperación de Apollo. También se ha corregido la recarga del escritorio durante la sustitución de los archivos del paquete, sin cerrar las aplicaciones.

Las fuentes anteriores del kernel, servicios y recuperación se conservan en `hardware/apollo-base/`. Sus capturas antiguas de KDE no se presentan como capturas de Omarchy.
