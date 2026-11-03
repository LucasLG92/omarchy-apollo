<p align="center"><img src="../../media/hero.svg" alt="Omarchy Apollo: Linux nativo adaptado al móvil" width="100%"></p>

# Omarchy Apollo

**Omarchy nativo en el Xiaomi Mi 10T Pro (`apollo`), instalado en la memoria interna.** Proyecto comunitario independiente y experimental, probado en una unidad Pro.
[English](../../README.md) · [Galería](../gallery.md) · [Estado completo](../status.md).

**Actualizado el 3 de noviembre de 2026:** Linux **7.3.1 R14**, Omarchy 4.5 RC2,
Hyprland 0.57.0-2.4 y shell29. El escritorio, las correcciones de repintado y el
nuevo cambio de orientación están instalados. [Último hito y pruebas](../milestone-2026-11-03.md).

**Nuevo checkpoint de código:** base mínima con Web/Epiphany y Bazaar, asistente de primera cuenta y actualizador transaccional con el mismo kernel. Han pasado **66 comprobaciones pequeñas, seis arranques ARM64 virtuales y una preparación aislada real en el móvil**. El nuevo selector de arranque todavía no se ha probado físicamente ni activado. [Código, resultados y límites](../checkpoint-2026-11-03.md) · [Lista de pruebas pendientes](../pruebas-pendientes.md).

## Capturas del Apollo

<p align="center"><a href="../../media/apollo-home-portrait-r33.png"><img src="../../media/apollo-home-portrait-r33.png" width="245" alt="Inicio real del Apollo en vertical con reloj e iconos"></a></p>

<p align="center"><a href="../../media/apollo-home-landscape-r33.png"><img src="../../media/apollo-home-landscape-r33.png" width="880" alt="Inicio real del Apollo en horizontal con las barras compactas"></a></p>

Son capturas del móvil anteriores a la limpieza posterior de apps, no maquetas. El inventario de aplicaciones ya ha cambiado. La SIM estaba retirada. Los iconos indican
aplicaciones instaladas; no certifican su hardware. La [galería](../gallery.md)
incluye Teléfono y Recientes, con datos desechables y sin números ni contactos.

## Lo que ya se ha comprobado

- **Arranque nativo y acceso local:** raíz ext4 interna, systemd y sesión del
  propietario. El acceso y la administración autenticada se han probado; el alta
  de una primera cuenta en una instalación limpia sigue pendiente de aceptación completa.
- **Inicio táctil y gestos:** reloj, iconos, buscador, deslizar para Inicio,
  mantener para Recientes y cerrar el teclado. La vuelta a Inicio al cerrar
  la última app tuvo confirmación humana en una prueba anterior.
- **Corrección permanente de los recortes:** el usuario confirmó que la interfaz
  vuelve a verse completa. Tras recargar la sesión, una app GTK pasó de
  960×372 a 960×192 al abrir el teclado y recuperó 960×372 al cerrarlo.
  No se modificaron fuentes, zoom ni escala de pantalla.
- **Giro con el fotograma preparado:** se conserva la imagen anterior hasta
  componer la nueva. Cuatro cambios medidos tardaron **0,50–0,68 segundos desde
  el inicio de la transacción**, aparte de la detección del sensor; las barras
  encajaron y el fondo no se recargó. No es una medida de todas las aplicaciones.
- **Recientes más estable:** se reprodujo el negro como un reinicio de la interfaz.
  La corrección pasó tres tandas de cinco ventanas desechables, conservando
  el proceso de la interfaz y sin recargar el fondo.
- **Refresco configurable:** 60, 90, 120 o 144 Hz, más el modo automático de
  90 Hz con batería y 144 Hz al cargar. Falta medir su efecto sostenido en consumo.

## Qué incorpora el kernel 7.3.1 R14

La base oficial tiene su firma verificada y se ha portado el soporte de Apollo,
con **502 módulos**. Incluye ThinLTO conservando el enlace ARM64 normal,
adaptaciones de panel, cámara y firmware, y una política de carga que sigue
el presupuesto USB-C/PD manteniendo las protecciones térmicas y AICL.

Se conservan EAS/schedutil y las frecuencias de fábrica. La GPU usa aceleración
MSM/EGL y puede suspenderse entre actividades. MGLRU está activo; zram admite
LZO-RLE, LZ4 y Zstd, manteniendo LZO-RLE al arrancar. Landlock ABI 11 está verificado.
Pasaron **3.341 casos de carga** y **646 comprobaciones del árbol de dispositivos**.

**No hay un porcentaje demostrado de ahorro de batería ni de mejora global de
velocidad.** No se ha aplicado overclock, undervolt ni retirada de límites térmicos.
[Detalle, procedencia y límites del kernel](../kernel-7.3.1.md).

## Funciones y pendientes

| Apartado | Resultado disponible | Pendiente |
| --- | --- | --- |
| Pantalla, GPU y táctil | Escritorio acelerado, gestos y comprobaciones de giro/área útil | Más apps, reinicios y sesiones largas |
| Wi-Fi | Conexión y HTTPS comprobados con R14 | Ambas bandas, reconexión y suspensión |
| Cámaras | Capturas anteriores de los cuatro sensores; principal 3000×2256 y gran angular 4200×3120; controladores presentes en R14 | Calidad y vídeo en R14; **108 MP no disponible** con este controlador |
| SIM y datos | Continuidad del PIN y HTTPS IPv4 con perfil automático en pruebas anteriores de una red | No repetido con SIM en R14; otras redes, IPv6 y reconexión |
| Llamadas | GNOME Calls es el único marcador; antes se escuchó el buzón | **Manos libres sin resolver:** hubo distorsión y un reinicio posterior. Micrófono, entrantes, SMS y AEC pendientes |
| Sensores y vibración | Acelerómetro/luz y vibración AW8697 muy suave comprobados antes | Proximidad, intensidad e integración amplia |
| Apps nativas / investigación APK | Base actual con Web/Epiphany y Bazaar; **Android/Waydroid retirado**. Las pruebas anteriores se conservan como históricas | Revisar apps/servicios nativos; las APK no son binarios Linux nativos. No se promete WhatsApp nativo oficial ni Google Play |
| GPS y huella | Investigación y requisitos | GPS sin posición verificada; **captura de huella y desbloqueo no operativos** |
| Energía y carga apagado | Mecanismos de consumo y política de carga integrados | Autonomía, suspensión/despertar, apagado/conexión en frío y animación de carga con el sistema apagado |
| Bluetooth, NFC e IR | Detección previa de servicios/interfaces | Emparejar/audio, etiquetas NFC y emitir IR |

## Actualización y primera cuenta

El asistente preparado pide usuario administrador, contraseña o PIN y preferencias locales; no vuelve a crear la cuenta existente. Falta probar una imagen realmente limpia y su primer acceso SDDM/logind. El actualizador prepara conjuntos firmados y empareja archivos con ALPM; todavía no se ha arrancado ni instalado físicamente el nuevo initramfs, el conjunto inocuo no está encolado y la actualización automática del kernel sigue desactivada. [Resultados y fuentes](../checkpoint-2026-11-03.md) · [Próximas pruebas](../pruebas-pendientes.md).

## Código y colaboración

Hay fuentes seleccionadas, parches y pruebas saneadas. **El constructor público
completo de R14, la imagen genérica y el instalador de principio a fin siguen
pendientes.** La imagen de desarrollo tiene configuración del dispositivo y no
se distribuye. El Mi 10T normal necesita sus propias pruebas de cámara, memoria,
almacenamiento y calibración. [Compatibilidad](../compatibility.md).

[Hoja de ruta](../roadmap.md) · [Contribuir](../../CONTRIBUTING.md) ·
[Créditos/licencias](../../LICENSES/README.md) · [Privacidad](../../SECURITY.md).
Puedes dar una **estrella** para seguir los avances. Las pruebas reproducibles,
las revisiones y el trabajo en controladores son especialmente útiles.
