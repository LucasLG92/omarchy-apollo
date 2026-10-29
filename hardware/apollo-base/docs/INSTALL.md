# Instalación persistente y recuperación

**Estado de esta revisión:** base persistente r5/kernel 23 en la unidad de pruebas. El borrado inicial de userdata tuvo autorización expresa y no se repitió al actualizar. KDE, cambios persistentes y WiFi comprobados; encendido físico sin cable confirmado por el propietario en r5, seguido de verificación del nuevo arranque y recuperación de USB/SSH. No es una guía de flasheo universal ni una entrega estable para terceros.

## Diseño de la candidata

- Conserva la tabla de particiones y el cargador de Xiaomi.
- Usa `userdata` como ext4 y guarda una base SquashFS verificada en `base/arch-apollo.sqfs`.
- Conserva cambios de programas, configuración y `/home` en `state/upper`, mediante overlayfs. Se verificó la conservación de un archivo de usuario, identidad del sistema y clave del servidor entre reinicios.
- El initramfs localiza exactamente `PARTNAME=userdata`, verifica marcador y SHA256 y arranca systemd desde el almacenamiento interno. No descarga el sistema desde el ordenador.
- La imagen persistente va en `boot`; DTBO de Android debe quedar vacío para el DTB mainline probado. No se modifica recovery, GPT, ABL, XBL, TrustZone, persist, EFS ni metadata.

**Formatear userdata borra aplicaciones, fotos, archivos y ajustes de Android.** No hay cifrado de datos Linux implementado en esta candidata. Una copia de boot/recovery no es una copia de los datos personales. Conservarlos requiere un respaldo independiente y verificable antes del borrado. El consentimiento debe corresponder al teléfono y al borrado concreto.

## Preparación obligatoria

1. Confirmar modelo exacto y cargador desbloqueado. Una unidad parecida no basta.
2. Obtener y verificar copias privadas de boot, DTBO, recovery, vbmeta y calibraciones/NV del **propio** teléfono. No publicarlas ni sustituirlas por las de otra unidad.
3. Probar en RAM la pareja kernel/rootfs que se pretende instalar. Comprobar teclado, acceso local y recuperación.
4. Generar manifiesto con tamaño y SHA256 de base/boot y tamaño real de userdata. Verificar espacio libre, ausencia de montajes/holders y copias antes de cualquier escritura.
5. Aprobar expresamente la pérdida de los datos de Android antes de ejecutar el modo de borrado.

`system/install-persistent` se ejecuta como root desde Linux en RAM. Sin las opciones de borrado hace solo preflight. La operación destructiva exige tanto una frase de aceptación específica como el marcador local de autorización. Se niega a ejecutarse desde una raíz persistente, sobre otro modelo, con hashes/tamaños incorrectos, con userdata montado o usando Python con aserciones desactivadas.

Tras copiar la base vuelve a calcular su hash; solo después escribe boot y lo lee de vuelta para comprobarlo. No reiniciar ni dejar que un arnés de pruebas restaure automáticamente DTBO durante la transacción. Un corte durante el formateo puede perder los datos aunque no llegue a cambiar boot.

## Primer inicio

KDE inicia sesión local como `apollo`. La contraseña de pruebas se elimina de la candidata y la cuenta de root no tiene contraseña utilizable. `apollo-firstboot-password` solicita crear una contraseña directamente en el móvil. No se recoge por el chat, por el PC ni en registros. La excepción limitada de sudo para esa configuración se elimina tras completarla.

Mientras no se configure una contraseña, el bloqueo automático queda desactivado para evitar dejar al usuario fuera. La sesión local tiene acceso a sus archivos. El propietario deberá configurar el bloqueo deseado después. La candidata no cifra el almacenamiento.

SSH escucha únicamente en `172.16.42.1` y admite claves del propietario desde `172.16.42.2`, la red USB de mantenimiento. No hay contraseña compartida, acceso por WiFi/LAN ni reenvío. La clave pública del propietario se aprovisiona localmente, fuera de Git; las claves de servidor se generan en el primer arranque. La imagen permanente no debe conservar la consola USB con shell root usada para las pruebas RAM.

En el primer encendido autónomo se detectó una carrera: SSH intentaba escuchar antes de existir la dirección USB y agotaba los reintentos. `20-apollo-usb.network` configura la dirección sin portadora y `30-apollo-sshd-usb-retry.conf` permite reintentar cada tres segundos sin agotar el límite. La reconexión después de usar el monitor pasó sin una nueva intervención manual; quedan más encendidos fríos para validar esta corrección.

## Fallo inicial y reparación r2

La primera imagen permanente creaba `/dev/pts` antes de montar devtmpfs en `/dev`. Ese montaje ocultaba el directorio; el montaje posterior de devpts fallaba y PID 1 salía, provocando `Attempted to kill init` con código `0x0000ff00`. La reparación crea `/dev/pts` después de montar `/dev`. Se reprodujo el orden incorrecto en una prueba aislada, se recompuso boot y se verificó su lectura tras escribirlo. No se volvió a formatear userdata.

El propietario creó su contraseña local. En esta instalación ya no está pendiente el asistente inicial. Las máscaras de servicios de audio de las pruebas silenciosas se retiraron con `apollo-enable-audio`; la salida se deja silenciada para que el propietario decida cuándo activarla. El helper no reproduce sonidos.

## Actualizaciones de la instalación ensayada

R3 actualiza kernel/boot a 21 y activa el backend Zstd de zram. R4 los actualiza a 22, corrige el modo de reinicio a bootloader y habilita Landlock para que funcione el aislamiento del gestor de paquetes. Los datos y la base SquashFS se conservan. Las imágenes y los manifiestos de recuperación siguen siendo privados.

`system/update-kernel21-to22.py` conserva el núcleo del actualizador **específico de esta transición**; no es un actualizador general para cualquier versión. Exige Linux persistente Apollo con paquete 21 y los archivos/manifiesto preparados en `maintenance/kernel22`. El modo `plan` comprueba modelo, almacenamiento, batería, partición boot y hash anterior. `apply` instala el paquete correspondiente, conserva el boot anterior, escribe solo boot, sincroniza y lee de vuelta. Si falla la transacción intenta restaurar la pareja anterior. No formatea userdata ni cambia DTBO. Hace falta preparar las entradas propias antes de usarlo; no ejecutarlo por probar en una instalación distinta.

No usar los arneses históricos de arranque RAM para mantener una instalación interna: sus fases de restauración de Android pueden reponer DTBO y romper el arranque Linux. Tampoco reinstalar formateando userdata para aplicar una actualización ordinaria.

La r4 añade controles gráficos de red/pantalla y herramientas locales de diagnóstico/ajuste. Las claves de redes se introducen en el propio móvil, nunca en un informe o repositorio. Los scripts de pantalla se ejecutan como usuario y guardan configuración privada; la prueba del lector utiliza sudo normal y no incorpora contraseñas ni una nueva excepción de privilegios.

## Validación posterior

Comprobar dos reinicios con un archivo y un ajuste persistentes, reinicio físico sin cable, acceso a Internet con HTTPS sobre WiFi, carga/batería, teclado y sudo local. No describir la instalación como autónoma hasta haber observado el encendido sin PC. Mantener los fallos de hardware en la matriz de estado aunque el escritorio arranque.

## Volver a LineageOS

Entrar en el cargador con encendido + volumen abajo si no funciona el reinicio por software. Verificar producto, tamaño de partición y límite de descarga antes de escribir; se ha observado que fastboot puede enumerar antes de que UFS esté listo.

Restaurar **boot y DTBO originales verificados de esa unidad** y arrancar su recovery. Si userdata se convirtió a ext4 Linux, Android requerirá restablecer/formatear sus datos desde recovery para recrear su almacenamiento cifrado; ese paso vuelve a borrar los datos de la partición. Restaurar después los archivos personales desde la copia independiente, si existe. No restaurar NV/EFS/calibraciones por rutina.

El sistema Android de `super` se conserva en este diseño. Si se cambia también, hará falta su copia/ROM correspondiente. No hay procedimiento probado de volver a Android conservando la nueva instalación Linux y sus datos. Las imágenes y hashes de recuperación son privados y no se incluyen aquí.
