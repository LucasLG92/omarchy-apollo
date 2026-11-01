# Omarchy Apollo

**Omarchy nativo en el Xiaomi Mi 10T Pro (`apollo`), con interfaz táctil y resultados verificables.** Un escritorio Linux en formato móvil, con Hyprland, Quickshell y la GPU Adreno 650.

[English / portada](../../README.md) · [Estado completo](../status.md) · [Pruebas recientes](../validation-2026-11-01.md) · [Hoja de ruta](../roadmap.md)

<p align="center"><img src="../../media/hero.svg" width="100%" alt="Omarchy Apollo: Linux nativo adaptado a un teléfono"></p>

## Estado actual: 4.5 RC2 en RAM

La nueva base **Omarchy 4.5 RC2** se ha probado de forma nativa en el teléfono, con Linux ARM64 y systemd como PID 1. En **R19**, el usuario marcó manualmente su buzón: **la llamada saliente conectó y pudo escucharlo**. El backend confirmó ACTIVE/OUTGOING. **Micrófono/uplink, entrantes, SMS, datos IP, velocidad, AEC y ruta VoLTE siguen sin verificar.** Android no actúa como anfitrión. R19 volvió automáticamente a Android con boot/DTBO originales comprobados; la recuperación manual de R17 mantiene pendiente la fiabilidad general.

Se conservan como resultados históricos el Wi-Fi real de R13 y el arranque original R16 en rescate RAM mínimo. R16 no probó el escritorio completo ni autenticación PAM.

**La instalación permanente de esta nueva base sigue pendiente. No es todavía un móvil plenamente funcional ni existe un instalador público validado.** La instalación y las pruebas de Waydroid del 30 de octubre pertenecen a una [etapa anterior](../history/README-2026-10-30.md); no demuestran esas funciones en la nueva base.

<p align="center"><a href="../../media/apollo-home-r11.png"><img src="../../media/apollo-home-r11.png" width="245" alt="Captura real del inicio de la sesión R11, sin el aviso de PIN"></a></p>

## Arranque original de Omarchy: V2

<p align="center"><img src="../../media/apollo-boot-r16.png" width="180" alt="Captura KMS real de Plymouth en R16"> <img src="../../experiments/original-boot-v2/previews/login-keyboard-432.png" width="180" alt="Render Qt del acceso V2 con teclado; no es una autenticación real del móvil"></p>

Izquierda: **captura real** del arranque nativo R16, solo logo y fondo. Derecha: **render Qt** del acceso SDDM con ayuda táctil. Se conservan los PNG oficiales MIT de Omarchy y el fondo `#1a1b26`; el estado inicial a 432×960 coincide píxel a píxel con la referencia original.

El tema carga con Qt/SDDM ARM64 real en modo de prueba, pero **el acceso PAM en el móvil no se ha probado**. No se ha configurado contraseña/PIN ni cambiado PAM, autologin o selección permanente del tema. El teclado aparece al tocar el campo, no tiene PIN fijo y no necesita QtVirtualKeyboard. El desbloqueo táctil LUKS sigue pendiente. [Fuentes y límites](../../experiments/original-boot-v2/README.md) · [Integración en español](../../experiments/original-boot-v2/INTEGRACION.txt).

## Avances comprobados

- Escritorio nativo con renderizado **Freedreno FD650**, entrada táctil, aplicaciones y teclado en pantalla.
- R19: GNOME Calls 51.1 abierto sin número ni URI de marcado. El usuario llamó a su buzón; 65 segundos de observación vieron como máximo una llamada DIALING→ACTIVE, dirección OUTGOING y cero errores de consulta. Confirmó conexión y audio del buzón. El agente no marcó ni recibió/publicó el número y no se grabó audio.
- Las cuatro cámaras entregan imágenes de 640×480. La principal capturó 24 imágenes RGB de **3000×2256** y la ultra gran angular otras 24 de **4200×3120**.
- La reserva de memoria contigua pasó de 32 a **256 MiB**, resolviendo el fallo de asignación DMA de la principal.
- En R11, la sesión normal consultó llamadas sin el aviso de autenticación del sistema al iniciar. Administración del servicio y cambios de firmware siguen requiriendo autenticación de administrador. La UI PIN de R18 se ejecutó como root solo en la sesión RAM supervisada; la integración con la sesión normal sigue pendiente.
- Se han comprobado el encendido/apagado de la linterna desde la sesión normal y el cierre/reinicio del servicio EFS del módem. Falta confirmar visualmente la luz y probar una transferencia EFS real.
- En R12, el motor **AW8697** respondió a un pulso de **120 ms al 12,5 %**: el usuario confirmó una vibración **muy suave**. La sesión normal obtuvo acceso con `uaccess`, sin escritura para todos; feedbackd abrió el dispositivo después de reiniciarlo para detectar la regla añadida en RAM.
- Infrarrojos aparece como dispositivo LIRC y anuncia capacidades `0x302`. Solo se consultaron: **no se emitió ninguna señal** ni se probó como mando.
- En R13, el usuario conectó Wi-Fi desde la pantalla. Una petición HTTPS obligada a usar esa interfaz devolvió **200** desde `omarchy.org`. No se publican nombre, direcciones ni contraseña de la red.
- Corregido un fallo concreto al crear el archivo temporal permitido de sensores: 26 comprobaciones ARM64 RPC/VFS y creación privada en RAM. No apareció ese error en el registro de arranque recogido ni durante **20,97 segundos de observación**. Acelerómetro y luz siguen disponibles; proximidad no. Ese tiempo no es una medida de arranque ni una mejora general de velocidad.
- En R18, el usuario introdujo el PIN únicamente en el Apollo. Se verificaron acceso desbloqueado, registro en red de origen y LTE/NR5G anunciados. No se recibió ni publicó el PIN, números, operador o identificadores de la tarjeta.
- R18/R19 volvieron automáticamente y verificaron Android con boot/DTBO originales. R17 había requerido botones y cargador completo: se conserva ese resultado y todavía no se da por fiable el retorno automático. No se formateó `userdata` ni se completó la instalación permanente en R19.

La app de R18 fue **0.1.2-1**, con un mensaje confuso para PIN2. La [fuente 0.1.3-1](../../experiments/sim-unlock/README.md), revisada antes con GTK/GIO ARM64 sintético, **se cargó físicamente en R19 y se comprobó su proceso/ventana**. El usuario cerró un aviso pero no quedó identificado su origen ni si hablaba de PIN2 o SIM2; la aceptación humana del arreglo sigue pendiente y no se repitió un envío del PIN de acceso. El módem ya estaba registrado y no lo requería. Dos slots informados, uno ocupado y otro vacío, no demuestran dos tarjetas físicas; el proxy actual no coincidía con el array de slots, así que el mapeo sigue sin validar.

R12 necesitó añadir la regla del motor durante la sesión. En R13 se probó un arranque completo en RAM con kernel R6 y runtime **`20261101-6`**, que incluye esa regla: la sesión normal tiene acceso y feedbackd abrió el dispositivo **sin reinicio manual**. La intensidad física confirmada sigue siendo la muy suave de R12. [Detalle de R13](../validation-2026-11-01.md#r13--wifi-runtime-v6-and-sensor-scratch-files).

## Lo que falta

**La llamada saliente y el audio descendente de R19 no verifican micrófono/uplink, llamadas entrantes, SMS, datos IP, velocidad 5G, AEC ni ruta VoLTE.** R18 no tuvo intento entrante confirmado; sus cero objetos observados no fueron prueba de fallo. El mapeo entre ranura física y lógica sigue pendiente. El diálogo SIM-PIN es distinto de la credencial Linux/PAM; esa integración y la administración por Polkit no se han validado. Faltan reconexión/suspensión Wi-Fi, emparejamiento/audio Bluetooth y lectura de etiquetas NFC.

Quedan GPS, huella, proximidad, emisión óptica y uso como mando IR; la intensidad del motor y su respuesta en aplicaciones necesitan más pruebas. También faltan suspensión, autonomía, primer PIN definitivo, arranque independiente de la nueva base y actualizaciones coherentes. El controlador de la principal **no ofrece 108 MP**. Las capturas prueban el transporte de imágenes; calidad, color, enfoque óptico, vídeo y giro necesitan más pruebas.

## Revisar o colaborar

El [registro 4.5](../rebase-4.5.md) identifica versiones, fuentes y alcance. Los [parches públicos](../../patches/rebase-4.5/README.md) están separados por componente y conservan sus licencias. Aún no forman un procedimiento completo de reconstrucción o instalación. No deben flashearse como una imagen ni usarse con un instalador de PC.

Se puede revisar el proyecto y comprobar los documentos sin conectar un teléfono:

```sh
git clone https://github.com/LucasLG92/omarchy-apollo.git
cd omarchy-apollo
python3 tests/check_public_docs.py
```

Son útiles los cambios pequeños con una prueba clara: controladores, cámara, audio, consumo, interfaz táctil, traducción y recuperación. [Cómo contribuir](../../CONTRIBUTING.md).

Si quieres seguir el avance, puedes dar una **estrella** al repositorio. La prioridad es que cada función anunciada tenga una prueba que la respalde.

El proyecto se apoya en Omarchy, Omarchy Mobile y los [paquetes de hardware de Apollo](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages), entre otros. Se mantienen sus créditos y licencias. No se publican firmware propietario, calibración, copias de particiones, identificadores, credenciales, fotos de cámara ni registros privados. [Seguridad y privacidad](../../SECURITY.md).
