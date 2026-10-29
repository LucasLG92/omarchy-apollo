-- Portrait panel: 1080 x 2400 becomes a readable 432 x 960 touch workspace.
hl.monitor({ output = "DSI-1", mode = "preferred", position = "0x0", scale = 2.5 })
hl.env("GDK_SCALE", "2")
