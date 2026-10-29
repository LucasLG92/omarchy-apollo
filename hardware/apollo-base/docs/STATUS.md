# Estado del hardware

Actualizado: 29-10-2026. Probado en una unidad M2007J3SG. «Pasa» describe la prueba indicada, no una garantía de funcionamiento total ni de estabilidad prolongada.

| Componente | Comprobado | Falta o limitación |
| --- | --- | --- |
| Arranque | Base interna r5/kernel 23; persistencia y encendido físico sin cable confirmados, nuevo arranque cotejado tras reconectar | Más repeticiones, autonomía y uso prolongado |
| Pantalla/táctil | 1080×2400/144 Hz; escala 225 %, panel de 48 puntos, menú compacto, ventanas nuevas maximizadas y botones de tema ampliados | Rotación y experiencia táctil prolongada en todas las aplicaciones; no todas las apps de escritorio son adaptativas |
| Iluminación | Kernel 15: 96 peticiones; kernel 23: otras 12 rondas y blank/unblank con lectura de hardware y restauración de ajustes | Calibración física e inyección de fallos eléctricos |
| GPU | Adreno 650, Freedreno/GLES 3.2, Turnip/Vulkan 1.3 | Juegos, rendimiento sostenido, todas las aplicaciones y consumo |
| WiFi | Selector de redes confirmado por el usuario; conexión automática, DNS/HTTPS y reconexión. Escaneo de 2,4/5 GHz y HTTPS real a 5200 MHz | WPA3/roaming/consumo, más redes y aplicación del país seleccionado al firmware autogestionado |
| Bluetooth | Controlador e integración disponibles | Accesorio real, audio, HID y reconexión |
| Cámaras | Kernel 23: cuatro sensores, 90 fotogramas cada uno antes/después de reposo y tras el arranque permanente, como usuario de escritorio | Calidad, colores, exposición, resolución completa, concurrencia y app habitual |
| Frontal | Kernel 12: 144/144 aperturas en seis arranques; nuevas tandas de 24/24 tras reposo en 13, 14, 19, 20 y 23 | Arranques fríos y uso prolongado; los conteos pertenecen a versiones diferentes |
| Enfoque | Kernel 23: 100/100 antes y 40/40 después de s2idle, alimentación vuelve a reposo en la prueba aislada con observador de cámaras pausado temporalmente | Enfoque óptico, AF en aplicación, estabilizador y suspensión con cámara abierta |
| GPS | Receptor real, ModemManager, GeoClue/D-Bus y libgeoclue; autorización y denegación probadas | Precisión exterior medida, más aplicaciones y recorrido real |
| Lector de huellas | Kernel 21: contacto coordinado con el usuario, interrupción 197→198 y sensor apagado al terminar. Prueba local instalada | Consulta de dimensiones incompatible; registro, comparación, fprint/PAM y desbloqueo pendientes; no se usan plantillas Android |
| Audio | PCM S16LE/48 kHz en pruebas anteriores; PipeWire/pulse/WirePlumber activos tras reiniciar. Retiradas las máscaras de las pruebas silenciosas, volumen controlable | Falta prueba audible completa, micrófonos, estéreo, auriculares y llamadas |
| Vídeo | Hardware H.264/HEVC/VP9 y comparación de fotogramas; Clapper H.264 en Wayland | HDR/10 bits, ventana HEVC/VP9, navegador, codificación y rendimiento sostenido |
| Módem | SDX55 reconocido; estado sin SIM | Llamadas, SMS, datos y emergencia no probados |
| Sensores | Movimiento, brújula, luz y servicios SSC accesibles | Calibración, proximidad virtual y uso real en aplicaciones |
| Batería/carga | Información de batería, carga y temperatura accesible | Autonomía, descarga prolongada y seguridad térmica bajo carga sostenida |
| NFC | Integración pendiente de prueba real | Etiqueta y lectura/escritura funcional |
| USB | R5: servicio NCM después de cambiar de raíz; arranque frío sin cable, reconexión física y retorno de s2idle con DHCP/SSH, sin reiniciar servicios manualmente | Más cambios de cable/rol y periféricos OTG reales |
| Pantalla externa | USB-C directo probado sin imagen; el monitor anuncia SVID DisplayPort, modo inactivo; sin conector DRM externo | Ruta física de vídeo no demostrada; no hay soporte funcional de DisplayPort |
| Hora | Kernel 14 evita volver al contador RTC de 1970; sincronización UTC por WiFi | Hora exacta persistente sin red; la fecha guardada es solo un mínimo |
| Suspensión | Kernel 23: s2idle de unos 13 s con alarma RTC y reanudación de escritorio/cámaras/USB | Suspend prolongado, cámara abierta, consumo y múltiples ciclos autónomos |
| Reinicio | Kernel 22: orden normal de bootloader lleva a FASTBOOT, el PC lo detecta y vuelve a Linux sin pulsaciones físicas | UFS intermitente en fastboot sigue abierto; conservar las comprobaciones antes de escribir |
| Instalación de programas | Kernel 22: Landlock ABI 9 y denegación real en proceso de prueba sin privilegios; siete paquetes oficiales de escritorio con SHA256/PGP e integridad verificados | Revisar futuras actualizaciones del sistema y su efecto en los paquetes de integración |

El monitor fue conectado mediante cable USB-C directo: no apareció imagen. El registro muestra negociación de alimentación y anuncio del modo DisplayPort por el monitor, sin activación ni salida DRM externa. La configuración original de LineageOS que incluye Apollo también desactiva `usb_qmp_dp_phy` y usa USB de alta velocidad con PHY secundario nulo: [fuente fijada](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/3a0fc935fe41b56669466a1ef17420d099c2eeb2/arch/arm64/boot/dts/vendor/qcom/xiaomi-sm8250-common.dtsi). Esto apunta a una limitación de la placa, pero no demuestra por sí solo su cableado físico. El cable tampoco se verificó por separado con otra fuente de vídeo. No se promete solucionar DisplayPort mediante software.

En kernel 23 quedan dos avisos SPMI. El fallo del PLL DSI y los dos avisos de relojes observados en kernel 22 desaparecen con el parche 0025, sin ocultar diagnósticos. Los avisos eliminados de WLED y APR se contrastaron en sus respectivas versiones. No se confunden avisos con una prueba de que el resto del sistema sea estable.
