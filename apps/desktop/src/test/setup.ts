import "@testing-library/jest-dom";
import { vi } from "vitest";

// jsdom has no window.__TAURI_INTERNALS__, so listen() throws trying to
// register its callback. Mock it to the real API's resolved-unlisten shape.
vi.mock("@tauri-apps/api/event", () => ({
  listen: vi.fn().mockResolvedValue(() => {}),
}));
