import React, { useEffect, useRef, useState } from "react";
import { cn } from "../../../lib/cn";
import { useJarvisChat } from "../../../hooks/useJarvisChat";
import { useAppStore } from "../../../stores/useAppStore";

export function ChatShell() {
  const { messages, sendUserMessage, isTyping, streamingMessageId, streamingContent, streamingSearchQuery } = useJarvisChat();
  const { graphFocused, setGraphFocused } = useAppStore();
  const [inputValue, setInputValue] = useState("");
  const [messagesFaded, setMessagesFaded] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  const FADE_DELAY = 15000;

  useEffect(() => {
    if (messages.length === 0 && !streamingMessageId) return;
    const timer = setTimeout(() => {
      setMessagesFaded(true);
    }, FADE_DELAY);
    return () => clearTimeout(timer);
  }, [messages, streamingContent, streamingMessageId]);

  const handleInputFocus = () => {
    setMessagesFaded(false);
  };

  const handleSend = () => {
    const val = inputValue.trim();
    if (!val) return;
    setInputValue("");
    setGraphFocused(false); // expands chat, dims graph
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

  const handleScroll = () => {
    if (logRef.current) {
      if (logRef.current.scrollTop <= 4) {
        setGraphFocused(true); // collapse chat when scrolled to very top
      }
    }
  };

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
      <div 
        className={cn(
          "flex flex-col gap-2 overflow-y-auto pr-[2px] mb-[10px] transition-all duration-1000 ease-out",
          graphFocused ? "max-h-0 opacity-0 mb-0 overflow-hidden" : "max-h-[calc(60vh-120px)] min-h-[200px]",
          messagesFaded && !graphFocused ? "opacity-0" : "opacity-100"
        )} 
        ref={logRef} 
        onScroll={handleScroll}
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {allMessages.map((msg, idx) => (
          <div 
            key={idx} 
            className={cn(
              "max-w-[82%] px-[13px] py-[9px] rounded-xl text-[13px] leading-[1.5] backdrop-blur-[8px] border",
              msg.role === "user" ? "self-end" : "self-start"
            )}
            style={{ 
              background: 'var(--color-panel)', 
              borderColor: msg.role === 'user' ? 'rgba(82, 236, 227, 0.3)' : 'var(--color-line)' 
            }}
          >
            {msg.role === "assistant" && (
              <div className="flex flex-col mb-[3px]">
                <div className="flex items-center gap-[6px]">
                  <div className="w-[6px] h-[6px] rounded-full shadow-[0_0_6px_var(--color-cyan)]" style={{ background: 'var(--color-cyan)' }} />
                  <span className="font-display font-bold tracking-[1px] text-[11px] uppercase" style={{ color: 'var(--color-cyan)' }}>J.A.R.V.I.S</span>
                </div>
                {msg.searchQuery && (
                  <div className="font-mono text-[10px] flex items-center mt-1" style={{ color: 'var(--color-cyan)' }}>
                    🌐 searched: {msg.searchQuery}
                  </div>
                )}
              </div>
            )}
            <div className="whitespace-pre-wrap font-sans text-[var(--text)]">{msg.content}</div>
            <div className="mt-1 font-mono text-[10px] text-right" style={{ color: 'var(--color-muted-dim)' }}>
              {msg.timestamp}
            </div>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 rounded-[14px] p-[6px_6px_6px_16px] shadow-[0_8px_30px_rgba(0,0,0,0.4)]"
           style={{ background: 'var(--color-panel-solid)', border: '1px solid var(--color-line-strong)' }}>
        <input
          type="text"
          placeholder="Ask JARVIS..."
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setMessagesFaded(false);
          }}
          onKeyDown={handleKeyDown}
          onFocus={handleInputFocus}
          className="flex-1 bg-transparent border-none outline-none font-sans text-[13.5px] placeholder-[var(--color-muted-dim)] text-[var(--text)]"
        />
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
