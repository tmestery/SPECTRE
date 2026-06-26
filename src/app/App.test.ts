import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("exports the dashboard component", () => {
    expect(App).toBeTypeOf("function");
  });
});
