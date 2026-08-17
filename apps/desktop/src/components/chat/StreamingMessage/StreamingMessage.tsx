import { useConversationStore } from "../../../stores/useConversationStore"
import ReactMarkdown from 'react-markdown'

export function StreamingMessage() {
  const { 
    streamingMessageId, 
    streamingContent 
  } = useConversationStore()
  
  if (!streamingMessageId) return null
  
  return (
    <div className="flex items-start gap-[var(--space-3)] px-[var(--space-4)] py-[var(--space-2)]">
      <div className="shrink-0 w-[var(--icon-size-lg)] h-[var(--icon-size-lg)] rounded-full bg-[var(--color-accent)] opacity-80" />
      <div className="max-w-[85%] rounded-[var(--radius-md)] bg-[var(--color-surface)] p-[var(--space-3)] text-[var(--color-text-primary)] text-[var(--font-size-body)] leading-[var(--line-height-body)] whitespace-pre-wrap break-words markdown-content">
        <ReactMarkdown>{streamingContent}</ReactMarkdown>
        <span className="inline-block w-2 h-4 bg-[var(--color-accent)] ml-1 animate-pulse" />
      </div>
    </div>
  )
}
