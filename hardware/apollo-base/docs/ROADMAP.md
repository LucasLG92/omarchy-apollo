# Pendientes y criterios de aceptación

## Base instalada

- Hecho en la unidad: almacenamiento interno, archivo/identidad/claves persistentes, KDE/teclado/WiFi automáticos, HTTPS sobre WiFi y encendido físico sin cable confirmado por el propietario.
- Hecho: contraseña del propietario y mantenimiento por clave limitado a USB. El primer panic se reparó cambiando solo boot; recuperación de Android documentada.
- Hecho en r5: actualización recuperable de la pareja kernel/boot, Landlock funcional, selector WiFi y perfil de escritorio para la pantalla. Reinicios y vuelta desde FASTBOOT conservan la instalación y el acceso USB.
- Pendiente: más arranques fríos sin cable, constructor completo desde cero y procedimiento general de actualizaciones para terceros.

## Cámara y multimedia

- Medir foco óptico y funcionamiento del AF en qcam/app habitual con los cambios AK7377.
- Suspender con el dispositivo de enfoque abierto y verificar reanudación, además del caso inactivo ya probado.
- Repetir arranques fríos de frontal y principal. Calidad, colores, exposición y resolución completa.
- Estabilizador óptico, captura concurrente y resistencia prolongada.
- HEVC/VP9 en ventana, navegador, 10 bits/HDR, codificación, cambios de resolución y reproducción sostenida.
- Completar audio/micrófonos/auriculares y rutas de llamada cuando se autoricen pruebas sonoras.

## Funciones de teléfono

- Huellas: contacto real ya detectado. Completar protocolo de registro/comparación propios de Linux e integración fprint/PAM. No copiar plantillas Android.
- SIM: probar llamadas, SMS y datos. No hay SIM disponible en la prueba actual.
- Bluetooth con accesorio, NFC con etiqueta, proximidad y periféricos OTG.
- Ubicación exterior/recorrido, permisos de más aplicaciones y precisión medida.

## Estabilidad y otros sistemas

- Resolver inicialización UFS intermitente en fastboot y avisos SPMI/DSI restantes.
- Modo de reinicio al cargador corregido y probado en kernel 22; conservar la regresión en futuras versiones.
- Kernel 23 instalado: adopción de relojes inactivos y mantenimiento USB después de cambiar de raíz. KUnit, pruebas de recuperación y regresiones nativas de pantalla/cámaras/GPU/reposo pasan. Faltan más pruebas frías sin cable y de consumo. Detalles en [CANDIDATE-23.md](CANDIDATE-23.md).
- Completar la aplicación del país seleccionado al firmware WiFi autogestionado, conservando restricciones y calibración. La conexión de 5 GHz ya está verificada; no habilitar bandas por aparecer en una tabla genérica del controlador.
- Autonomía, suspensión prolongada, ciclos térmicos y gestión de batería.
- Constructor limpio y reproducible de imagen completa; auditar licencias antes de distribuir binarios.
- USB-C directo ya dio un resultado negativo. Investigar el cableado y alternativas de pantalla; no anunciar HDMI/DisplayPort funcional por la mera presencia del conector o del anuncio del monitor.
- Evaluar otras distribuciones ARM64 y eventualmente un arranque múltiple. UEFI y compatibilidad con cualquier sistema no están implementados. Un sistema x86 no se vuelve ARM por cambiar la imagen de arranque.
