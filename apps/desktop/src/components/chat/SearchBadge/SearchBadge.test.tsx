import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { SearchBadge } from "./SearchBadge"

describe("SearchBadge", () => {
  it("renders when visible", () => {
    render(<SearchBadge query="test query" visible={true} />)
    expect(screen.getByText('Searched: "test query"')).toBeInTheDocument()
  })

  it("does not render when not visible", () => {
    const { container } = render(<SearchBadge query="test query" visible={false} />)
    expect(container.firstChild).toBeNull()
  })
})
