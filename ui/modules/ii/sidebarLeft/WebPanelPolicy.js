.pragma library

var defaults = [
    {id: "chatgpt", name: "ChatGPT", url: "https://chatgpt.com"},
    {id: "gemini", name: "Gemini", url: "https://gemini.google.com"}
];

function sites(value) {
    var clean = (value && typeof value.length === "number" ? Array.prototype.slice.call(value) : defaults).filter(function(site) {
        return site && typeof site.name === "string" && /^https?:\/\/[^\s/]+/i.test(site.url || "");
    }).slice(0, 6).map(function(site, index) {
        return {id: String(site.id || "site-" + index), name: site.name.slice(0, 28),
            url: String(site.url), navigation: site.navigation === true, lookAhead: site.lookAhead === true,
            discardWhenHidden: site.discardWhenHidden !== false, theme: site.theme === "compact-forum" ? site.theme : "native",
            zoom: Math.max(0.5, Math.min(1.5, Number(site.zoom) || 0.9))};
    });
    return clean.length ? clean : sites(defaults);
}
