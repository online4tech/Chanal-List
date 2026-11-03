import { defineConfig } from "vite";
import { resolve } from "node:path";
import { existsSync, readdirSync, rmSync } from "node:fs";

const outDir = resolve(process.cwd(), "control-center");

// Remove only Vite-generated hashed assets; keep manually maintained assets such as header-logo.css.
const cleanAssetsOnly = {
  name: "clean-assets-only",
  buildStart() {
    const assetsDir = resolve(outDir, "assets");
    if (!existsSync(assetsDir)) return;
    for (const file of readdirSync(assetsDir)) {
      if (/^index-[\\w-]+\\.(js|css)$/.test(file)) {
        rmSync(resolve(assetsDir, file), { force: true });
      }
    }
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
