import { useEffect, useState } from "react";
import { useAppStore } from "../../../stores/useAppStore";
import { PinAuthModal } from "../../conversations/ConversationPanel/PinAuthModal";
import { updateMemory, deleteMemory } from "../../../services/jarvisApi";
import { MEMORY_CATEGORIES } from "../../../data/graphHubs";

export function MemoryInspector() {
  const selectedMemory = useAppStore(state => state.selectedMemory);
  const setSelectedMemory = useAppStore(state => state.setSelectedMemory);
  const deletingMemoryId = useAppStore(state => state.deletingMemoryId);
  const setDeletingMemoryId = useAppStore(state => state.setDeletingMemoryId);
  const bumpMemoriesVersion = useAppStore(state => state.bumpMemoriesVersion);

  const [editing, setEditing] = useState(false);
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("fact");
  const [importance, setImportance] = useState(5);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setEditing(false);
    setError("");
    if (selectedMemory) {
      setContent(selectedMemory.content || "");
      setCategory(selectedMemory.category || "fact");
      setImportance(selectedMemory.importance ?? 5);
    }
  }, [selectedMemory]);

  if (!selectedMemory) {
    return (
      <div className="inspector-empty">
        Click a memory leaf to inspect it - content, category, importance, and when it was created.
      </div>
    );
  }

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const updated = await updateMemory(selectedMemory.id, {
        content: content.trim(),
        category,
        importance,
      });
      setSelectedMemory(updated);
      bumpMemoriesVersion();
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save memory");
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmDelete = async (pin: string) => {
    if (!deletingMemoryId) return;
    await deleteMemory(deletingMemoryId, pin);
    setDeletingMemoryId(null);
    setSelectedMemory(null);
    bumpMemoriesVersion();
  };

  const createdAt = selectedMemory.created_at
    ? new Date(selectedMemory.created_at).toLocaleString()
    : "Unknown";

  return (
    <>
      <div className="node-title">Memory</div>
      <div className="node-meta">
        {(selectedMemory.category || "fact").toUpperCase()} · IMPORTANCE {selectedMemory.importance ?? 5}/10
      </div>

      {editing ? (
        <div className="memory-edit-form">
          <textarea
            className="memory-edit-textarea"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={4}
          />
          <div className="memory-edit-row">
            <label className="memory-edit-label">
              Category
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {MEMORY_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
            <label className="memory-edit-label">
              Importance
              <input
                type="number"
                min={1}
                max={10}
                value={importance}
                onChange={(e) => setImportance(Math.max(1, Math.min(10, Number(e.target.value) || 1)))}
              />
            </label>
          </div>
          {error && <div className="memory-edit-error">{error}</div>}
          <div className="memory-edit-actions">
            <button className="memory-btn memory-btn-cancel" onClick={() => setEditing(false)} disabled={saving}>
              Cancel
            </button>
            <button className="memory-btn memory-btn-save" onClick={handleSave} disabled={saving || !content.trim()}>
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="node-desc">{selectedMemory.content}</div>
          <div className="memory-created">Created {createdAt}</div>
          <div className="memory-edit-actions">
            <button className="memory-btn memory-btn-cancel" onClick={() => setEditing(true)}>
              Edit
            </button>
            <button
              className="memory-btn memory-btn-delete"
              onClick={() => setDeletingMemoryId(selectedMemory.id)}
            >
              Delete
            </button>
          </div>
        </>
      )}

      <PinAuthModal
        isOpen={!!deletingMemoryId}
        onCancel={() => setDeletingMemoryId(null)}
        onConfirm={handleConfirmDelete}
        itemLabel="memory"
      />
    </>
  );
}
