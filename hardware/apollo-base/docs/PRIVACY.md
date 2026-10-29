# Revisión antes de publicar

La publicación se prepara en un directorio separado con lista de archivos permitidos; no se sube la carpeta de trabajo del teléfono ni su historial privado.

## Material excluido

- Copias de particiones, imágenes de sistema/arranque y archivos de firmware/calibración.
- EFS/NV, IMEI, números de serie, identificadores del procesador y plantillas de huellas.
- Claves SSH, claves de servidor, contraseñas y hashes de contraseñas, tokens y cookies.
- Perfiles WiFi, SSID/BSSID y credenciales de red.
- Coordenadas, NMEA, fotografías de las cámaras y registros originales del sistema.
- Rutas personales del ordenador, archivos de configuración del usuario e identidades del rootfs de pruebas.

Las fuentes se comprueban contra patrones de secretos y contra valores privados conocidos, sin mostrar esos valores. Se inspeccionan extensiones y contenido y se genera un manifiesto de archivos. Las capturas reales se revisan visualmente y se comprueba que no incluyan EXIF, ubicación ni datos personales en metadatos. Los únicos campos de texto de estas capturas son el nombre genérico de pantalla DSI-1 y su origen lógico 0,0.

Los resúmenes de pruebas se escriben a partir de hechos seleccionados; no son copias automáticas de JSON completos. Los informes originales pueden contener datos privados en campos anidados. `.gitignore` es una segunda protección; por sí solo no demuestra que un repositorio sea seguro.

Se conserva la autoría pública y los avisos de copyright de los proyectos originales. Las direcciones públicas de autores en parches no son credenciales del propietario del teléfono. La identidad pública de la cuenta GitHub que aloja el repositorio será visible.

## Para contribuir

No adjuntar informes completos ni una imagen del teléfono. Compartir versión, fallo, pasos y un extracto revisado. Ocultar identificadores de unidad, redes y ubicación. Los scripts de diagnóstico pueden generar datos privados al ejecutarse aunque sus fuentes sean públicas.
