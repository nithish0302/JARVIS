import { useEffect } from "react";
import { useConversationStore } from "../stores/useConversationStore";
import { getConversation } from "../services/jarvisApi";

export function useConversationLoader() {
  const { 
    setConversationId,
    addMessage,
    messages 
  } = useConversationStore();

  useEffect(() => {
    const load = async () => {
      if (messages.length > 0) return;
      
      const savedId = window.localStorage?.getItem("jarvis_conversation_id");
      if (!savedId) return;
      
      try {
        const history = await getConversation(savedId);
        if (!history || history.length === 0) return;
        
        setConversationId(savedId);
        
        history.forEach((msg: any) => {
          addMessage({
            id: window.crypto.randomUUID(),
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp || "",
          });
        });
      } catch {
        window.localStorage?.removeItem("jarvis_conversation_id");
      }
    };
    
    load();
  }, [messages.length, addMessage, setConversationId]);
}
