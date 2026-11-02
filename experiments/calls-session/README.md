# Calls graphical-session integration 0.1.0-2

Exact installed user unit for Calls' ordinary D-Bus activation. The upstream
service command, BusName, Type and restart behavior are preserved; PartOf,
Requisite, After and WantedBy use `graphical-session.target` instead of unavailable
GNOME-only targets. The earlier ineffective 0.1 drop-in is not published as current.

With Calls 51.1.apollo4-1 and shell 16, the normal mobile launcher/D-Bus cold path
opened the real application on its own workspace, without a manual move afterward.
This is activation/layout plumbing, not a new voice/audio test or physical
rotation acceptance. The [Calls source license](../../patches/phone-omarchy/COPYING-Calls)
applies to this adapted upstream unit. [Exact source pin](SOURCEPINS.json).
No installer, credential, live window metadata or diagnostic is included.
