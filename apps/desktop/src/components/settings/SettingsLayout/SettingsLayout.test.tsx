import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SettingsLayout } from "./SettingsLayout";

describe("SettingsLayout", () => {
  it("renders sidebar and children", () => {
    render(
      <SettingsLayout sidebar={<div>Sidebar Content</div>}>
        <div>Main Content</div>
      </SettingsLayout>
    );

    expect(screen.getByText("Sidebar Content")).toBeInTheDocument();
    expect(screen.getByText("Main Content")).toBeInTheDocument();
  });
});
