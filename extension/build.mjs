// Build script for the OfferFlow browser extension.
//
// Bundles the TypeScript entry points with esbuild and copies static assets
// (manifest, popup HTML/CSS) into dist/. Load dist/ as an unpacked extension.
import { build, context } from "esbuild";
import { cp, mkdir, rm } from "node:fs/promises";

const watch = process.argv.includes("--watch");
const outdir = "dist";

const options = {
  entryPoints: {
    background: "src/background.ts",
    content: "src/content.ts",
    popup: "src/popup.ts",
  },
  bundle: true,
  format: "esm",
  target: "chrome110",
  outdir,
  logLevel: "info",
};

async function copyStatic() {
  await cp("src/manifest.json", `${outdir}/manifest.json`);
  await cp("src/popup.html", `${outdir}/popup.html`);
  await cp("src/popup.css", `${outdir}/popup.css`);
}

await rm(outdir, { recursive: true, force: true });
await mkdir(outdir, { recursive: true });
await copyStatic();

if (watch) {
  const ctx = await context(options);
  await ctx.watch();
  console.log("Watching for changes… (assets are copied once on start)");
} else {
  await build(options);
  console.log("Build complete → dist/");
}
