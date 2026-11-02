# Omarchy Phone: source delta and visual checks

Installed and human-accepted on the development phone as **GNOME Calls
51.1.apollo3-1**. These are source inputs, not a package or phone installer.

Start with the [GNOME Calls 51.1 release](https://download.gnome.org/sources/calls/51/),
verify the [source checksum](SOURCEPINS.json), then apply the four patches in the
listed order. Copy the unchanged `omarchy-logo.png` to `src/omarchy-logo.png`
before patch 4. After patch 4, copy `phone-style.css` to `src/style.css`: this
preserves the exact reviewed CRLF source bytes, which the textual diff normalizes.
Keep the existing Apollo build/provider integration; this directory is not a
complete replacement packaging recipe.

The main window uses the original Omarchy logo, framed controls, readable mono
digits, three navigation tabs and a mobile portrait/landscape layout. The logo
is not redrawn or recolored. GTK palette integration is separate; the previews
use public Tokyo Night CSS in an empty fixture home. The three previous patches
are retained exactly, including private-by-default logging. The latest UI delta
changes ten UI/CSS/resource paths; 197 C/header/provider source paths remain
identical. The installed package preserved unrelated provider binaries and data.

Full **real application** fixtures used a dummy provider, isolated bus and empty
home at 432×960, 432×520, 800×360 and 360×756. All 12 keys, three navigation
targets, entry/delete and call control fit; targets were at least 44 pixels.
The menu measured 44×53 and original logo 112×26. Input roundtrip/IME checks
passed, with zero dial signals and zero GTK/CSS/template warnings. These are
host fixtures, not calls made on a device. Human acceptance after normal reboot
later confirmed the installed main screen.

![Synthetic full-window landscape preview](../../media/phone-landscape-fixture.png)

The active-call, account and DTMF screens were not exercised by these fixtures.
The earlier outgoing/downlink result remains separate; microphone, incoming calls
and SMS are still unverified. No performance or battery improvement is measured.

Calls-derived UI/style/resources remain **GPL-3.0-or-later**; libcall-ui UI/style
remain **LGPL-2.1-or-later**. The additional style/script notice does not relicense
either upstream. The unmodified Omarchy logo retains **David Heinemeier Hansson's
MIT notice**. See the included licenses and [file-scope attribution](../../LICENSES/README.md).
