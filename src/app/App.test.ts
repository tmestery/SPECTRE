import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("exports the shell component", () => {
    expect(App).toBeTypeOf("function");
  });
});
