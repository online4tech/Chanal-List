import { defineConfig } from "vite";
import { resolve } from "node:path";
import { rmSync } from "node:fs";

const outDir = resolve(process.cwd(), "control-center");

// Only the hashed build output is cleaned; control-center/data/catalog.json is kept.
const cleanAssetsOnly = {
  name: "clean-assets-only",
  buildStart() {
    rmSync(resolve(outDir, "assets"), { recursive: true, force: true });
  },
};

export default defineConfig({
  root: resolve(process.cwd(), "control-center-app"),
  base: "/Enigma2-Chanal-List-BYRomeh/control-center/",
  plugins: [cleanAssetsOnly],
  build: {
    outDir,
    emptyOutDir: false,
  },
});
