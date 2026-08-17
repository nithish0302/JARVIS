import React, { useEffect, useRef, useState } from "react";
import { cn } from "../../../lib/cn";
import { useJarvisChat } from "../../../hooks/useJarvisChat";
import { useAppStore } from "../../../stores/useAppStore";
import { useConversationStore } from "../../../stores/useConversationStore";
import { ConfirmationButtons } from "../ConfirmationButtons/ConfirmationButtons";

export function ChatShell() {
  const { messages, sendUserMessage, isTyping, streamingMessageId, streamingContent, streamingSearchQuery } = useJarvisChat();
  const { isStreaming } = useConversationStore();
  const clearConversation = useConversationStore(state => state.clearConversation);
  const graphFocused = useAppStore(state => state.graphFocused);
  const [inputValue, setInputValue] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

  const handleInputFocus = () => {
    // No-op
  };

  const handleSend = () => {
    const val = inputValue.trim();
    if (!val) return;
    setInputValue("");
    sendUserMessage(val);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  useEffect(() => {
    if (logRef.current && !graphFocused) {
      logRef.current.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isTyping, streamingContent, graphFocused]);



  const allMessages = [...messages];
  if (streamingMessageId) {
    allMessages.push({
      id: streamingMessageId,
      role: "assistant",
      content: streamingContent,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      searchQuery: streamingSearchQuery || undefined
    });
  }

  return (
    <div className={cn(
      "absolute left-1/2 bottom-[16px] -translate-x-1/2 w-[min(680px,88%)] z-10",
      graphFocused && "nodes-focused"
    )}>
      <ConfirmationButtons />
      <div className="flex items-center gap-2 rounded-[14px] p-[6px_6px_6px_16px] shadow-[0_8px_30px_rgba(0,0,0,0.4)]"
           style={{ background: 'var(--color-panel-solid)', border: '1px solid var(--color-line-strong)' }}>
        <input
          type="text"
          placeholder="Ask JARVIS..."
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
          }}
          onKeyDown={handleKeyDown}
          onFocus={handleInputFocus}
          className="flex-1 bg-transparent border-none outline-none font-sans text-[13.5px] placeholder-[var(--color-muted-dim)] text-[var(--text)]"
        />
        {messages.length > 0 && (
          <button
            onClick={() => clearConversation()}
            disabled={isStreaming}
            className="h-[36px] px-3 rounded-[10px] border border-transparent flex items-center gap-1.5 cursor-pointer transition-colors hover:bg-[rgba(82,236,227,0.08)] hover:text-[var(--color-cyan)] hover:border-[var(--color-line)] text-[11px] font-mono text-[var(--color-muted-dim)]"
            title="Start new conversation"
            style={{ 
              opacity: isStreaming ? 0.5 : 1,
              cursor: isStreaming ? 'not-allowed' : 'pointer'
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="w-3.5 h-3.5">
              <path d="M12 5v14M5 12h14" />
            </svg>
            New
          </button>
        )}
        <button 
          onClick={handleSend}
          className="w-[36px] h-[36px] rounded-[10px] border-none flex items-center justify-center cursor-pointer transition-colors hover:bg-[rgba(82,236,227,0.18)]"
          style={{ background: 'rgba(82,236,227,0.12)', color: 'var(--color-cyan)' }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="w-4 h-4">
            <path d="M4 12h15M13 6l6 6-6 6" />
          </svg>
        </button>
      </div>
    </div>
  );
}
