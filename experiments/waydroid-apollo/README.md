# APK con icono y ventana propios en Omarchy Apollo

Waydroid 1.6.3.apollo2-1 y perfil 1.0.0-6 están instalados y verificados por firmasALPM normales/Qkk. El cierre normal y posterior lanzamiento desde el icono individual de F-Droid arrancaron una sesión Android en segundo plano, con su proceso y ventana960x372. No apareció ninguna superficie Android Home/Waydroid genérica; Name/Icon/StartupWMClass del icono permanecieron byteidénticos. No se reinstalaron APK ni imágenes y no se repitieron pruebasGPU/API/red.

La integración usa CPU ARM64 y GPU reales mediante un contenedor Android. Las APK no se convierten en binarios Linux. Cada APK conserva su icono y ventana en el launcher de Omarchy, sin pasar por un escritorio Android. El icono genérico se oculta con NoDisplay; «Cerrar Android» sigue disponible y los gestos normales no apagan todo el runtime.

Cambios mínimos: una condición en app_manager para arranque background de app/intent; dos cachés Python ARM64 checked-hash correspondientes; NoDisplay en el escritorio genérico. El helperAPK inicia `waydroid session start` en segundo plano. El generador de escritorios individuales, sus nombres/iconos/clases, las 14fuentes del perfil, permisosGIO0755, hintsdeorientación y hardening se conservan salvo el helper indicado.

El ciclo final con rotation 0.3.1-2/Shell 20 mantuvo Inicio vacío al girar en ambos
sentidos con una ventana F-Droid en segundo plano. Reabrir la app canceló el guard
real y abrió la ventana normalmente. Es una prueba concreta, no garantía para toda
APK/proceso/superficie. Las barras pasaron el ciclo automático; la prueba física
posterior a 19 sigue pendiente. [Alcance final](../../docs/mobile-layout-android-2026-11-02.md).

Se incluyen 14fuentes exactas del perfil, las 3fuentesPython Waydroid modificadas, el escritorio genérico y un parche contra el paqueteoficial1.6.3. LicenciasMIT/GPL conservadas. No se incluyen imágenes, APK, pyc binarios, logs, cuentas o identificadores. Los dos pyc nuevos se generaron sólo enHOST con Python ARM64 oficial 3.14.9; no existe emulaciónCPU en el móvil.

VANILLA no contiene GooglePlay/GMS; siguen sin garantizarse PlayIntegrity, banca/DRM, otrasABI/API, cámara/micrófono/GPSAndroid o consumo. El proveedor de orientación usa metadata de la actividad principal; orientación dinámica/BEHIND/NOSENSOR/LOCKED conserva limitaciones documentadas en final-result.json.

Fuentes: [uso oficial de apps](https://docs.waydro.id/usage/install-and-run-android-applications), [opciones multiwindow](https://docs.waydro.id/usage/waydroid-prop-options), [código oficial](https://github.com/waydroid/waydroid/tree/1.6.3).

## Alcance público y permisos

SOURCEPINS identifica los 14payloads del perfil, 3fuentes Python Waydroid y el
escritorio genérico. Los avisos originales Copyright/SPDX se conservan: GPL3+
para Waydroid y MIT para el perfil móvil/Apollo. Sólo se exportan fuentes,
licencias y pins; no paquetes, firmas, APK, imágenes, pyc, inventarios vivos,
políticas generadas ni registros privados. Los hashes de imágenes corresponden
a imágenes oficiales públicas, nunca a particiones o datos de una unidad.

La política de dispositivos no concede bloques. La regla específica c1:11 wm no
concede lectura; no demuestra aislamiento global de kmsg frente a root. Los
comentarios heredados CSIS/Pixel/Mali no describen Apollo: MSM/Freedreno es la
ruta usada, sin el adapter Pixel/Mali. [Resultado saneado](../../docs/evidence/2026-11-02-android-runtime-apk.json).
