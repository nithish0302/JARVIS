import { useEffect, useMemo, useRef, useState } from "react";
import "./ConversationPanel.css";
import { PinAuthModal } from "./PinAuthModal";
import { useAppStore } from "../../../stores/useAppStore";
import { getConversations, getConversation, updateConversationTitle, deleteConversation } from "../../../services/jarvisApi";
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
  const conversationPanelOpen = useAppStore(state => state.conversationPanelOpen);
  const setConversationPanelOpen = useAppStore(state => state.setConversationPanelOpen);
  
  const clearConversation = useConversationStore(state => state.clearConversation);
  const setConversationId = useConversationStore(state => state.setConversationId);
  const setConversationTitle = useConversationStore(state => state.setConversationTitle);
  const currentConversationId = useConversationStore(state => state.currentConversationId);
  const addMessage = useConversationStore(state => state.addMessage);

  const [conversations, setConversations] = useState<ConvoMeta[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [search, setSearch] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);
  const deletingConversationId = useAppStore(state => state.deletingConversationId);
  const setDeletingConversationId = useAppStore(state => state.setDeletingConversationId);
  const conversationSearchFocusToken = useAppStore(state => state.conversationSearchFocusToken);
  // Bumped by useJarvisChat.ts whenever a voice turn creates, switches, or
  // appends to a conversation - lets this panel reflect that without the
  // user closing and reopening it. Bumps while the panel is closed are
  // harmless: they don't refetch (see the effect below), and the next
  // open always fetches fresh regardless of this token's value.
  const conversationsVersion = useAppStore(state => state.conversationsVersion);

  const refreshConversations = () => {
    getConversations()
      .then(setConversations)
      .catch(console.error);
  };

  useEffect(() => {
    if (conversationPanelOpen) {
      refreshConversations();
    }
  }, [conversationPanelOpen, conversationsVersion]);

  // Ctrl+F bumps the token in the store; focus the input on every bump so
  // repeated presses re-focus rather than firing only once.
  useEffect(() => {
    if (conversationSearchFocusToken === 0) return;
    const t = setTimeout(() => {
      searchRef.current?.focus();
      searchRef.current?.select();
    }, 60);
    return () => clearTimeout(t);
  }, [conversationSearchFocusToken]);

  const visibleConversations = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return conversations;
    return conversations.filter((c) =>
      `${c.title || "Session"} ${c.preview || ""}`.toLowerCase().includes(q)
    );
  }, [conversations, search]);

  const loadConversation = async (id: string, title: string) => {
    try {
      clearConversation();
      const history = await getConversation(id);
      
      if (!history || history.length === 0) return;
      
      setConversationId(id);
      setConversationTitle(title);
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

  const handleEditClick = (e: React.MouseEvent, c: ConvoMeta) => {
    e.stopPropagation();
    setEditingId(c.id);
    setEditingTitle(c.title || "Session");
  };

  const handleRenameSubmit = async (e: React.FormEvent, id: string) => {
    e.preventDefault();
    if (editingTitle.trim()) {
      try {
        await updateConversationTitle(id, editingTitle.trim());
        if (currentConversationId === id) {
          setConversationTitle(editingTitle.trim());
        }
        refreshConversations();
      } catch (err) {
        console.error(err);
      }
    }
    setEditingId(null);
  };

  const handleDeleteClick = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDeletingConversationId(id);
  };

  const handleConfirmDelete = async (pin: string) => {
    if (!deletingConversationId) return;
    // deleteConversation now carries the PIN to the server, which is the
    // actual enforcement point (DELETE /conversation/{id} checks it
    // server-side) - a 403 here throws and PinAuthModal shows the shake.
    await deleteConversation(deletingConversationId, pin);
    if (currentConversationId === deletingConversationId) {
      clearConversation();
    }
    refreshConversations();
    setDeletingConversationId(null);
  };

  const cancelDelete = () => {
    setDeletingConversationId(null);
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
      <div className="convo-search">
        <input
          ref={searchRef}
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter conversations…"
          aria-label="Filter conversations"
        />
        {search && (
          <button
            className="convo-search-clear"
            onClick={() => setSearch("")}
            title="Clear filter"
          >
            &times;
          </button>
        )}
      </div>
      <div className="convo-list">
        {visibleConversations.map((c) => (
          <div
            key={c.id}
            className="convo-item group relative"
            onClick={() => editingId !== c.id && loadConversation(c.id, c.title || "Session")}
          >
            {editingId === c.id ? (
              <form onSubmit={(e) => handleRenameSubmit(e, c.id)} className="w-full mb-1">
                <input 
                  type="text" 
                  value={editingTitle}
                  onChange={(e) => setEditingTitle(e.target.value)}
                  onBlur={(e) => handleRenameSubmit(e, c.id)}
                  autoFocus
                  className="w-full bg-[#0D1420] text-[#E8EEF7] border border-[rgba(79,168,255,0.3)] px-2 py-1 text-sm rounded outline-none"
                  onClick={(e) => e.stopPropagation()}
                />
              </form>
            ) : (
              <div className="t pr-12">{c.title || "Session"}</div>
            )}
            <div className="m">{timeAgo(c.updated_at)} · {c.id.split("-")[0]}</div>
            <div className="s">{c.preview}</div>

            {/* Action buttons (shown on hover) */}
            {editingId !== c.id && (
              <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  onClick={(e) => handleEditClick(e, c)}
                  className="p-1 rounded bg-[rgba(13,20,32,0.8)] text-[#8B98AC] hover:text-[#4FA8FF] border border-transparent hover:border-[rgba(79,168,255,0.3)] transition-colors"
                  title="Rename"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
                <button 
                  onClick={(e) => handleDeleteClick(e, c.id)}
                  className="p-1 rounded bg-[rgba(13,20,32,0.8)] text-[#8B98AC] hover:text-[#ff4f4f] border border-transparent hover:border-[rgba(255,79,79,0.3)] transition-colors"
                  title="Delete"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        ))}
        {visibleConversations.length === 0 && (
          <div className="convo-item">
            <div className="s">
              {search.trim()
                ? `No conversations match "${search.trim()}".`
                : "No previous conversations found."}
            </div>
          </div>
        )}
      </div>

      <PinAuthModal
        isOpen={!!deletingConversationId}
        onCancel={cancelDelete}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
}
