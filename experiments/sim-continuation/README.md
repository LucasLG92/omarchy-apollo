# SIM continuation 0.2.2

Source-only record of **0.2.2-1**, installed and accepted in the combined normal
reboot test: desktop and Phone correct, SIM without screen jumps. This supersedes
the earlier installed 0.2.1 status. The [0.1.3 export](../sim-unlock/README.md) stays
historical, with its own R18/R19 scope.

The event-based launcher waits for the authenticated display without periodic
display polling. Status readiness is composed inside one window. Entering the
ready form cancels queued startup reads so they cannot clear freshly typed input.
Auto-close occurs only after a stable unlocked or absent-card state; there is no
automatic PIN retry. Secondary PIN2/PUK2 is distinguished from the primary access
PIN and does not imply another physical card.

The controller reviewed 14 ARM GTK checks across five viewports plus event-launcher
checks. The earlier 14 input/backend methods and identity-free state helper stayed
unchanged. Device warm continuation and the later combined human reboot acceptance
are separate from those synthetic checks. No PIN, subscriber identity, screenshot
or network configuration is included here.

These five [pinned payloads](SOURCEPINS.json) are **not a complete package or general
root-GUI launcher**. They expect the existing Apollo unit, root-owned entry point,
owner-ready state, UID1000 Wayland integration and normal device policy. Do not run
them as an unreviewed standalone installer. No new authorization bypass is added.
Original Apollo contributor MIT license and source headers are retained.
