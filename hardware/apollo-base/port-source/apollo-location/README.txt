Localización nativa para Xiaomi Apollo

GeoClue usa el receptor GNSS real mediante ModemManager. La preparación se
activa cuando arranca GeoClue: habilita el motor LOC, aporta la hora del
sistema y selecciona funcionamiento autónomo. No inyecta posiciones ni
inicia una sesión de seguimiento; esas sesiones corresponden a las peticiones
de aplicaciones y a sus permisos. El estado se vuelve a preparar tras parar
y volver a arrancar ModemManager.

La hora del sistema debe ser correcta. La imagen conserva una fecha mínima
de construcción y ejecuta systemd-timesyncd; se debe verificar su sincronización
con Internet para el arranque sin ordenador. La calibración RTC no se modifica.

Se incluye libnotify como dependencia porque el agente de permisos de GeoClue
instalado para KDE necesita esa biblioteca. No se añade una autorización global
de aplicaciones. El agente y las reglas originales de GeoClue permanecen activos.

Esta receta requiere las correcciones de descubrimiento LOC de apollo-modem
1.0-4 y de indicaciones NMEA de modemmanager-apollo 1.24.2.r1-2.
La integración de esta nueva preparación automática necesita prueba nativa;
las mismas tres operaciones sí han funcionado en la prueba de diagnóstico.

SPDX-License-Identifier: GPL-2.0-only
