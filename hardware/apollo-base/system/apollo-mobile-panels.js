// Apply a compact menu and touch-sized panels through Plasma's supported API.
// The existing desktop theme and launchers remain user-managed.
let changes = [];
for (const panel of panels()) {
    if (panel.location === "top") {
        panel.height = 48;
        panel.lengthMode = "fill";
        panel.hiding = "none";
    }
    for (const widget of panel.widgets()) {
        if (widget.type === "org.kde.plasma.appmenu") {
            widget.currentConfigGroup = ["Appearance"];
            widget.writeConfig("compactView", true);
            changes.push("compact_application_menu");
        }
        if (widget.type === "org.kde.plasma.systemtray" && knownWidgetTypes.includes("org.kde.plasma.networkmanagement")) {
            widget.currentConfigGroup = ["General"];
            const network = "org.kde.plasma.networkmanagement";
            const visible = [network, "org.kde.plasma.manage-inputmethod"].filter(type => knownWidgetTypes.includes(type));
            for (const key of ["extraItems", "shownItems"]) {
                const value = widget.readConfig(key, []);
                const items = Array.isArray(value) ? value.slice() : String(value).split(",").filter(Boolean);
                for (const type of visible) if (!items.includes(type)) items.push(type);
                widget.writeConfig(key, items);
            }
            const value = widget.readConfig("hiddenItems", []);
            const hidden = Array.isArray(value) ? value : String(value).split(",").filter(Boolean);
            widget.writeConfig("hiddenItems", hidden.filter(item => !visible.includes(item)));
            changes.push("network_widget_always_visible");
        }
    }
}
print(JSON.stringify(changes));
