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
          
        case "new_chat":
          import("../stores/useConversationStore").then(m => {
            m.useConversationStore.getState().clearConversation()
            if (action.payload) {
              const newId = window.crypto?.randomUUID() || Math.random().toString()
              m.useConversationStore.getState().setConversationId(newId)
              import("../services/jarvisApi").then(api => {
                api.updateConversationTitle(newId, action.payload!).then(() => {
                  m.useConversationStore.getState().setConversationTitle(action.payload!)
                }).catch(err => {
                  store.showActionFeedback(err.message)
                  m.useConversationStore.getState().clearConversation()
                })
              })
            }
          })
          store.setChatMode(true)
          store.setConversationPanelOpen(false)
          break

        case "delete_conversation":
          if (action.payload) {
            import("../services/jarvisApi").then(api => {
              api.getConversations().then(convos => {
                const target = convos.find(c => c.title.toLowerCase().includes(action.payload!.toLowerCase()))
                if (target) {
                  store.setDeletingConversationId(target.id)
                } else {
                  store.showActionFeedback(`Could not find a conversation named "${action.payload}"`)
                }
              })
            })
          }
          break
          
        case "rename_chat":
          if (action.payload) {
            import("../stores/useConversationStore").then(m => {
              const currentId = m.useConversationStore.getState().currentConversationId
              if (currentId) {
                import("../services/jarvisApi").then(api => {
                  api.updateConversationTitle(currentId, action.payload!).then(() => {
                    m.useConversationStore.getState().setConversationTitle(action.payload!)
                  }).catch(err => {
                    store.showActionFeedback(err.message)
                  })
                })
              } else {
                const newId = window.crypto?.randomUUID() || Math.random().toString()
                m.useConversationStore.getState().setConversationId(newId)
                import("../services/jarvisApi").then(api => {
                  api.updateConversationTitle(newId, action.payload!).then(() => {
                    m.useConversationStore.getState().setConversationTitle(action.payload!)
                  }).catch(err => {
                    store.showActionFeedback(err.message)
                    m.useConversationStore.getState().clearConversation()
                  })
                })
              }
            })
          }
          break
          
        case "open_chat":
          if (action.payload) {
            import("../services/jarvisApi").then(api => {
              api.getConversations().then(convos => {
                const target = convos.find(c => c.title.toLowerCase().includes(action.payload!.toLowerCase()))
                if (target) {
                  import("../stores/useConversationStore").then(async m => {
                    const mst = m.useConversationStore.getState()
                    mst.clearConversation()
                    const history = await api.getConversation(target.id)
                    if (history && history.length > 0) {
                      mst.setConversationId(target.id)
                      mst.setConversationTitle(target.title)
                      history.filter((msg: any) => msg.role === "user" || msg.role === "assistant").forEach((msg: any) => {
                        mst.addMessage({
                          id: window.crypto?.randomUUID() || Math.random().toString(),
                          role: msg.role,
                          content: msg.content,
                          timestamp: msg.timestamp || new Date().toISOString()
                        })
                      })
                    }
                  })
                } else {
                  store.showActionFeedback(`Could not find a conversation named "${action.payload}"`)
                }
              })
            })
          }
          store.setChatMode(true)
          store.setConversationPanelOpen(false)
          break
          
        case "chat_mode_off":
          store.setChatMode(false)
          break
          
        case "graph_expand":
          store.setChatMode(false)
          store.setGraphLevel(1)
          break
          
        case "graph_collapse":
          store.setChatMode(false)
          store.setGraphLevel(0)
          break
          
        case "graph_open_hub":
          store.setChatMode(false)
          if (action.payload) {
            if (store.graphLevel === 0 || store.chatMode) {
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
          store.setChatMode(false)
          store.setConversationPanelOpen(true)
          if (store.graphLevel === 0 || store.chatMode) {
            store.setGraphLevel(1)
            setTimeout(() => {
              store.setActiveHub("Conversations")
              store.setGraphLevel(2)
            }, 800)
          } else {
            store.setActiveHub("Conversations")
            store.setGraphLevel(2)
          }
          break
          
        case "conversations_close":
          store.setConversationPanelOpen(false)
          break
          
        case "switch_provider":
          if (action.payload) {
            import("../stores/useAIStore").then(m => {
              m.useAIStore.getState().setProvider(action.payload as any)
            })
            import("../services/jarvisApi").then(api => {
              api.switchProvider(action.payload!, "")
            })
          }
          break
          
          case "open_app":
          if (action.payload) {
            import("../services/systemApi").then(api => {
              api.openApplication(action.payload!).then(res => {
                store.setInspectorMessage(res)
              }).catch(err => {
                store.setInspectorMessage(`Error opening app: ${err}`)
              })
            })
          }
          break
          
        case "open_url":
          if (action.payload) {
            const firstColon = action.payload.indexOf(":")
            if (firstColon !== -1) {
              const browser = action.payload.substring(0, firstColon)
              const url = action.payload.substring(firstColon + 1)
              import("../services/systemApi").then(api => {
                api.openUrlInBrowser(url, browser).then(res => {
                  store.setInspectorMessage(res)
                }).catch(err => {
                  store.setInspectorMessage(`Error opening url: ${err}`)
                })
              })
            }
          }
          break
          
        case "run_powershell":
          if (action.payload) {
            import("../services/systemApi").then(api => {
              api.executePowerShell(action.payload!, false).then(res => {
                store.setInspectorMessage(`PowerShell Output:\n${res}`)
              }).catch(err => {
                if (typeof err === "string" && err.startsWith("REQUIRES_CONFIRMATION:")) {
                  const cmd = err.replace("REQUIRES_CONFIRMATION:", "")
                  store.setPendingCommand(cmd)
                  store.setInspectorMessage(`Command requires confirmation.`)
                } else {
                  store.setInspectorMessage(`Error: ${err}`)
                }
              })
            })
          }
          break
          
        case "lock_screen":
          import("../services/systemApi").then(api => {
            api.lockScreen()
          })
          break
          
        case "confirm_action":
          if (action.payload) {
            store.setPendingCommand(action.payload)
          }
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
        "new_chat": "Starting a fresh conversation, sir.",
      }

      if (action.type === "new_chat" && action.payload) {
        feedbackMessages["new_chat"] = `Starting a new chat titled "${action.payload}", sir.`
      }

      if (action.type === "delete_conversation" && action.payload) {
        feedbackMessages[`delete_conversation:${action.payload}`] = `Initiating deletion protocol for "${action.payload}". Awaiting PIN verification...`
      }
      
      if (action.type === "rename_chat" && action.payload) {
        feedbackMessages[`rename_chat:${action.payload}`] = `Renaming current conversation to "${action.payload}", sir.`
      }

      if (action.type === "open_chat" && action.payload) {
        feedbackMessages[`open_chat:${action.payload}`] = `Opening conversation "${action.payload}", sir.`
      }

      if (action.type === "switch_provider" && action.payload) {
        feedbackMessages[`switch_provider:${action.payload}`] = `Switching AI brain to ${action.payload.toUpperCase()}, sir.`
      }
      
      if (action.type === "open_app" && action.payload) {
        feedbackMessages[`open_app:${action.payload}`] = `Opening ${action.payload}, sir.`
      }

      if (action.type === "open_url" && action.payload) {
        const firstColon = action.payload.indexOf(":")
        if (firstColon !== -1) {
          const url = action.payload.substring(firstColon + 1)
          feedbackMessages[`open_url:${action.payload}`] = `Opening URL ${url}, sir.`
        }
      }

      if (action.type === "run_powershell" && action.payload) {
        feedbackMessages[`run_powershell:${action.payload}`] = `Executing automation task, sir.`
      }

      if (action.type === "lock_screen") {
        feedbackMessages["lock_screen"] = `Locking screen, sir.`
      }

      if (action.type === "confirm_action" && action.payload) {
        feedbackMessages[`confirm_action:${action.payload}`] = `Awaiting confirmation for command, sir.`
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
