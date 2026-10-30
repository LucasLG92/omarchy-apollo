# Omarchy Apollo

Omarchy funcionando de forma nativa en el Xiaomi Mi 10T Pro: escritorio Linux, interfaz adaptada al tacto y Android sin Google para instalar APK.

El escritorio ya arranca desde la instalación interna. Tanto Hyprland como Android utilizan la Adreno 650. Se han instalado una barra simplificada y un teclado táctil. El instalador de APK confirma el resultado real de Android y ha superado 31 comprobaciones en el móvil: rechaza archivos inválidos, instala F-Droid con firma verificada y conserva la aplicación y la aceleración gráfica después de detener y volver a arrancar Android.

Android se abre desde el lanzador y se ejecuta bajo demanda, sin Google. La asociación para abrir archivos APK está registrada. Falta comprobar la pulsación desde el gestor de archivos, las notificaciones y la navegación táctil en la pantalla física. La [guía de Android](../android.md) incluye los comandos, las pruebas reproducibles y sus límites.

El audio del sistema Android ya llega en estéreo a Linux: una prueba con `AudioTrack` reprodujo tres segundos y comprobó ambos canales en una salida virtual aislada. No se reprodujo sonido físico ni se captó el micrófono. Falta comprobar contigo el altavoz y los micrófonos; la prueba digital no sustituye esa comprobación.

La aplicación **Pantalla Apollo** añade controles de orientación, giro automático, bloqueo de posición y frecuencia de pantalla. Ha superado 23 comprobaciones en una sesión aislada del móvil, usando el acelerómetro real y el teclado táctil. Se ha comprobado la recuperación ante fallos de guardado y la conservación de los ajustes al recargar o reiniciar el servicio. El teclado reserva menos altura en horizontal. La pantalla física conserva sus ajustes durante la creación del PIN; faltan la prueba de giro en la mano, la precisión táctil y los cambios de frecuencia. La [guía de pantalla](../display.md) describe lo instalado y sus límites.

El teclado nuevo supera 19 comprobaciones con la candidata y otras 19 con el paquete instalado, incluidos 12 ciclos de escritura y ocultación por prueba, bloqueo de sesión y recuperación sin dejar Ctrl pulsado. Se ha corregido un cierre al destruir la ventana de las teclas emergentes. La apertura automática al escribir queda preparada para después de crear el PIN; durante su configuración, el teclado del escritorio sigue oculto. Faltan la escritura con el dedo, el desbloqueo real y la comprobación de otras aplicaciones. La [guía del teclado](../keyboard.md) contiene las pruebas y sus límites.

Las cuatro cámaras ya entregan vídeo a través de PipeWire en Omarchy y tienen nombres distintos: principal, frontal, gran angular y macro. Se ha corregido una retención de contextos gráficos al reabrirlas: la candidata completó 40 aperturas y 1.200 fotogramas, y el paquete instalado superó otras 12 aperturas. Cámara de GNOME está instalada; faltan el permiso y la prueba física de fotos, vídeo y orientación. Los [resultados de cámara](../cameras.md) incluyen el fallo de control, la corrección y las pruebas reproducibles, sin imágenes privadas.

Es un port experimental. El código del PIN táctil ha pasado 15 comprobaciones de autenticación en el dispositivo y el teclado numérico ya se dibuja en la pantalla. Falta que el propietario cree el PIN en el propio móvil y se compruebe el desbloqueo real. No se ha validado el uso diario de todas las funciones. Las huellas no permiten aún registrar ni desbloquear; las llamadas, SMS y datos esperan una SIM de pruebas. El cable USB-C directo no dio imagen en la pantalla externa.

El objetivo es conservar el uso normal de Omarchy y añadir lo necesario para manejar el teléfono. La [matriz principal](../../README.md) distingue lo comprobado, lo heredado de la base anterior y lo pendiente. Las [pruebas](../validation.md) incluyen los límites de cada resultado.

La protección del kernel, firmware y cámaras ha pasado 24 pruebas con el gestor de paquetes real en instalaciones desechables. Las aplicaciones normales se pueden instalar, actualizar y quitar en esas pruebas. El actualizador completo para PC se detiene antes de modificar el sistema: falta terminar y validar el proceso específico de actualización y recuperación de Apollo. También se ha corregido la recarga del escritorio durante la sustitución de los archivos del paquete, sin cerrar las aplicaciones.

Las fuentes anteriores del kernel, servicios y recuperación se conservan en `hardware/apollo-base/`. Sus capturas antiguas de KDE no se presentan como capturas de Omarchy.
