import { useEffect, useState } from "react";
import "./ConversationPanel.css";
import { useAppStore } from "../../../stores/useAppStore";
import { getConversations, getConversation } from "../../../services/jarvisApi";
import { useConversationStore } from "../../../stores/useConversationStore";
import { cn } from "../../../lib/cn";

interface ConvoMeta {
  id: string;
  updated_at: string;
  preview: string;
  title: string;
}

function timeAgo(dateStr: string) {
  const d = new Date(dateStr);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function ConversationPanel() {
  const { conversationPanelOpen, setConversationPanelOpen } = useAppStore();
  const { clearConversation, setConversationId, addMessage } = useConversationStore();
  const [conversations, setConversations] = useState<ConvoMeta[]>([]);

  useEffect(() => {
    if (conversationPanelOpen) {
      getConversations()
        .then(setConversations)
        .catch(console.error);
    }
  }, [conversationPanelOpen]);

  const loadConversation = async (id: string) => {
    try {
      clearConversation();
      const history = await getConversation(id);
      
      if (!history || history.length === 0) return;
      
      setConversationId(id);
      history
        .filter((msg: any) => msg.role === "user" || msg.role === "assistant")
        .forEach((msg: any) => {
          addMessage({
            id: window.crypto?.randomUUID() || Math.random().toString(),
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp || new Date().toISOString()
          });
        });

      setConversationPanelOpen(false);
    } catch (err) {
      console.error("Failed to load conversation", err);
    }
  };

  return (
    <div id="convoPanel" className={cn(conversationPanelOpen && "open")}>
      <div className="convo-head">
        <h3>Memory Index</h3>
        <button
          className="convo-close"
          onClick={() => setConversationPanelOpen(false)}
        >
          &times;
        </button>
      </div>
      <div className="convo-list">
        {conversations.map((c) => (
          <div
            key={c.id}
            className="convo-item"
            onClick={() => loadConversation(c.id)}
          >
            <div className="t">{c.title || "Session"}</div>
            <div className="m">{timeAgo(c.updated_at)} · {c.id.split("-")[0]}</div>
            <div className="s">{c.preview}</div>
          </div>
        ))}
        {conversations.length === 0 && (
          <div className="convo-item">
            <div className="s">No previous conversations found.</div>
          </div>
        )}
      </div>
    </div>
  );
}
