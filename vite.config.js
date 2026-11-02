import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  root: resolve(process.cwd(), "control-center-app"),
  base: "/Enigma2-Chanal-List-BYRomeh/control-center/",
  build: {
    outDir: resolve(process.cwd(), "control-center"),
    emptyOutDir: true,
  },
});
