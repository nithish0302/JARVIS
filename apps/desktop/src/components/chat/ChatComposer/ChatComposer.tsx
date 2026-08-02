import { type KeyboardEvent, useEffect, useRef, useState, type ElementRef } from "react";
import { cn } from "../../../lib/cn";
import { ComposerToolbar } from "../ComposerToolbar/ComposerToolbar";
import { SendButton } from "../SendButton/SendButton";

export interface ChatComposerProps {
  disabled?: boolean;
  // eslint-disable-next-line no-unused-vars
  onSend: (message: string) => void;
  placeholder?: string;
}

export function ChatComposer({
  disabled = false,
  onSend,
  placeholder = "Message JARVIS...",
}: ChatComposerProps) {
  const [inputText, setInputText] = useState("");
  const textareaRef = useRef<ElementRef<"textarea">>(null);

  // Auto-grow textarea up to 5 lines (approx 120px depending on line-height)
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to recalculate scrollHeight correctly
    textarea.style.height = "auto";
    const nextHeight = Math.min(textarea.scrollHeight, 120);
    textarea.style.height = `${nextHeight}px`;
  }, [inputText]);

  const handleSend = () => {
    const trimmed = inputText.trim();
    if (!trimmed || disabled) return;

    onSend(trimmed);
    setInputText("");
    
    // Reset height explicitly
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<ElementRef<"textarea">>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isOverLimit = inputText.length > 500;
  const isSendDisabled = disabled || inputText.trim().length === 0;

  return (
    <div className="flex w-full flex-col gap-[var(--space-2)] rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-[var(--space-2)] focus-within:border-[var(--color-accent)] focus-within:ring-1 focus-within:ring-[var(--color-accent)] transition-all">
      <textarea
        ref={textareaRef}
        aria-label="Message"
        className={cn(
          "w-full resize-none overflow-y-auto bg-transparent px-[var(--space-2)] py-[var(--space-2)] text-[length:var(--font-size-md)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none",
        )}
        disabled={disabled}
        onChange={(e) => setInputText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        value={inputText}
      />
      <div className="flex items-center justify-between">
        <ComposerToolbar />
        <div className="flex flex-col items-end gap-[var(--space-1)]">
          {isOverLimit && (
            <span className="text-[length:var(--font-size-caption)] text-[var(--color-text-muted)]">
              {inputText.length} / 500
            </span>
          )}
          <SendButton disabled={isSendDisabled} onClick={handleSend} />
        </div>
      </div>
    </div>
  );
}
