# Pruebas pendientes del Apollo — 4 de noviembre de 2026

Esta lista acompaña al [estado actual](milestone-2026-11-04.md) y a las
[fuentes del lector](../experiments/native-fingerprint/README.md). Las casillas
marcadas son resultados concretos, no una aceptación completa del teléfono.

## Ya comprobado

- [x] R15 (`r15-ddr-pm1`) instalado y Hyprland 0.57.1 en uso.
- [x] Inicio, iconos y widgets; giro, barras, ventanas y teclado aceptados por el usuario.
- [x] Acceso original de Omarchy centrado con entrada suave y fondo posterior aceptado.
- [x] Captura y registro de una huella real; 29 muestras seguras.
- [x] Base cifrada autenticada guardada y recargada únicamente en el móvil.
- [x] Dedo registrado reconocido y otro dedo real rechazado.
- [x] Servicios seguros detenidos y módulo del sensor descargado al terminar las pruebas.
- [x] Selector recuperable instalado; candidata con marcador firmada arrancada;
  archivos/ALPM emparejados y salud de la generación actual aceptada.
- [x] Nueva cohorte de huella/autenticación preparada y firmada en el PC:
  340 casos de PAM ARM64, 32 del adaptador simulado, 1.732 de decisión,
  11 de activación/restauración y controles de interfaz Qt ARM64.

## 1. Próxima prueba de huella — conservar el dedo existente

- [ ] Recuperar conexión USB/SSH del Apollo y confirmar el estado instalado.
- [ ] Instalar la cohorte firmada sin activar PAM. Comprobar firmas, versiones,
  coherencia de actualización y adopción sólo de metadatos del dedo ya guardado.
- [ ] Abrir Huellas y usar el dedo registrado: fprintd debe comunicar coincidencia.
- [ ] Repetir con un dedo no registrado: debe comunicar que no coincide. Un
  resultado inesperado impide la activación; no sustituirlo por una simulación.
- [ ] Verificar cancelación, lector ocupado/no disponible y limpieza: servicios
  seguros detenidos y sensor descargado al finalizar.
- [ ] Sólo después de ambas pruebas, activar la política por servicio con copia
  local de los archivos originales y alternativa por contraseña.

## 2. Bloqueo, administración y acceso inicial

- [ ] Bloquear: dedo incorrecto no entra; dedo registrado desbloquea.
- [ ] Confirmar que la contraseña habitual sigue entrando y que cancelar no
  deja la lectura activa ni impide usar el teclado.
- [ ] sudo: Enter vacío selecciona huella; una contraseña escrita usa la ruta
  original sin esperar al lector. Probar una operación inocua autorizada.
- [ ] Polkit: Huella, Confirmar y Cancelar deben caber y responder, también en
  horizontal y con teclado. Mantener sudoers y controles de cuenta/sesión.
- [ ] Con el usuario presente, cerrar sesión y comprobar «Usar huella» en SDDM.
  Repetir tras reinicio y probar la contraseña alternativa.
- [ ] Probar restauración de la configuración gestionada antes de dar por
  aceptada la actualización. No borrar huellas ni credenciales.
- [ ] Ampliar dedos/gestión y despertar desde suspensión completa sólo con huella.
  **Este último despertar todavía no está implementado.**

## 3. Consumo, giro y fiabilidad

- [ ] Medir reposo desconectado con hora inicial/final, capacidad, temperatura,
  brillo, refresco y radios controlados, sin publicar identificadores.
- [ ] Comparar PM1 con el R15 anterior en condiciones equivalentes. No hay un
  porcentaje demostrado de mejora de batería; el drenaje sigue investigándose.
- [ ] Suspensión y despertar repetidos, USB tras reanudación, bloqueo y lector
  sin bucles de lectura que mantengan el hardware despierto.
- [ ] Giros rápidos/lentos, ambos lados, apps pequeñas, diálogos, teclado y cierre
  repetido. Separar detección del sensor y entrega del fotograma.
- [ ] Repetir arranques y sesiones largas; conservar historial de bloqueos y recuperación.

## 4. Actualización, instalación limpia y aplicaciones

- [ ] Ampliar reversión real y fallo de salud controlado con datos desechables.
- [ ] Interrupciones, espacio insuficiente, ALPM concurrente y migraciones deben
  fallar sin aceptar archivos y base de paquetes de generaciones distintas.
- [ ] Crear una imagen limpia reproducible, sin cuenta ni datos de desarrollo.
- [ ] Completar usuario administrador, nombre visible, contraseña/PIN, idioma,
  zona horaria, teclado y selección de apps; aceptar su primera sesión real.
- [ ] Comprobar Chromium, enlaces, tienda de plugins y una instalación/retirada
  de app nativa. Android/Waydroid sigue retirado; APK no equivale a app Linux nativa.
- [ ] Validar ZapFast sin publicar cuentas, claves, conversaciones ni datos personales.
- [ ] Canal público, nuevas bases de Omarchy y actualización segura de
  kernel/initramfs/DTB siguen pendientes. No ejecutar una actualización genérica
  ni desactivar sus guardas: los cambios automáticos de kernel no están aceptados.

## 5. Hardware pendiente

- [ ] SIM/datos con operador automático, otras redes, reconexión, IPv6 y SMS.
- [ ] Auricular, micrófono, llamadas entrantes y manos libres. **El altavoz sigue
  sin resolver: hubo distorsión y un reinicio reportado.** Diagnosticar antes
  de repetir ganancias altas; no prometer AEC ni micrófono corregido.
- [ ] GPS con posición real; calidad/vídeo/orientación de cámaras en R15.
- [ ] Bluetooth/audio, NFC, emisión IR, proximidad y vibración útil.
- [ ] Apagado real, conexión de cargador en frío y animación de carga apagado.
- [ ] Pruebas separadas del Mi 10T no Pro: los resultados del Pro no lo certifican.

No publicar números, redes, credenciales, plantillas, calibración, imágenes
privadas ni registros completos. Una interfaz visible o prueba sintética no
marca una función como aceptada físicamente.
