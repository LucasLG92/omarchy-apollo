# Omarchy Apollo

**Omarchy nativo en el Xiaomi Mi 10T Pro (`apollo`), con interfaz táctil y resultados verificables.** Un escritorio Linux en formato móvil, con Hyprland, Quickshell y la GPU Adreno 650.

[English / portada](../../README.md) · [Estado completo](../status.md) · [Pruebas recientes](../validation-2026-11-01.md) · [Hoja de ruta](../roadmap.md)

<p align="center"><img src="../../media/hero.svg" width="100%" alt="Omarchy Apollo: Linux nativo adaptado a un teléfono"></p>

## Estado actual: 4.5 RC2 en RAM

La nueva base **Omarchy 4.5 RC2** se ha probado de forma nativa en el teléfono, con Linux ARM64 y systemd como PID 1. Android no actúa como anfitrión. Son sesiones temporales en RAM: al terminar se restaura el DTBO original, se vuelve a Android y se comprueban los hashes de las particiones de arranque.

**La instalación permanente de esta nueva base sigue pendiente. No es todavía un móvil plenamente funcional ni existe un instalador público validado.** La instalación y las pruebas de Waydroid del 30 de octubre pertenecen a una [etapa anterior](../history/README-2026-10-30.md); no demuestran esas funciones en la nueva base.

<p align="center"><a href="../../media/apollo-home-r11.png"><img src="../../media/apollo-home-r11.png" width="245" alt="Captura real del inicio de la sesión R11, sin el aviso de PIN"></a></p>

## Avances comprobados

- Escritorio nativo con renderizado **Freedreno FD650**, entrada táctil, aplicaciones y teclado en pantalla.
- Las cuatro cámaras entregan imágenes de 640×480. La principal capturó 24 imágenes RGB de **3000×2256** y la ultra gran angular otras 24 de **4200×3120**.
- La reserva de memoria contigua pasó de 32 a **256 MiB**, resolviendo el fallo de asignación DMA de la principal.
- La sesión local normal puede consultar llamadas sin el aviso de PIN al iniciar. Administración del servicio y cambios de firmware siguen requiriendo autenticación de administrador.
- Se han comprobado el encendido/apagado de la linterna desde la sesión normal y el cierre/reinicio del servicio EFS del módem. Falta confirmar visualmente la luz y probar una transferencia EFS real.
- Los últimos retornos a Android y las lecturas de `boot` y DTBO coinciden con las copias originales. No se ha formateado `userdata` en estas pruebas.

## Lo que falta

No hay una SIM de pruebas: **no están verificadas las llamadas reales, SMS, datos ni audio de llamada**. La conexión Wi-Fi y el emparejamiento Bluetooth también siguen pendientes. La detección del adaptador NFC no demuestra todavía lectura de etiquetas.

Quedan GPS, huella, proximidad, vibración e infrarrojos, además de suspensión, autonomía, primer PIN definitivo, arranque independiente de la nueva base y actualizaciones coherentes. El controlador de la principal **no ofrece 108 MP**. Las capturas prueban el transporte de imágenes; calidad, color, enfoque óptico, vídeo y giro necesitan más pruebas.

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
