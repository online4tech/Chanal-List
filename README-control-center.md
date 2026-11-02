# Control Center

This is a standalone React + Vite + TailwindCSS page. It does not replace or modify the existing static HTML pages or their APIs/data.

## Local development

```bash
npm install
npm run dev
```

## Build for GitHub Pages

```bash
npm run build
```

Vite writes the static site to `control-center/`. Commit that generated directory to the Pages branch so the standalone page is published at:

`https://online4tech.github.io/Enigma2-Chanal-List-BYRomeh/control-center/`

The supplied `control-center-sample-data.json` is demo data and includes example.com placeholder commands. It is intentionally kept separate from the repository's existing Enigma2 catalog and command data. The page's default actions copy commands; no device API or remote execution endpoint is connected.
