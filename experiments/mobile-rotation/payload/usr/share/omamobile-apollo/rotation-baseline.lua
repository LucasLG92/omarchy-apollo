-- SPDX-License-Identifier: MIT
-- Explicit coordinator-owned baseline, not inferred configuration readback.
-- Load after existing monitor/device configuration, before starting rotation.
-- Root's filtered device evidence: DSI-1 1080x2400@144, scale 2.5, at 0x0.
hl.monitor({output="DSI-1",mode="1080x2400@144",position="0x0",scale=2.5,transform=0})
hl.device({name="nvtcapacitivetouchscreen",transform=0,output="DSI-1"})
-- A reload explicitly restores this known baseline. Restart the existing unit
-- so its tracked pair is reset too; arbitrary drift still fails closed.
hl.on("config.reloaded", function()
  hl.exec_cmd("systemctl --user --no-block try-restart omamobile-autorotate.service")
end)
