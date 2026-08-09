import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { StreamingMessage } from "./StreamingMessage";
import { useConversationStore } from "../../../stores/useConversationStore";

// Mock the zustand store
vi.mock("../../../stores/useConversationStore", () => ({
  useConversationStore: vi.fn(),
}));

describe("StreamingMessage", () => {
  it("renders nothing when streamingMessageId is null", () => {
    vi.mocked(useConversationStore).mockReturnValue({
      streamingMessageId: null,
      streamingContent: "",
    } as any);

    const { container } = render(<StreamingMessage />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the streaming content when streamingMessageId is set", () => {
    vi.mocked(useConversationStore).mockReturnValue({
      streamingMessageId: "msg-1",
      streamingContent: "Hello world",
    } as any);

    const { getByText } = render(<StreamingMessage />);
    expect(getByText("Hello world")).toBeInTheDocument();
  });
});
