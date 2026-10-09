// Your catalogue. Add, remove or reorder entries — the page renders from this list.
//
// name:    shown in the sidebar
// url:     the live site loaded in the preview
// glyph:   spark | leaf | wave | grid | bolt | chat | moon | camera
// colors:  two hex values for the icon gradient (also tints the selected row)
// embed:   set to false for sites that refuse to load inside an iframe
//          (X-Frame-Options / CSP frame-ancestors) — the preview shows an "Open" card instead

window.APPS = [
  { name: "Lumen",    url: "https://example.com",  glyph: "spark",  colors: ["#FFB340", "#FF5E3A"] },
  { name: "Verdant",  url: "https://example.org",  glyph: "leaf",   colors: ["#5BE37D", "#1E9E5A"] },
  { name: "Tidepool", url: "https://example.net",  glyph: "wave",   colors: ["#64D2FF", "#0A60FF"] },
  { name: "Gridline", url: "https://example.com",  glyph: "grid",   colors: ["#BF5AF2", "#5E5CE6"] },
  { name: "Voltage",  url: "https://example.org",  glyph: "bolt",   colors: ["#FFD60A", "#FF9F0A"] },
  { name: "Murmur",   url: "https://example.net",  glyph: "chat",   colors: ["#FF6482", "#D63384"] },
  { name: "Nocturne", url: "https://github.com",   glyph: "moon",   colors: ["#5E5CE6", "#1C1C5E"], embed: false },
];
