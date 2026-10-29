# Pruebas realizadas

Los registros originales permanecen locales. Esta es una transcripción de resultados concretos revisada para publicación: no contiene números de serie, coordenadas, NMEA, redes WiFi, credenciales ni fotogramas de las cámaras. Los identificadores de tanda son marcas UTC, no identificadores del teléfono.

## Enfoque: fallo reproducido y correcciones

1. **Kernel 18, 20261029T053812Z**: trazado filtrado de escrituras I²C del motor AK7377. La orden de modo `02 00` recibe ACK; la siguiente escritura DAC `00 00 00` falla con NACK. La separación era prácticamente nula tras completar la orden anterior. El fallo no se atribuye ya a la propia orden de modo.
2. **Kernel 19, 20261029T054732Z**: parche 0022, espera de 1000 µs tras aceptar modo activo, solo para AK7377. 100/100 ciclos, 812 escrituras aceptadas, 103 pares modo→posición; mínimo medido de 1110 µs. Sin pérdidas en el trazado.
3. **Vuelta a kernel 18, 20261029T055228Z**: control negativo con la pareja anterior de imágenes. Se reproduce ACK de modo seguido por NACK de posición, con aproximadamente 1 µs de separación. La primera apertura normal falla.
4. **Kernel 19, 20261029T055617Z y 20261029T060403Z**: pasan otras dos tandas de 100 ciclos antes de suspender. Al reanudar, el controlador mantiene referencias de alimentación pese a figurar suspendido. Una prueba posterior se detiene antes de iniciar los ciclos porque los contadores no vuelven a cero durante 20 s. Estos resultados se conservan como fallos reales.
5. **Kernel 20, 20261029T063920Z**: parche 0023 sustituye las funciones directas de suspensión/reanudación por `pm_runtime_force_suspend`/`pm_runtime_force_resume`. Pasan 100/100 ciclos antes y 40/40 después de s2idle con alarma RTC. Contadores de L7/VIO a cero al principio y al final de ambas tandas; reguladores desactivados en reposo. No se limpian errores PM ni se reintentan aperturas fallidas para convertirlas en éxito.

Kernel 19 suma **300 ciclos previos al reposo** en tres arranques. Kernel 20 suma **140 ciclos** en esta tanda. No son 440 ciclos de kernel 20. La devolución de un control V4L2 no mide foco óptico. El algoritmo de AF por contraste ya existe en el parche comunitario de libcamera 0004; falta validar su resultado en aplicaciones con el motor corregido.

## Última tanda conjunta de kernel 20

Referencia: `20261029T063920Z`.

- Enfoque: 100 ciclos previos y 40 posteriores al reposo, con cinco posiciones por ciclo.
- Cámaras: 90 fotogramas de cada uno de los cuatro sensores a 640×480, descartados en memoria.
- Frontal: 24/24 aperturas adicionales después del reposo; ajustes temporales de la prueba restaurados.
- Clapper: decodificación por hardware, pausa, búsqueda, reanudación y cierre de ventana; patrón sintético sin sonido.
- Retorno al cargador y restauración de LineageOS; boot y DTBO cotejados con las copias originales por SHA256.
- Cuatro avisos conocidos, sin Oops y sin fallos I²C del motor en esta tanda.

SHA256 de aquella pareja, **no de la nueva candidata limpia**:

| Archivo | SHA256 |
| --- | --- |
| boot de prueba | `cfbae87f37dd45663209e37bad0af8ad7883c037c14d1986898857c425fdabff` |
| raíz SquashFS de prueba | `28394525deb1e8ea7dcb46a966b8324add4c2666ce38961176f6f98eb749fac2` |

## Pruebas anteriores con procedencia separada

| Versión/tanda | Prueba | Resultado y límite |
| --- | --- | --- |
| Kernel 12 | Seis clips H.264, HEVC y VP9, incluidos H.264/HEVC 4K, VP9 altref y H.264 720p/30 s | FFmpeg y GStreamer entregan 1110 fotogramas cada uno, iguales a referencias CPU. El tiempo incluye conversión y comparación; no prueba reproducción 4K en tiempo real |
| Kernel 12, seis arranques | Aperturas de frontal | 144/144; no prueba toda la calidad fotográfica |
| Kernel 13 y 14 | Clapper, reposo/RTC, frontal y WiFi | Vídeo/pause/seek/cierre, recuperación del escritorio, frontal 24/24 por tanda, Internet sobre WiFi |
| Kernel 14, 20261029T025931Z | Reloj, WiFi, ubicación y cámara | Sin reloj inyectado por PC, conserva fecha mínima de imagen y sincroniza por WiFi; GeoClue recibe datos del receptor |
| GNSS, tandas históricas | NMEA directo | 225 + 296 + 60 informes válidos, sin SIM. No son posiciones distintas ni una medida de exactitud topográfica |
| GeoClue, kernel 13 y 14 | D-Bus, libgeoclue y permisos | Posición contrastada con NMEA en memoria; app denegada no recibe posición. Coordenadas no guardadas. Estimación HDOP no equivale a exactitud real |
| Kernel 15, 20261029T032817Z | WLED | 12 rondas antes + 12 después, 96 peticiones verificadas con registros y apagado/encendido de iluminación |
| Kernel 16 | Memoria DMA APR | 24 clientes temporales, 72 reservas, 1944 páginas mapeadas/liberadas; fallos de conexión y reenlaces. Servicio real conectado, sin paquetes DSP ni audio. Variante módulo solo compilada |
| Recuperación del host | Protección de restauración | Diez replays sin hardware y comprobación real sin escritura; exige dos lecturas coincidentes de producto, tamaño y límite de descarga. No arregla el fallo UFS subyacente |
| Candidata limpia, 20261029T073051Z | KDE/SSH/teclado y preflight del instalador | Arranque RAM, servicios SDDM/SSH activos, proceso plasma-keyboard activo, modelo/particiones comprobados y cero escrituras solicitadas. Capturas de escritorio y Konsole. La configuración final puede cambiar después |

## Instalación interna r2 y pruebas posteriores

- Transacción real: base copiada y verificada; un único formateo autorizado de userdata. El resto de particiones de recuperación y calibración se conserva.
- Primer boot permanente: panic reproducido por el montaje de `/dev/pts` en orden incorrecto. Reparación de initramfs, escritura de solo boot y comprobación de lectura; sin repetir el borrado.
- Reinicios: archivo de usuario, identidad del sistema y clave de servidor iguales; identificador de arranque distinto. Contraseña configurada y asistente inicial retirado. KDE, teclado, WiFi y servicios de audio activos.
- Encendido físico: propietario confirma Linux sin cable; tras reconectar, mismos datos persistentes, nuevo arranque y WiFi conectado automáticamente.
- Audio: se retiraron las máscaras de PipeWire/pulse/WirePlumber; servicios activos también después de reiniciar. Salida silenciada al 25 %, sin sonido de prueba. No equivale a comprobar todas las rutas de audio.
- USB-C/monitor: cinco cambios de estado registrados. El monitor anuncia DisplayPort (`ff01`) pero el modo permanece inactivo. Solo aparecen DSI y Writeback; Writeback no es una salida externa. El propietario no vio imagen. Tras volver al PC se recuperó SSH sin otro reinicio manual del servicio. No se registraron píxeles, EDID ni números de serie USB.
- Huella instalada, prueba sin intervención coordinada: firmware cargado e inicialización y espera de dedo aceptadas; ventana de 100 s sin cambio del contador de interrupciones. No demuestra una prueba física de contacto ni desbloqueo funcional. Registro/comparación no implementados.

## Kernel 21: memoria comprimida y contacto FPC

- Paquete y boot actualizados como pareja; lectura de boot cotejada con el manifiesto y archivo/identidad/claves conservados al reiniciar.
- Zram: el kernel anterior usaba LZO-RLE porque faltaba el backend Zstd solicitado por la configuración. Con kernel 21 se seleccionó Zstd al arrancar. Se paginaron 64 MiB de datos sintéticos del propio proceso a zram y se recuperaron con el mismo hash. No se reseteó el swap ni se creó presión global de memoria; no es una medición de rendimiento real.
- Huella, tanda `20261029T104322Z`: espera ampliada a 300 s, usuario retira y apoya el dedo sin pulsar el botón. Contador de interrupciones 197→198 y `detected=1`. Liberación aceptada y alimentación a cero al terminar. Esta prueba demuestra contacto, no identidad.
- La consulta de dimensiones sigue devolviendo error de parámetro. No se ejecutaron registro, comparación, captura de imagen, exportación de plantillas ni desbloqueo.
- El helper rechaza duraciones fuera de 30–600 s antes de acceder al hardware. La prueba local queda accesible desde el menú del móvil y conserva sus informes solo allí.

## Kernel 22 / base r4: arranque, seguridad y escritorio

- El árbol de Apollo no definía modos de reinicio para qcom-pon: una orden de bootloader volvía a Linux. Parche 0024 añade el valor 2 de bootloader; configuración de hardware restante sin cambios.
- El gestor de paquetes rechazaba descargar porque faltaba Landlock. Se habilitan Landlock y sus dependencias Kconfig de seguridad de red/rutas; SELinux continúa desactivado. Lista de LSM ya incluía Landlock.
- Compilación y paquete: 529 archivos comprobados, cero alterados. Actualización de solo boot con copia de recuperación, dos lecturas del hash anterior, escritura/sincronización y comprobación del nuevo hash. La base y los datos no se formatearon.
- Arranque realmente distinto confirmado por identificador, además de la versión de paquete; persistencia y escritorio comprobados. Landlock ABI 9 observado. Una prueba **sin privilegios**, limitada a un proceso hijo y archivos sintéticos, permite leer el archivo autorizado y deniega el otro con EACCES. No aplica políticas a otras aplicaciones.
- Reinicio ordenado con argumento bootloader: el PC detecta FASTBOOT Apollo, solicita vuelta normal y Linux inicia otra vez. Sin pulsaciones físicas ni escritura de particiones durante esta prueba de transición. La incidencia UFS de fastboot conserva sus protecciones y sigue abierta.
- Repositorio: las referencias antiguas de `plasma-nm`/`kscreen` 6.8.1 dieron 404. Se obtuvieron siete paquetes concretos del repositorio oficial vigente, con SHA256, firmas PGP, dependencias e integridad comprobados. No se cambió la base global de sincronización ni los paquetes de cámara/kernel para resolver el escritorio.
- WiFi: icono y lista de redes confirmados por el propietario. Escaneo con ambas bandas; conexión real a 5200 MHz antes y después de HTTPS a kernel.org, certificado verificado y petición ligada a WiFi. SSID/BSSID no se guardaron. Redes con el mismo nombre pueden existir en ambas bandas.
- Pantalla: escala 2,55→2,25, ancho lógico 424→480; menú de aplicaciones compacto, panel superior de 48 puntos y teclado accesible. Controles del tema ampliados y ventanas nuevas maximizadas; ventana real de Konsole revisada visualmente con título legible. Hay copia privada de la configuración anterior.
- Tras reiniciar r4, se mantienen servicios, configuración y selector WiFi; el módulo de redes del escritorio se carga automáticamente. La captura de estado muestra datos reales y los fallos pendientes, sin identificadores de red.
- Región: la petición estándar cambia el dominio global, pero el firmware WiFi autogestionado conserva otro dominio. Aplicar correctamente el país seleccionado a ese firmware sigue pendiente. No se forzaron canales, potencia ni una banda adicional.

## Kernel 23 / base r5: relojes y USB

- KUnit real del CCF: antes del parche 0025 fallan dos casos y pasa uno; después pasan los tres. El conjunto de relojes habilitado termina con 117 casos correctos y cuatro omisiones conocidas.
- Nativo: arranque temporal y luego permanente con identificador de compilación cotejado. Paquete e imagen de boot comprobados tras reiniciar. El fallo del PLL y dos avisos de relojes desaparecen; permanecen dos avisos SPMI.
- DSI 1080×2400/144 Hz; Vulkan/Wayland renderiza una ventana de 120 fotogramas antes y después de reposo y tras instalar. EGL usa freedreno FD650/GLES 3.2.
- Cuatro cámaras: 90 fotogramas por sensor antes/después de reposo y en otra tanda tras el arranque permanente, usando el usuario del escritorio y sin guardar imágenes.
- Enfoque 100/100 antes y 40/40 después; frontal 24/24 ciclos tras reposo, cinco fotogramas por ciclo. Las pruebas de apagado físico de cámara/foco pausan temporalmente WirePlumber para liberar observadores; PipeWire/pulse siguen activos y WirePlumber se restaura. El ensayo inicial con observadores activos se detuvo a cero ciclos y no se cuenta como una prueba de reposo superada.
- RTC: un s2idle de unos 13 segundos, mismo arranque, USB/SSH recuperados sin reinicio manual y sin avisos nuevos. No equivale a suspensión prolongada ni a encendido físico sin cable.
- Brillo: 12 rondas, cancelación rápida y blank/unblank; lecturas de hardware y ajustes restaurados. WiFi a 5200 MHz con HTTPS/TLS comprobados.
- USB: adopción de un gadget conectado sin escrituras, servicio después de cambiar de raíz y comprobación de DHCP/SSH en el nuevo arranque. Doce casos simulados y comprobaciones systemd/udev pasan. Se añadieron los detalles nativos de LPM USB 2.01 y NUL final en direcciones NCM.
- Prueba física de r5: propietario confirma desconexión/reconexión y, después, apagado y encendido hasta el escritorio sin cable. Tras reconectar se comprueban un arranque distinto, persistencia, kernel 23, paquete/boot y servicios de escritorio/audio/red. USB/SSH disponibles sin reiniciar servicios manualmente. Es una prueba fría, no una campaña de duración.
- Actualizador 22→23: siete pruebas de archivos propios, incluida escritura parcial, corrupción de lectura y restauración de toda la partición simulada. En el teléfono se verifican preflight, copia completa privada, escritura/lectura de boot y paquete, sin formateo ni cambios en DTBO.
- Detalles, condiciones de aislamiento y pendientes: [kernel 23 / r5](CANDIDATE-23.md). No se atribuyen a esta tanda pruebas nuevas de huella, telefonía con SIM, enfoque óptico ni DisplayPort.

## Cómo repetir sin filtrar datos

Los scripts de `port-source/apollo-hardware-tests` guardan resultados en `/run/apollo-audit`. Revisar qué hace cada fase antes de ejecutarla: algunas cambian brillo, suspensión o servicios. Las pruebas de audio no deben ejecutarse durante trabajo silencioso. Mantener los resultados originales fuera de Git.

Para cámara, usar captura a descarte y no exportar imágenes del entorno. Para GNSS, comparar en memoria y exportar únicamente un resultado booleano y conteos. Para WiFi, facilitar un perfil privado local con permisos 0600 y publicar solo DNS/TLS/ruta verificados, nunca SSID, BSSID ni claves. Los informes genéricos del sistema pueden contener identificadores incluso cuando una prueba concreta no los registra.
