# Omarchy Apollo

**Omarchy nativo en el Xiaomi Mi 10T Pro (`apollo`), con interfaz táctil y resultados verificables.** Un escritorio Linux en formato móvil, con Hyprland, Quickshell y la GPU Adreno 650.

[English / portada](../../README.md) · [Estado completo](../status.md) · [Pruebas recientes](../validation-2026-11-02.md) · [Hoja de ruta](../roadmap.md)

<p align="center"><img src="../../media/hero.svg" width="100%" alt="Omarchy Apollo: Linux nativo adaptado a un teléfono"></p>

## Estado actual: arranque nativo, SIM comprobada y fallo de escritorio abierto

**Omarchy 4.5 RC2 está instalado nativamente en la unidad Pro:** boot grabado, raíz ext4 y login local comprobados. **En el último arranque en frío reapareció el centro negro del escritorio**, con barra y buscador visibles. Un reinicio oficial solo de Quickshell, con shell .8 ya instalado, recuperó fondo, reloj y ocho iconos según revisión privada del controlador. La causa y la corrección definitiva del inicio siguen abiertas; no se publica esa captura.

**La entrada humana del PIN de acceso con SIM UI 0.2.1 pasó**, solo en el teléfono. El módem llegó a conectado/home y ya no requirió el PIN primario; quedó PIN2 secundario (enum3), distinto de una segunda SIM. El perfil AUTO estaba activo y HTTPS204 **ligado a celular IPv4** funcionó con Wi-Fi conectado/preferido. No se publican PIN, operador, APN, direcciones ni capturas.

Tras instalar shell .8/gestos-teclado r2, el usuario aceptó HOME, mantener para recientes y cerrar el teclado. Afinado completo y volver a Inicio al cerrar la última app de Recientes quedan pendientes. **No se ha verificado un móvil completo para uso diario**: el fallo de escritorio, Polkit, hardware/audio restante, IPv6, batería/suspensión e instalador público siguen abiertos. [Evidencia y límites](../validation-2026-11-02.md).

Los resultados anteriores conservan su alcance histórico; Waydroid no se ha revalidado íntegramente en esta base.

<p align="center"><a href="../../media/apollo-home-r11.png"><img src="../../media/apollo-home-r11.png" width="245" alt="Captura real del inicio de la sesión R11, sin el aviso de PIN"></a></p>

## Arranque original de Omarchy: V2

<p align="center"><img src="../../media/apollo-boot-r16.png" width="180" alt="Captura KMS real de Plymouth en R16"> <img src="../../experiments/original-boot-v2/previews/login-keyboard-432.png" width="180" alt="Render Qt del acceso V2 con teclado; no es una autenticación real del móvil"></p>

Izquierda: **captura real** del arranque nativo R16, solo logo y fondo. Derecha: **render Qt** del acceso SDDM con ayuda táctil. Se conservan los PNG oficiales MIT de Omarchy y el fondo `#1a1b26`; el estado inicial a 432×960 coincide píxel a píxel con la referencia original.

R16 cargó el tema con Qt/SDDM ARM64 en modo de prueba; **R20 verificó después un acceso real con la credencial local, también tras arranque normal**. En la prueba R16 no se configuró contraseña/PIN ni se cambió PAM, autologin o selección permanente del tema. La configuración local y el acceso SDDM/PAM posterior de R20 se documentan por separado. El logo del nuevo arranque sigue sin confirmación visual humana. El teclado aparece al tocar el campo, no tiene PIN fijo y no necesita QtVirtualKeyboard. El desbloqueo táctil LUKS sigue pendiente. [Fuentes y límites](../../experiments/original-boot-v2/README.md) · [Integración en español](../../experiments/original-boot-v2/INTEGRACION.txt).

## Avances comprobados

- R20: raíz ext4 interna arrancada, escritorio confirmado y sistema de archivos ampliado a su partición. La transferencia inicial se verificó por lectura física completa antes del primer arranque nativo con escritura; no se publican imágenes ni datos de esa unidad.
- Arranque nativo grabado y repetido, con guardas de firmware/calibración y prefijos de imágenes esperadas de boot/recovery comprobados. `userdata` se usa para la raíz; `super`, `metadata` y `cache` de Android fueron limpiados y el siguiente arranque normal funcionó.
- Formulario local [r5 y prueba sintética](../../experiments/owner-setup/README.md): credencial guardada y acceso real posterior comprobado. El cierre automático solo tiene aceptación sintética; Polkit queda pendiente.
- Shell .8/gestos-teclado r2 instalados: HOME, mantener para recientes y cerrar teclado aceptados por el usuario. Ajustes y volver a Inicio al cerrar la última app siguen pendientes.
- Recurrencia del centro negro tras login en frío, recuperado con reinicio oficial de Quickshell. No se considera una corrección definitiva del inicio.
- Escritorio nativo con renderizado **Freedreno FD650**, entrada táctil, aplicaciones y teclado en pantalla.
- R19: GNOME Calls 51.1 abierto sin número ni URI de marcado. El usuario llamó a su buzón; 65 segundos de observación vieron como máximo una llamada DIALING→ACTIVE, dirección OUTGOING y cero errores de consulta. Confirmó conexión y audio del buzón. El agente no marcó ni recibió/publicó el número y no se grabó audio.
- Las cuatro cámaras entregan imágenes de 640×480. La principal capturó 24 imágenes RGB de **3000×2256** y la ultra gran angular otras 24 de **4200×3120**.
- La reserva de memoria contigua pasó de 32 a **256 MiB**, resolviendo el fallo de asignación DMA de la principal.
- En R11, la sesión normal consultó llamadas sin el aviso de autenticación del sistema al iniciar. Administración del servicio y cambios de firmware siguen requiriendo autenticación de administrador. La UI PIN de R18 se ejecutó como root solo en la sesión RAM supervisada; la integración con la sesión normal sigue pendiente.
- Se han comprobado el encendido/apagado de la linterna desde la sesión normal y el cierre/reinicio del servicio EFS del módem. Falta confirmar visualmente la luz y probar una transferencia EFS real.
- En R12, el motor **AW8697** respondió a un pulso de **120 ms al 12,5 %**: el usuario confirmó una vibración **muy suave**. La sesión normal obtuvo acceso con `uaccess`, sin escritura para todos; feedbackd abrió el dispositivo después de reiniciarlo para detectar la regla añadida en RAM.
- Infrarrojos aparece como dispositivo LIRC y anuncia capacidades `0x302`. Solo se consultaron: **no se emitió ninguna señal** ni se probó como mando.
- R20: perfil celular automático r2 creado desde cero tras arranque normal, ruta activa y HTTPS **204** por IPv4 con **Wi-Fi apagado**, en una red. No demuestra IPv6, velocidad ni autoconfiguración para cualquier SIM. Después el PIN local de la SIM fue aceptado y otra petición ligada a celular IPv4 devolvió HTTPS204 con Wi-Fi conectado/preferido. No se publican operador, APN, direcciones ni capturas.
- En R13, el usuario conectó Wi-Fi desde la pantalla. Una petición HTTPS obligada a usar esa interfaz devolvió **200** desde `omarchy.org`. No se publican nombre, direcciones ni contraseña de la red.
- Corregido un fallo concreto al crear el archivo temporal permitido de sensores: 26 comprobaciones ARM64 RPC/VFS y creación privada en RAM. No apareció ese error en el registro de arranque recogido ni durante **20,97 segundos de observación**. Acelerómetro y luz siguen disponibles; proximidad no. Ese tiempo no es una medida de arranque ni una mejora general de velocidad.
- En R18, el usuario introdujo el PIN únicamente en el Apollo. Se verificaron acceso desbloqueado, registro en red de origen y LTE/NR5G anunciados. No se recibió ni publicó el PIN, números, operador o identificadores de la tarjeta.
- R18/R19 volvieron automáticamente y verificaron Android con boot/DTBO originales. R17 había requerido botones y cargador completo: se conserva ese resultado y todavía no se da por fiable el retorno automático. No se formateó `userdata` ni se completó la instalación permanente en R19.

La versión instalada actual es **0.2.1-1**: compacta, sin el candado grande, con campos `Gtk.Button`/`PasswordEntryBuffer` y teclado propio sin `Gtk.Editable` ni superficie OSK. El controlador del proyecto informa de núcleo de radio idéntico, 13 métodos de flujo con AST idéntico, 18 pruebas de clasificación y 17 GTK ARM64 sintéticas correctas. **La entrada PIN humana con 0.2.1 tras el arranque en frío quedó confirmada**: conectado/home, PIN primario ya no requerido y PIN2 secundario enum3. El estado anterior enum2/sin sesión quedó superado. El escritorio negro reaparecido es un problema de presentación/inicio distinto de esa autenticación correcta. No se publican fuentes nuevas de la app.

Como registro histórico, la app de R18 fue **0.1.2-1**, con un mensaje confuso para PIN2. La [fuente 0.1.3-1](../../experiments/sim-unlock/README.md), revisada antes con GTK/GIO ARM64 sintético, **se cargó físicamente en R19 y se comprobó su proceso/ventana**. El usuario cerró un aviso pero no quedó identificado su origen ni si hablaba de PIN2 o SIM2; la aceptación humana del arreglo sigue pendiente y no se repitió un envío del PIN de acceso. El módem ya estaba registrado y no lo requería. Dos slots informados, uno ocupado y otro vacío, no demuestran dos tarjetas físicas; el proxy actual no coincidía con el array de slots, así que el mapeo sigue sin validar.

R12 necesitó añadir la regla del motor durante la sesión. En R13 se probó un arranque completo en RAM con kernel R6 y runtime **`20261101-6`**, que incluye esa regla: la sesión normal tiene acceso y feedbackd abrió el dispositivo **sin reinicio manual**. La intensidad física confirmada sigue siendo la muy suave de R12. [Detalle de R13](../validation-2026-11-01.md#r13--wifi-runtime-v6-and-sensor-scratch-files).

## Lo que falta

**La llamada saliente y el audio descendente de R19 no verifican micrófono/uplink, llamadas entrantes, SMS, velocidad 5G, AEC ni ruta VoLTE.** La prueba IPv4 posterior de R20 tiene alcance separado; faltan IPv6, otras SIM/redes y comportamiento sostenido de la autoconfiguración r2. R18 no tuvo intento entrante confirmado; sus cero objetos observados no fueron prueba de fallo. El mapeo entre ranura física y lógica sigue pendiente. El diálogo SIM-PIN es distinto de la credencial Linux/PAM guardada localmente en R20; el acceso SDDM/PAM posterior pasó, pero la administración por Polkit no se ha validado. Faltan reconexión/suspensión Wi-Fi, emparejamiento/audio Bluetooth y lectura de etiquetas NFC.

Quedan GPS, huella, proximidad, emisión óptica y uso como mando IR; la intensidad del motor y su respuesta en aplicaciones necesitan más pruebas. También faltan suspensión, autonomía, recuperación y actualizaciones coherentes. La instalación y el arranque normal persistente de la nueva base sí están verificados en esta unidad. El controlador de la principal **no ofrece 108 MP**. Las capturas prueban el transporte de imágenes; calidad, color, enfoque óptico, vídeo y giro necesitan más pruebas.

## ¿Sirve para el Mi 10T 5G normal?

La base es aprovechable, pero **este port solo está probado en la unidad Pro del proyecto**. El normal necesita validar/adaptar su cámara principal, configuración de RAM/almacenamiento y calibración propia. La imagen privada actual no es genérica ni se debe flashear directamente en otro móvil, tampoco en otro Pro. [Tabla y FAQ de compatibilidad](../compatibility.md).

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
