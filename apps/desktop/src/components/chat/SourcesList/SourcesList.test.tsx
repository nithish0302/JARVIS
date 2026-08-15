import { render, screen } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { SourcesList } from "./SourcesList"

// Mock the tauri open command
vi.mock("@tauri-apps/plugin-shell", () => ({
  open: vi.fn()
}))

describe("SourcesList", () => {
  const mockSources = [
    { title: "Test Source", url: "https://example.com", snippet: "Test", source: "example.com" }
  ]

  it("renders when visible and has sources", () => {
    render(<SourcesList sources={mockSources} visible={true} />)
    expect(screen.getByText("Sources:")).toBeInTheDocument()
    expect(screen.getByText("Test Source")).toBeInTheDocument()
    expect(screen.getByText("(example.com)")).toBeInTheDocument()
  })

  it("does not render when not visible", () => {
    const { container } = render(<SourcesList sources={mockSources} visible={false} />)
    expect(container.firstChild).toBeNull()
  })

  it("does not render when sources are empty", () => {
    const { container } = render(<SourcesList sources={[]} visible={true} />)
    expect(container.firstChild).toBeNull()
  })
})
