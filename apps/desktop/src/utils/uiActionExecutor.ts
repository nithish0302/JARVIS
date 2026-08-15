import { useAppStore } from "../stores/useAppStore"
import type { UIAction } from "./uiActionParser"

export function executeUIActions(
  actions: UIAction[]
): void {
  const store = useAppStore.getState()
  
  for (const action of actions) {
    try {
      switch (action.type) {
        case "chat_mode_on":
          store.setChatMode(true)
          break
          
        case "chat_mode_off":
          store.setChatMode(false)
          break
          
        case "graph_expand":
          store.setGraphLevel(1)
          break
          
        case "graph_collapse":
          store.setGraphLevel(0)
          break
          
        case "graph_open_hub":
          if (action.payload) {
            if (store.graphLevel === 0) {
              store.setGraphLevel(1)
              setTimeout(() => {
                store.setActiveHub(action.payload!)
                store.setGraphLevel(2)
              }, 800)
            } else {
              store.setActiveHub(action.payload!)
              store.setGraphLevel(2)
            }
          }
          break
          
        case "conversations_open":
          store.setConversationPanelOpen(true)
          break
          
        case "conversations_close":
          store.setConversationPanelOpen(false)
          break
          
        default:
          console.log(
            "Unknown UI action:", action.type
          )
      }

      const feedbackMessages: Record<string, string> = {
        "chat_mode_on": "Switching to conversation mode, sir.",
        "chat_mode_off": "Returning to HUD mode, sir.",
        "graph_expand": "Expanding knowledge graph.",
        "graph_collapse": "Collapsing knowledge graph.",
        "graph_open_hub:Skills": "Opening Skills hub, sir.",
        "graph_open_hub:Tools": "Opening Tools hub, sir.",
        "graph_open_hub:Files": "Opening Files hub, sir.",
        "graph_open_hub:Notes": "Opening Notes hub, sir.",
        "graph_open_hub:Models": "Opening Models hub, sir.",
        "graph_open_hub:Conversations": "Opening Conversations hub.",
        "conversations_open": "Displaying conversation history.",
        "conversations_close": "Closing conversation panel.",
      }

      const key = action.payload 
        ? `${action.type}:${action.payload}`
        : action.type
      const message = feedbackMessages[key] || 
        `Executing: ${action.type}`
      
      store.showActionFeedback(message)
      store.setInspectorMessage(`Executed: ${message}`)

    } catch (err) {
      console.error(
        "UI action error:", action.type, err
      )
    }
  }
}
