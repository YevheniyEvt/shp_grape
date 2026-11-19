import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Unmount rendered trees between tests (Vitest runs without globals, so RTL cannot do it itself).
afterEach(cleanup);

// jsdom has no ResizeObserver; Radix (slider, select) only needs it to exist.
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
