#!/usr/bin/env node
/**
 * Run a frontend tool (eslint, prettier) from the repository root, e.g. in pre-commit hooks.
 *
 * Usage: node frontend/scripts/run-in-frontend.mjs <bin> [args...] [frontend/file ...]
 * The working directory is switched to `frontend/` so the tool finds its config, and
 * `frontend/` prefixes are stripped from file arguments.
 */
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const [bin, ...rest] = process.argv.slice(2);
if (!bin) {
  console.error("usage: run-in-frontend.mjs <bin> [args...]");
  process.exit(2);
}

const args = rest.map((arg) => arg.replace(/^frontend[\\/]/, ""));
const result = spawnSync("npx", ["--no-install", bin, ...args], {
  cwd: frontendDir,
  stdio: "inherit",
  shell: process.platform === "win32",
});
process.exit(result.status ?? 1);
