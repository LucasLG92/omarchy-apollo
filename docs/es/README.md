# Omarchy Apollo

Omarchy funcionando de forma nativa en el Xiaomi Mi 10T Pro: escritorio Linux, interfaz adaptada al tacto y Android sin Google para instalar APK.

El escritorio ya arranca desde la instalación interna. Tanto Hyprland como Android utilizan la Adreno 650. Se han instalado una barra simplificada y un teclado táctil. La prueba de APK incluye F-Droid con firma verificada y descarga de su catálogo.

Es un port experimental. El PIN táctil todavía está pendiente de implementación y de que el propietario lo configure en el móvil. No se ha validado el uso diario de todas las funciones. Las huellas no permiten aún registrar ni desbloquear; las llamadas, SMS y datos esperan una SIM de pruebas. El cable USB-C directo no dio imagen en la pantalla externa.

El objetivo es conservar el uso normal de Omarchy y añadir lo necesario para manejar el teléfono. La [matriz principal](../../README.md) distingue lo comprobado, lo heredado de la base anterior y lo pendiente. Las [pruebas](../validation.md) incluyen los límites de cada resultado.

Las fuentes anteriores del kernel, servicios y recuperación se conservan en `hardware/apollo-base/`. Sus capturas antiguas de KDE no se presentan como capturas de Omarchy.
