# Pruebas pendientes del Apollo

Estado al **3 de noviembre de 2026**. Esta lista acompaña al [checkpoint de código](checkpoint-2026-11-03.md). Las casillas sin marcar son trabajo pendiente, no resultados.

## Qué está comprobado antes de tocar el arranque

- [x] Kernel 7.3.1 R14 instalado y arranque nativo anterior comprobado en un Mi 10T Pro.
- [x] Correcciones de repintado, área útil con teclado, giro y cierre de ventanas documentadas en el [hito gráfico](milestone-2026-11-03.md).
- [x] Paquetes del actualizador experimental instalados con firmas y verificación de integridad. La integración del nuevo initramfs está **inactiva**.
- [x] **66 comprobaciones pequeñas** del actualizador: selector/manifiesto 38, integración móvil 9, instalador aditivo 6, bloqueo de transacciones pendientes 8 y configuración privada 5.
- [x] **Seis arranques ARM64 virtuales en PC**, con R14, ext4, el selector C y el montador de esta versión: fallo de salud, retorno tras intentos limitados, aceptación, persistencia y reversión. La interfaz, las aplicaciones y la identidad eran sintéticas.
- [x] ALPM/pacman ARM64 real en PC: firmas auténticas del proyecto, rechazo de manipulación y cambios de configuración, bloqueo y limpieza de la transacción.
- [x] Preparación ARM64 real en el móvil de un conjunto inocuo que sólo añade un paquete marcador al candidato aislado. `/usr` y la base ALPM activos no cambiaron. El conjunto **no está encolado**; no se reinició ni se grabó ninguna partición.

[Evidencia pública saneada](evidence/2026-11-03-native-updates.json). Los arranques virtuales no son seis arranques físicos del teléfono. Los resultados de PC no certifican la interfaz o el hardware del Apollo.

## 1. Primer arranque físico del selector nuevo

- [ ] Confirmar modelo Pro y correspondencia de la imagen privada con ese dispositivo. Tener batería suficiente, cable fiable, copias verificadas del arranque/DTBO y recuperación conocida. Mantener las copias fuera del repositorio.
- [ ] Arrancar primero la imagen de prueba **en RAM**, conservando R14 en la partición de inicio. No hay una imagen pública genérica ni instrucciones de flasheo universal en este checkpoint.
- [ ] Comprobar selección coherente de `/usr`, `/opt`, base local ALPM y metadatos de adaptación, y conservación de la protección de almacenamiento.
- [ ] Acceder con la contraseña existente únicamente en el móvil. Confirmar usuario administrador, bloqueo seguro, Inicio, iconos y widgets. No exportar contraseñas, hashes ni archivos de identidad.
- [ ] Abrir una app nativa; probar teclado, Inicio/Recientes, cierre de la última app y giro en ambos sentidos. No debe haber negro, recortes, cambios de escala ni reinicios de la interfaz.
- [ ] Verificar que el servicio de salud espera al escritorio real y acepta la generación correcta; la pantalla de acceso sola no debe contar como éxito.

## 2. Actualización inocua desde Omarchy

- [ ] Usar Actualizar de Omarchy con el conjunto marcador ya preparado. Comprobar autorización habitual, firmas, versiones de partida, plan de dependencias y aviso de reinicio.
- [ ] Confirmar que la generación queda pendiente, sin modificar la generación activa ni `/home`. Las operaciones ALPM nativas posteriores deben quedar bloqueadas mientras haya una generación pendiente o sin confirmar.
- [ ] Hacer un **segundo arranque en RAM de la misma imagen nueva**. Antes de activar permanentemente ese initramfs, un reinicio ordinario volvería al R14 físico anterior y no ejecutaría el nuevo selector.
- [ ] Confirmar el paquete marcador en los archivos y en ALPM de la misma generación; comprobar escritorio/salud y persistencia de la identidad existente.
- [ ] Sólo tras superar lo anterior, activar el initramfs revisado como arranque habitual y comprobar un reinicio normal. Conservar una recuperación independiente.

## 3. Reversión y recuperación

- [ ] Solicitar reversión del conjunto marcador y comprobarla después del reinicio: desaparece el marcador y coinciden `/usr`, `/opt`, ALPM y metadatos.
- [ ] En una prueba controlada con datos sintéticos, provocar falta de salud y confirmar el límite de intentos y retorno. El selector no demuestra recuperación automática de todos los bloqueos de hardware.
- [ ] Confirmar que usuario, contraseña, archivos personales y configuración conservada siguen funcionando. Registrar sólo resultados y versiones, nunca esos archivos.
- [ ] Comprobar actualización interrumpida, espacio insuficiente, cambio concurrente de la base ALPM y paquete que intenta modificar configuración compartida. Deben fallar antes de aceptar un estado incoherente.

## 4. Instalación limpia y sistema mínimo

- [ ] Generar una imagen limpia reproducible sin usuario propietario ni datos de desarrollo. El asistente preparado no equivale a una imagen completa de instalación.
- [ ] En un destino limpio y desechable, completar usuario administrador, nombre visible, contraseña o PIN, nombre del equipo, idioma, zona horaria, teclado y selección de aplicaciones.
- [ ] Confirmar primera sesión SDDM/logind, sudo con la misma contraseña de la cuenta y cambio posterior de contraseña con letras. Recuperar un alta interrumpida sin sobrescribir una cuenta existente.
- [ ] Revisar físicamente posición del PIN/teclado, vertical/horizontal y tamaños naturales de diálogos. La nueva distribución necesita aceptación humana.
- [ ] Probar Web/Epiphany, enlaces de Omarchy y tienda de plugins; instalar y retirar una app desde Bazaar. Verificar actualizaciones Flatpak sin sustituir la pila nativa protegida.
- [ ] Probar la navegación de servicios web con la cuenta del usuario sólo en el móvil. Un acceso web no es un cliente Linux oficial ni garantiza funciones de una APK.

## 5. Pendientes de hardware y uso diario

- [ ] SIM en la ranura física 1: PIN en el móvil, cobertura, datos con detección de operador, reconexión, IPv6 y SMS. La SIM estaba retirada en la última validación de R14.
- [ ] Llamadas: auricular, micrófono, entrantes y manos libres. **El altavoz sigue sin resolver; hubo distorsión y un reinicio reportado.** Diagnosticar la ruta antes de repetir pruebas de ganancia alta.
- [ ] Huella: soporte real del sensor y ruta segura, captura guiada, verificación, errores/reintentos, desbloqueo de sesión y alternativa por contraseña. **No es funcional en esta versión.** No registrar plantillas ni sustituir la autenticación por una simulación.
- [ ] GPS con posición real, cámaras/calidad/vídeo en R14, Bluetooth/audio, NFC, IR, proximidad y vibración.
- [ ] Apagado real frente a reinicio, conexión del cargador con el sistema apagado y animación de carga centrada con logo. No dar por cerrado este punto por una previsualización.
- [ ] Suspensión y despertar físicos; consumo en reposo y con pantalla, temperaturas y refrescos 60/90/120/144 Hz y automático 90/144 en condiciones comparables.
- [ ] Giros rápidos y lentos, ventanas pequeñas, teclado, diálogos, varias apps y cierre repetido. Medir detección del sensor por separado de la entrega del fotograma.

## Qué falta para actualizar la base y el kernel

- [ ] Canal público mantenido de conjuntos firmados, compatibilidad de nuevas bases de Omarchy y migraciones de configuración/datos de aplicaciones.
- [ ] Actualización de kernel/initramfs/DTB con recuperación validada. **kexec y el cambio automático de kernel no están implementados ni validados.** El prototipo actual conserva el mismo kernel.
- [ ] Constructor público completo y pruebas de instalación/recuperación reproducibles; validación separada del Mi 10T no Pro.

Si falla el acceso, el escritorio, la salud o la coherencia de versiones, detener la promoción y volver al arranque conocido. No marcar una casilla por un icono visible, una unidad activa o una prueba sintética. Un resultado público debe incluir versión, escenario y resultado sin números, redes, credenciales, calibración, registros completos ni imágenes privadas.
