# Omarchy Apollo

**Omarchy nativo en un Xiaomi, adaptado para usarlo como móvil.** El proyecto desarrolla aquí su integración táctil, conservando el escritorio y las aplicaciones normales de Omarchy. Android es opcional para instalar APK, con elección sin Google o con Google Play y servicios.

La instalación limpia ya es permanente. El propietario ha apagado el teléfono, desconectado el PC, arrancado con el botón y desbloqueado con el PIN. La base procede de Arch Linux ARM firmado y Omarchy, sin copiar el sistema, la carpeta personal, contraseñas, redes guardadas ni datos Android anteriores. No contiene KDE/Plasma ni CachyOS.

El PIN numérico se crea y escribe únicamente en el móvil. Sirve para bloquear y, por elección del propietario, para autorizar cambios del sistema. Se ha confirmado el desbloqueo, el aviso numérico de autorización y el botón lateral: apaga sin el destello del teclado y pide el PIN al encender. La corrección de administración pasa 13 pruebas PAM/sudo con una cuenta temporal; el flujo de bloqueo pasa otras 19 pruebas controladas.

La barra tiene un botón para abrir las aplicaciones. La cuadrícula se ha renderizado en la pantalla real y sus capturas se han revisado. El teclado y los ajustes de giro/frecuencia están integrados; la escritura con el dedo en distintos programas, los gestos y otros detalles de manejo siguen en pruebas.

Linux y Android usan la Adreno 650. Android sin Google pasa 31 pruebas de APK y ciclo de arranque, incluida instalación confirmada, conservación de F-Droid y renderizado FD650. Tras el arranque en frío de Linux se ha observado Android en una ventana nativa, conservando la aplicación abierta. El inicializador con elección de Google pasa 27 pruebas aisladas; estas sustituyen la descarga y no demuestran todavía Google Play.

El selector Wi-Fi de la base limpia recibe las tres redes de solo 5 GHz detectadas en la comparación, sin ninguna ausente y sin publicar nombres ni direcciones. Falta confirmar físicamente selección y conexión. Los resultados de la base antigua permanecen separados.

Omarchy se ha actualizado al código revisado del 30 de octubre sin cambiar kernel, políticas del PIN ni botón de apagado. Pasan las tres pruebas de upstream relacionadas y las comprobaciones de los paquetes. Se ha añadido una calibración del reloj de solo lectura: recupera la hora sin escribir en el firmware y pasa 12 pruebas. Falta su propia comprobación después de apagar completamente.

La base anterior de Omarchy entregó vídeo desde las cuatro cámaras y confirmó tonos por el altavoz. La corrección de cámara pasó 40 aperturas con la candidata y otras 12 con la biblioteca instalada. Falta repetir la aceptación gráfica y física de fotos, vídeo y audio en esta base limpia. Android tiene comprobado el transporte estéreo a una salida virtual, no todos sus dispositivos físicos.

Las huellas no permiten aún registrar ni desbloquear. Las llamadas, SMS y datos necesitan una SIM de pruebas. El GPS necesita posicionamiento fiable en exterior. El USB-C directo no dio imagen y sigue sin estar soportado. Quedan también batería, suspensión y estabilidad prolongada.

Es un port de desarrollo con avances reales y límites visibles. «100 % funcional» es el objetivo, no el estado actual. La [tabla principal](../../README.md) y el [registro de instalación](../clean-install.md) distinguen lo comprobado, lo heredado y lo pendiente. Se mantienen los créditos y licencias del software utilizado. Se excluyen firmware propietario, imágenes personalizadas, copias de particiones, diagnósticos privados y credenciales.
