// Rasterize all SVGs in ../diagrams to high-res PNG via sharp.
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const dir = path.join(__dirname, "..", "diagrams");
const files = fs.readdirSync(dir).filter(f => f.endsWith(".svg"));
const DENSITY = 200; // ~2.8x crispness for the SVG's px dimensions

(async () => {
  for (const f of files) {
    const svg = fs.readFileSync(path.join(dir, f));
    const out = path.join(dir, f.replace(/\.svg$/, ".png"));
    try {
      const info = await sharp(svg, { density: DENSITY }).png({ compressionLevel: 9 }).toFile(out);
      console.log(`  ${f} -> ${path.basename(out)}  (${info.width}x${info.height})`);
    } catch (e) {
      console.log(`  ERR ${f}: ${e.message}`);
    }
  }
  console.log("rasterize done");
})();
