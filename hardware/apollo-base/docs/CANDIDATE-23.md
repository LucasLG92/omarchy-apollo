# Kernel 23 / base r5: relojes y conexión USB

**Instalada y comprobada en la unidad: apollo-linux-test-2026.10.29-r5, linux-apollo 7.1.0-23.** Se probó primero un arranque temporal y después la instalación permanente. Tras reiniciar se verificaron el identificador del kernel en ejecución, el paquete y el hash de boot. Continúa siendo una base experimental, con las limitaciones de [STATUS.md](STATUS.md).

## Relojes de pantalla

Los registros anteriores de Apollo muestran un fallo al activar el PLL DSI durante el registro del proveedor de relojes, seguido de dos avisos de referencias desequilibradas en `__clk_set_parent_after()`. Una prueba con el framework real de relojes reproduce ese recorrido cuando se registra un padre que falla al prepararse, cuyo hijo huérfano aún no estaba preparado.

El parche `0025` evita activar temporalmente el padre para adoptar un hijo sin referencias de preparación: actualiza la topología bajo el bloqueo existente. Los relojes que ya están preparados conservan el recorrido de migración anterior. El parche no cambia frecuencias, voltajes, registros del PLL ni las restricciones de seguridad del kernel. No elimina avisos ni ignora errores del controlador.

Pruebas ejecutadas con un kernel User Mode Linux y el CCF real:

- Antes del cambio: dos pruebas fallan y reproducen los dos avisos; la migración de referencias de un reloj activo pasa.
- Después: las tres pruebas pasan.
- Conjunto de relojes habilitado en `drivers/clk/.kunitconfig`: 117 pruebas pasan y cuatro se omiten por limitaciones ya indicadas en sus pruebas originales. No se afirma que todos los relojes de Apollo estén probados.

En Apollo, tanto en el arranque temporal como en el permanente, desaparecen el fallo del PLL y los dos avisos de relojes. DSI continúa a 1080×2400/144 Hz. Los dos relojes observados conservan una referencia de preparación y activación y una frecuencia de 160917041 Hz. **Permanecen dos avisos SPMI**; no se han eliminado ni corregido con este parche.

Referencias: [CCF y sus reglas de preparación](https://docs.kernel.org/driver-api/clk.html) y la fuente original del kernel fijada en [BUILD.md](BUILD.md). El parche incluye las pruebas KUnit; no se habilitan en la configuración del kernel del teléfono.

## Conexión USB después de cambiar de raíz

El initramfs de r4 inicia la configuración del gadget en segundo plano y después mueve `/sys` y `/run` a la raíz definitiva. Si el controlador llega tarde, ese proceso puede seguir buscando en rutas que ya se han movido. Es un fallo de orden observado en las fuentes; no demuestra por sí solo la causa de una desconexión física concreta.

R5 elimina ese proceso del initramfs y usa:

- `apollo-usb-gadget.py`, instalado como `/usr/local/sbin/apollo-usb-gadget`.
- `apollo-usb-gadget.service`, iniciado después del montaje de configfs.
- `70-apollo-usb-gadget.rules`, que vuelve a solicitar el servicio al aparecer el controlador.
- Las políticas de networkd y NetworkManager seleccionadas por la dirección local fija del gadget, en lugar de depender del nombre `usb0`.

El servicio conserva un gadget compatible que ya está conectado: no lo desconecta ni reescribe sus atributos. Rechaza configuraciones ajenas y controladores ocupados. Cuando no hay controlador termina sin sondeo periódico; el evento del controlador inicia otro intento. Los fallos transitorios de configuración se reintentan con una espera, sin condicionar el arranque del escritorio a un PC.

Doce pruebas con un sistema de archivos simulado comprueban registro tardío, repetición sin escrituras, reintento tras un fallo de enlace, conservación de configuraciones ajenas y rechazo de ambigüedades. La comprobación nativa detectó USB 2.01 tras activar LPM y un NUL final en las direcciones NCM; se añadieron sus regresiones, manteniendo estrictas las identidades esperadas. Las simulaciones son pruebas de software; no validan la negociación USB-C ni el controlador físico. La referencia de la interfaz es la [documentación de gadgets del kernel](https://docs.kernel.org/usb/gadget_configfs.html).

La unidad y la regla udev pasan `systemd-analyze verify` y `udevadm verify` en el rootfs de construcción aarch64 bajo emulación. También se instalaron y ejecutaron correctamente en el teléfono. La compilación ARM64 conserva exactamente la configuración y el DTB de kernel 22. El paquete pasa su comprobación de integridad tanto en el entorno de construcción como en la instalación nativa.

En la raíz que se vaya a usar deben existir estos archivos:

| Fuente | Destino | Modo |
| --- | --- | --- |
| `system/apollo-usb-gadget.py` | `/usr/local/sbin/apollo-usb-gadget` | 0755 |
| `system/apollo-usb-gadget.service` | `/usr/lib/systemd/system/apollo-usb-gadget.service` | 0644 |
| `system/70-apollo-usb-gadget.rules` | `/usr/lib/udev/rules.d/70-apollo-usb-gadget.rules` | 0644 |
| `system/20-apollo-usb.network` | `/etc/systemd/network/20-apollo-usb.network` | 0644 |
| `system/20-apollo-usb-unmanaged.conf` | `/etc/NetworkManager/conf.d/20-apollo-usb-unmanaged.conf` | 0644 |

Habilitar la unidad en esa raíz antes de construir/usar el nuevo boot. En un sistema ya iniciado, recargar systemd y udev después de instalar las fuentes. La orden del auxiliar es `apollo-usb-gadget ensure`; no ofrece una orden de desconexión. El servicio DHCP y SSH conservan la política de mantenimiento existente. Las direcciones del gadget son locales y genéricas, no identificadores WiFi del propietario.

**Antes de arrancar la nueva imagen** hay que instalar y verificar el auxiliar, la unidad, la regla udev y las dos políticas de red en la raíz persistente, y habilitar `apollo-usb-gadget.service`. El initramfs nuevo depende de esa integración para el mantenimiento por USB. Conservar la pareja de recuperación de kernel 22 y comprobar el modelo, el boot actual, el estado de la batería y la geometría antes de cualquier escritura de boot. No volver a formatear `userdata`.

Se comprobó la adopción de la conexión de r4 sin interrupción, la creación del gadget después de cambiar de raíz, DHCP/SSH después de reiniciar y el retorno de USB tras suspensión. El propietario realizó una desconexión/reconexión física y confirmó el encendido de r5 sin cable hasta el escritorio. Tras reconectar al PC se cotejaron un identificador de arranque nuevo, kernel/paquete/boot y datos persistentes; USB/SSH estaban disponibles sin intervención manual. Faltan más repeticiones y cambios de rol. Estos cambios no implementan DisplayPort.

## Regresiones nativas y límites

| Prueba | Resultado de kernel 23 |
| --- | --- |
| GPU | Ventana Vulkan/Wayland de 120 fotogramas en Turnip Adreno 650 antes y después de reposo; nueva ejecución tras instalar. EGL/Wayland con freedreno FD650 y GLES 3.2 |
| Cámaras | Las cuatro entregan 90 fotogramas cada una como usuario de escritorio, antes y después de reposo, y en otra tanda tras el arranque permanente. Buffers descartados |
| Enfoque | 100 ciclos de control antes y 40 después de reposo, cinco valores por apertura, alimentación recuperada en la prueba aislada. Falta comprobar enfoque óptico y AF en una aplicación |
| Frontal | 24 ciclos adicionales de apagado/apertura tras reposo, cinco fotogramas por ciclo; ajustes temporales restaurados |
| Suspensión | Un ciclo s2idle con alarma RTC: unos 13 segundos, mismo arranque, reanudación y USB/SSH recuperados sin reiniciar servicios; cero avisos nuevos |
| Brillo | 12 rondas, cambios rápidos y blank/unblank con lectura de hardware; preferencias y PowerDevil restaurados |
| WiFi | Petición HTTPS ligada a WiFi a 5200 MHz, certificado comprobado |
| Instalación | Paquete e imagen de boot comprobados, identidad y claves conservadas, escritorio/teclado/red/audio/módem activos; Landlock ABI 9 y Zstd seleccionados |

El ensayo inicial de reposo del enfoque se detuvo sin ejecutar ciclos porque WirePlumber mantenía abiertos dispositivos de cámara y dos referencias de alimentación. Se identificó el proceso mediante sus descriptores. Para medir ciclos físicos aislados se pausó **temporalmente** WirePlumber; PipeWire y el servicio compatible con PulseAudio siguieron activos. WirePlumber se restauró al terminar cada ensayo. Las capturas normales se hicieron con el escritorio completo activo. El efecto de esos observadores de cámara sobre el consumo necesita medirse; no se presenta una autonomía mejorada ni una solución de consumo ya demostrada. En la prueba de frontal, CCI se mantuvo activo temporalmente para aislar los ciclos del sensor y se restauró al terminar.

La tanda no mide calidad óptica, colores, resolución máxima, consumo prolongado ni todos los periféricos. Huellas, SIM, USB-C de vídeo y los demás pendientes conservan sus límites documentados.

## Actualización recuperable de esta transición

`system/update-kernel22-to23.py` sirve solo para esta transición. Requiere los cuatro artefactos privados y sus hashes, la integración USB cotejada, el modelo exacto, el kernel temporal 23 en ejecución y un boot 22 conocido leído dos veces. Comprueba batería, tamaño/bloqueo exclusivo de boot y evidencia de pruebas del mismo arranque antes de aplicar. No es un instalador universal ni reconstruye las entradas privadas ausentes.

Conserva una copia privada de **toda** la partición boot, instala el paquete, escribe únicamente la nueva imagen en boot y comprueba la lectura. Ante un fallo restaura la partición completa, incluida su cola, y solicita restaurar el paquete anterior. Siete pruebas con archivos propios simulan escritura parcial, lectura corrupta, fallo de paquete y entradas inválidas; no son inyección de fallos eléctricos en el teléfono. La actualización real pasó preflight y comprobación posterior, sin formatear `userdata` ni cambiar DTBO. No se garantiza recuperación automática frente a una pérdida física de alimentación durante una escritura.

Las imágenes, paquetes, copias completas y resultados originales permanecen privados. Otra construcción debe generar sus artefactos y repetir las validaciones; los hashes de la unidad ensayada no se convierten en los de cualquier reconstrucción.
