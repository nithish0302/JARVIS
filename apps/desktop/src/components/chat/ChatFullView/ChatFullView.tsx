import React, { useEffect, useRef, useState } from "react";
import { cn } from "../../../lib/cn";
import { useJarvisChat } from "../../../hooks/useJarvisChat";
import { useConversationStore } from "../../../stores/useConversationStore";
import { SearchBadge } from "../SearchBadge/SearchBadge";
import { SourcesList } from "../SourcesList/SourcesList";

export function ChatFullView() {
  const { messages, sendUserMessage, isTyping, streamingMessageId, streamingContent, streamingSearchQuery } = useJarvisChat();
  const currentConversationTitle = useConversationStore((state) => state.currentConversationTitle);
  const [inputValue, setInputValue] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

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
    if (logRef.current) {
      logRef.current.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isTyping, streamingContent]);

  const clearConversation = useConversationStore(state => state.clearConversation);

  const handleNewChat = () => {
    clearConversation();
  };

  const formatTime = (timestamp: string) => {
    if (!timestamp) return "";
    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) return timestamp;
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return timestamp;
    }
  };

  const getTitle = () => {
    if (currentConversationTitle) return currentConversationTitle.toUpperCase();
    if (!messages || messages.length === 0) return "NEW CONVERSATION";
    const firstMsg = messages[0].content;
    const title = firstMsg.length > 40 ? firstMsg.substring(0, 40) + "..." : firstMsg;
    return title.toUpperCase();
  };

  const allMessages = [...messages];
  if (streamingMessageId) {
    allMessages.push({
      id: streamingMessageId,
      role: "assistant",
      content: streamingContent,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      searchPerformed: true,
      searchQuery: streamingSearchQuery || undefined
    });
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col h-full bg-transparent overflow-hidden px-8 pb-6 pt-8 z-10">
      <div className="flex items-center justify-between mb-4 px-2">
        <div className="w-[100px]"></div> {/* Spacer to center the title */}
        <div className="font-display text-[14px] uppercase tracking-wider text-[var(--color-muted)] text-center flex-1">
          {getTitle()}
        </div>
        <div className="w-[100px] flex justify-end">
          <button 
            onClick={handleNewChat}
            className="flex items-center gap-2 h-[28px] px-3 rounded-md border border-[var(--color-line)] bg-transparent text-[11px] font-mono text-[var(--color-muted)] cursor-pointer transition-colors hover:text-[var(--color-cyan)] hover:border-[var(--color-line-strong)]"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="w-3 h-3">
              <path d="M12 5v14M5 12h14" />
            </svg>
            New Chat
          </button>
        </div>
      </div>

      <div 
        className="flex-1 flex flex-col gap-4 overflow-y-auto pr-4 mb-4 no-scrollbar"
        ref={logRef}
      >
        <div className="flex-1 min-h-0" /> {/* Spacer to push messages down if few */}
        {allMessages.map((msg, idx) => (
          <div key={idx} className={cn("flex flex-col", msg.role === "user" ? "items-end" : "items-start")}>
            {msg.role === "assistant" && (
              <SearchBadge query={msg.searchQuery || ""} visible={msg.searchPerformed === true} />
            )}
            <div 
              className={cn(
                "max-w-[82%] px-[15px] py-[11px] rounded-xl text-[14px] leading-[1.6] backdrop-blur-[8px] border"
              )}
              style={{ 
                background: 'var(--color-panel)', 
                borderColor: msg.role === 'user' ? 'rgba(82, 236, 227, 0.3)' : 'var(--color-line)' 
              }}
            >
              {msg.role === "assistant" && (
                <div className="flex flex-col mb-[6px]">
                  <div className="flex items-center gap-[6px]">
                    <div className="w-[6px] h-[6px] rounded-full shadow-[0_0_6px_var(--color-cyan)]" style={{ background: 'var(--color-cyan)' }} />
                    <span className="font-display font-bold tracking-[1px] text-[12px] uppercase" style={{ color: 'var(--color-cyan)' }}>J.A.R.V.I.S</span>
                  </div>
                </div>
              )}
              <div className="whitespace-pre-wrap font-sans text-[var(--text)]">{msg.content}</div>
              {msg.role === "assistant" && (
                <SourcesList sources={msg.sources || []} visible={msg.searchPerformed === true} />
              )}
              <div className="mt-2 font-mono text-[11px] text-right" style={{ color: 'var(--color-muted-dim)' }}>
                {formatTime(msg.timestamp)}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="flex items-center gap-2 rounded-xl p-[8px_8px_8px_18px] shadow-[0_8px_30px_rgba(0,0,0,0.4)] flex-shrink-0"
           style={{ background: 'var(--color-panel-solid)', border: '1px solid var(--color-line-strong)' }}>
        <input
          type="text"
          placeholder="Ask JARVIS..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
          className="flex-1 bg-transparent border-none outline-none font-sans text-[14px] placeholder-[var(--color-muted-dim)] text-[var(--text)]"
        />
        <button 
          onClick={handleSend}
          className="w-[40px] h-[40px] rounded-lg border-none flex items-center justify-center cursor-pointer transition-colors hover:bg-[rgba(82,236,227,0.18)]"
          style={{ background: 'rgba(82,236,227,0.12)', color: 'var(--color-cyan)' }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="w-5 h-5">
            <path d="M4 12h15M13 6l6 6-6 6" />
          </svg>
        </button>
      </div>
    </div>
  );
}
