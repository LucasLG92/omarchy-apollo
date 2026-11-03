# Media provenance

## Current R14 / shell29 handset gallery — 3 November 2026

| File | Source and scope |
| --- | --- |
| `apollo-home-portrait-r33.png` | Actual 1080×2400 Apollo Home, current native session, manually reviewed. Only clock, stock shortcuts, wallpaper and generic status visible. |
| `apollo-home-landscape-r33.png` | Actual 2400×1080 Apollo Home after a native rotation transaction. A settled-layout capture, not a rotation-speed benchmark. |
| `apollo-calls-r33.png` | Actual 1080×2400 handset GNOME Calls window with disposable config/history and dummy provider. No call, account, contact or number; not audio acceptance. |
| `apollo-recents-r33.png` | Actual 2400×1080 handset overview of owned disposable Calculator and Calls windows. No personal app data; closing stability has a separate recorded test. |

These four PNGs are retained as captured, with no UI retouching. They were
manually reviewed and checked for absent text/EXIF chunks before publication.
The SIM was removed; “No SIM” is expected. No account/network names, credentials,
biometrics, subscriber identifiers, private notifications or conversations are
published. [Gallery and limits](../docs/gallery.md) ·
[Dimensions/hashes and evidence](../docs/evidence/2026-11-03-r14-ui.json).

Application/UI, wallpaper and icon authors retain their licenses; the original
Omarchy wordmark retains its DHH MIT attribution. The project MIT license does
not relicense all screenshot contents. No separate wallpaper file is exported.

## Historical media

| File | Origin and scope |
| --- | --- |
| `phone-portrait-fixture.png`, `phone-landscape-fixture.png` | Real GNOME Calls full-window HOST fixtures, empty synthetic data/dummy provider, manually reviewed. No phone capture or real account/number. UI keeps Calls GPL-3.0-or-later / libcall-ui LGPL-2.1-or-later; original Omarchy logo remains DHH MIT. Successful human phone acceptance is recorded separately. |
| `hero.svg` | Original vector illustration made for this project. MIT licensed. It is not a screenshot or evidence of hardware functionality. |
| `r20-root.svg` | Original MIT status badge: R20 native installation and normal boot verified on one Pro unit; it does not mark complete phone acceptance. It is an illustration, not a screenshot. |
| `r19-call.svg` | Original MIT status badge summarizing one manually dialed outgoing call and audible downlink in R19. It does not mark all telephony as complete. |
| `apollo-home-r11.png` | Actual home-screen capture from the supervised 2026-11-01 R11 RAM trial. Reviewed for identifiers, notifications and personal content; PNG contains no metadata fields. No entered PIN or camera photograph is shown. |
| `omarchy-desktop.png`, `mobile-apps.png`, `touch-lock-preview.png` | Earlier already-published 2026-10-30 captures. Historical only; the empty lock preview does not contain an entered PIN. |

Screen captures document the rendered desktop. Upstream interface, application icons and wallpaper retain their respective authorship and licenses; no separate wallpaper asset is redistributed. See [Omarchy](https://github.com/omacom/omarchy) and [Omarchy Mobile](https://github.com/derekross/omarchy-mobile). The project's MIT license does not relicense third-party visual content.

Do not replace these with raw terminal, camera, account, network or personal-gallery captures. Future images need manual review, not only a metadata scan.

## Original boot V2 and R16

`apollo-boot-r16.png` is a real 1080×2400 native KMS capture from the R16 minimal RAM rescue trial. It contains only the original Omarchy wordmark and background. It has a standard sRGB color tag and no text/EXIF metadata or identifiers. It is distinct from the SDDM Qt previews in [the V2 experiment](../experiments/original-boot-v2/README.md). No separate human confirmation of the final R16 screen was obtained.

V2 previews are renders of the original MIT Omarchy composition and the portrait/touch adaptation, not photographs or successful phone PAM logins. The reference and initial 432×960 renders are byte-identical; the keyboard preview exercises a rejecting mock. Their only ancillary image data is technical DPI. Native theme PNG assets are unchanged upstream files. **David Heinemeier Hansson's original MIT attribution remains in each native theme directory.** This does not claim ownership of or endorsement by upstream Omarchy.


## Calls 4 two-origin fixtures

`phone-two-origins-landscape-fixture.png` and `phone-two-origins-portrait-fixture.png`
are fresh960×344 and 432×916 real-GTK sandbox renders with two dummy origins and
empty number fields. They are not phone captures or accounts/SIM inventories.
Pixels were manually reviewed; only technical PNG chunks are retained. The original
MIT Omarchy logo is unchanged; Calls GPL3+/libcall-ui LGPL2.1+ authorship remains.
Fresh fixtures do not prove every runtime resize or physical rotation sequence.
