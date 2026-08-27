import { useAppStore } from "../stores/useAppStore"
import type { UIAction } from "./uiActionParser"
import {
  listDirectory,
  createFolder,
  openFile,
  showInExplorer
} from "../services/systemApi"

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

        case "personality_mode":
          if (action.payload) {
            const mode = action.payload.toLowerCase().trim() as "assistant" | "developer" | "research"
            import("../stores/useAIStore").then(m => {
              m.useAIStore.getState().setPersonalityMode(mode)
            })
            import("../services/jarvisApi").then(api => {
              api.updateSettings({ personality_mode: mode }).catch(err => {
                console.error("Failed to update personality_mode setting:", err)
              })
            })
          }
          break

        case "modifier":
          if (action.payload) {
            const mod = action.payload.toLowerCase().trim() as "none" | "planner" | "quiet"
            import("../stores/useAIStore").then(m => {
              m.useAIStore.getState().setModifier(mod)
            })
            import("../services/jarvisApi").then(api => {
              api.updateSettings({ modifier: mod }).catch(err => {
                console.error("Failed to update modifier setting:", err)
              })
            })
          }
          break

        case "provider_override":
          if (action.payload !== undefined) {
            const override = action.payload.toLowerCase().trim()
            const value = override === "none" || override === "" ? null : override
            import("../stores/useAIStore").then(m => {
              m.useAIStore.getState().setProviderOverride(value as any)
            })
            import("../services/jarvisApi").then(api => {
              api.updateSettings({ provider_override: value }).catch(err => {
                console.error("Failed to update provider_override setting:", err)
              })
            })
          }
          break

        case "fallback_mode":
          if (action.payload) {
            const mode = action.payload.toLowerCase().trim() as "auto" | "ask"
            import("../stores/useAIStore").then(m => {
              m.useAIStore.getState().setFallbackMode(mode)
            })
            import("../services/jarvisApi").then(api => {
              api.updateSettings({ fallback_mode: mode }).catch(err => {
                console.error("Failed to update fallback_mode setting:", err)
              })
            })
          }
          break

        case "address_preference":
          // payload can legitimately be "" (clear the address term), so
          // this checks !== undefined rather than truthiness like the
          // other cases above - an empty string must not be skipped.
          if (action.payload !== undefined) {
            const addr = action.payload.trim().slice(0, 20)
            import("../stores/useAIStore").then(m => {
              m.useAIStore.getState().setAddressPreference(addr)
            })
            import("../services/jarvisApi").then(api => {
              api.updateSettings({ address_preference: addr }).catch(err => {
                console.error("Failed to update address_preference setting:", err)
              })
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
          
        case "system_query":
          if (action.payload) {
            import("../services/systemApi").then(api => {
              const query = action.payload as "ip_address" | "battery_level" | "disk_space" | "top_processes" | "uptime"
              api.runSystemQuery(query).then(res => {
                store.setInspectorMessage(res)
                store.showActionFeedback(res)
                import("../stores/useConversationStore").then(m => {
                  m.useConversationStore.getState().addMessage({
                    id: window.crypto?.randomUUID() || Math.random().toString(),
                    role: "assistant",
                    content: res,
                    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                  })
                })
              }).catch(err => {
                store.setInspectorMessage(`Query error: ${err}`)
              })
            })
          }
          break
          
        case "close_app":
          if (action.payload) {
            import("../services/systemApi").then(api => {
              api.closeApplication(action.payload!).then(res => {
                store.setInspectorMessage(res)
                store.showActionFeedback(res)
              }).catch(err => {
                store.setInspectorMessage(`Error closing app: ${err}`)
                store.showActionFeedback(`Could not close ${action.payload}`)
              })
            })
          }
          break

        case "set_volume":
          if (action.payload) {
            import("../services/systemApi").then(api => {
              const act = action.payload as "up" | "down" | "mute" | "unmute"
              api.setVolume(act).then(res => {
                store.setInspectorMessage(res)
                store.showActionFeedback(res)
              }).catch(err => {
                store.setInspectorMessage(`Volume error: ${err}`)
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
            const colonIdx = action.payload.indexOf(":")
            if (colonIdx > -1) {
              const actionType = action.payload.substring(0, colonIdx)
              const path = action.payload.substring(colonIdx + 1)
              
              useAppStore.getState().setPendingCommand(
                `${actionType}:${path}`
              )
              store.showActionFeedback(
                `Waiting for confirmation...`
              )
            } else {
              useAppStore.getState().setPendingCommand(
                action.payload
              )
            }
          }
          break
          
        case "list_dir":
          if (action.payload) {
            listDirectory(action.payload)
              .then((result: any) => {
                const lines: string[] = []
                lines.push(
                  `📁 **${result.path}**`
                )
                lines.push(
                  `${result.folders.length} folders · ` +
                  `${result.files.length} files`
                )
                lines.push("")

                // Show folders first (max 10)
                result.folders.slice(0, 10).forEach(
                  (f: any) => lines.push(`📁 ${f.name}`)
                )

                // Then files (max 15)
                result.files.slice(0, 15).forEach(
                  (f: any) => {
                    const size = f.size > 1048576
                      ? `${(f.size/1048576).toFixed(1)}MB`
                      : f.size > 1024
                      ? `${(f.size/1024).toFixed(0)}KB`
                      : `${f.size}B`
                    lines.push(`📄 ${f.name} (${size})`)
                  }
                )

                if (result.total > 25) {
                  lines.push(
                    `\n... and ${result.total - 25} more items`
                  )
                }

                const summary = lines.join('\n')

                store.setInspectorMessage(
                  `${result.folders.length} folders, ` +
                  `${result.files.length} files`
                )
                store.showActionFeedback(
                  `Listed ${result.total} items, sir.`
                )

                import("../stores/useConversationStore")
                  .then(m => {
                    m.useConversationStore.getState()
                      .addMessage({
                        id: window.crypto?.randomUUID() || Math.random().toString(),
                        role: "assistant",
                        content: summary,
                        timestamp: new Date()
                          .toLocaleTimeString([],{
                            hour:"2-digit",
                            minute:"2-digit"
                          })
                      })
                  })
              })
              .catch((err: unknown) => {
                const errorMsg = err instanceof Error
                  ? err.message
                  : typeof err === 'string'
                  ? err
                  : 'Cannot list directory'
                store.showActionFeedback(errorMsg)
              })
          }
          break

        case "create_folder":
          if (action.payload) {
            createFolder(action.payload)
              .then((result: string) => {
                store.showActionFeedback(result)
                store.setInspectorMessage(result)
              })
              .catch((err: unknown) => {
                const errorMsg = err instanceof Error
                  ? err.message
                  : typeof err === 'string'
                  ? err
                  : 'Failed to create folder'
                store.showActionFeedback(errorMsg)
              })
          }
          break

        case "open_file":
          if (action.payload) {
            openFile(action.payload)
              .then((result: string) => {
                store.showActionFeedback(result)
              })
              .catch((err: unknown) => {
                const errorMsg = err instanceof Error
                  ? err.message
                  : typeof err === 'string'
                  ? err
                  : 'Cannot open file'
                store.showActionFeedback(errorMsg)
              })
          }
          break

        case "show_explorer":
          if (action.payload) {
            showInExplorer(action.payload)
              .then((result: string) => {
                store.showActionFeedback(result)
              })
              .catch((err: unknown) => {
                const errorMsg = err instanceof Error
                  ? err.message
                  : typeof err === 'string'
                  ? err
                  : 'Failed to open explorer'
                store.showActionFeedback(errorMsg)
              })
          }
          break

        case "delete_file":
          if (action.payload) {
            const { setPendingCommand } = 
              useAppStore.getState()
            setPendingCommand(
              `delete_file:${action.payload}`
            )
            store.showActionFeedback(
              `Delete ${action.payload}? Reply 'yes' to confirm.`
            )
          }
          break
          
        case "check_gmail":
          import("../services/jarvisApi").then(api => {
            api.checkGmail().then(results => {
              const count = results.length
              const message = count > 0 
                ? `You have ${count} unread emails:\n${results.map((e, i) => `${i+1}. ${e.subject} (from ${e.sender})`).join('\n')}`
                : "You have no unread emails."
              import("../stores/useConversationStore").then(m => {
                m.useConversationStore.getState().addMessage({
                  id: window.crypto?.randomUUID() || Math.random().toString(),
                  role: "assistant",
                  content: message,
                  timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                })
              })
              store.showActionFeedback(`Checked Gmail (${count} unread)`)
            }).catch(err => store.showActionFeedback(err.message))
          })
          break

        case "search_gmail":
          if (action.payload) {
            import("../services/jarvisApi").then(api => {
              api.searchGmail(action.payload!).then(results => {
                const count = results.length
                const message = count > 0 
                  ? `Found ${count} emails for "${action.payload}":\n${results.map((e, i) => `${i+1}. ${e.subject} (from ${e.sender})`).join('\n')}`
                  : `No emails found for "${action.payload}".`
                import("../stores/useConversationStore").then(m => {
                  m.useConversationStore.getState().addMessage({
                    id: window.crypto?.randomUUID() || Math.random().toString(),
                    role: "assistant",
                    content: message,
                    timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                  })
                })
                store.showActionFeedback(`Searched Gmail (${count} results)`)
              }).catch(err => store.showActionFeedback(err.message))
            })
          }
          break

        case "send_email":
          if (action.payload) {
            const parts = action.payload.split(":")
            if (parts.length >= 3) {
              const to = parts[0]
              const subject = parts[1]
              const body = parts.slice(2).join(":")
              import("../services/jarvisApi").then(api => {
                api.sendEmail(to, subject, body).then(() => {
                  store.showActionFeedback("Email sent successfully.")
                }).catch(err => store.showActionFeedback(err.message))
              })
            }
          }
          break

        case "check_calendar":
          import("../services/jarvisApi").then(api => {
            api.checkCalendar().then(results => {
              const count = results.length
              const message = count > 0 
                ? `You have ${count} events today:\n${results.map((e, i) => `${i+1}. ${e.summary} at ${e.start}`).join('\n')}`
                : "You have no events today."
              import("../stores/useConversationStore").then(m => {
                m.useConversationStore.getState().addMessage({
                  id: window.crypto?.randomUUID() || Math.random().toString(),
                  role: "assistant",
                  content: message,
                  timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                })
              })
              store.showActionFeedback(`Checked Calendar (${count} events today)`)
            }).catch(err => store.showActionFeedback(err.message))
          })
          break

        case "check_upcoming_events":
          import("../services/jarvisApi").then(api => {
            api.checkUpcomingEvents().then(results => {
              const count = results.length
              const message = count > 0 
                ? `You have ${count} upcoming events:\n${results.map((e, i) => `${i+1}. ${e.summary} on ${e.start}`).join('\n')}`
                : "You have no upcoming events."
              import("../stores/useConversationStore").then(m => {
                m.useConversationStore.getState().addMessage({
                  id: window.crypto?.randomUUID() || Math.random().toString(),
                  role: "assistant",
                  content: message,
                  timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                })
              })
              store.showActionFeedback(`Checked Calendar (${count} upcoming events)`)
            }).catch(err => store.showActionFeedback(err.message))
          })
          break

        case "create_event":
          if (action.payload) {
            const parts = action.payload.split(":")
            if (parts.length >= 3) {
              const title = parts[0]
              const start = parts[1]
              const end = parts.slice(2).join(":")
              import("../services/jarvisApi").then(api => {
                api.createEvent(title, start, end).then(() => {
                  store.showActionFeedback("Calendar event created successfully.")
                }).catch(err => store.showActionFeedback(err.message))
              })
            }
          }
          break

        case "check_weather":
          import("../services/jarvisApi").then(api => {
            api.checkWeather(action.payload || undefined).then(result => {
              const message = `Current weather in ${result.location_name}:\nTemperature: ${result.temperature}°C (Feels like ${result.feels_like}°C)\nHumidity: ${result.humidity}%\nWind: ${result.wind_speed} km/h\nCondition: ${result.weather_description}`
              import("../stores/useConversationStore").then(m => {
                m.useConversationStore.getState().addMessage({
                  id: window.crypto?.randomUUID() || Math.random().toString(),
                  role: "assistant",
                  content: message,
                  timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                })
              })
              store.showActionFeedback(`Checked weather for ${result.location_name}`)
            }).catch(err => store.showActionFeedback(err.message))
          })
          break

        case "check_forecast":
          if (action.payload) {
            const parts = action.payload.split(":")
            const location = parts[0] || undefined
            const days = parts[1] || undefined
            import("../services/jarvisApi").then(api => {
              api.checkForecast(location, days).then(results => {
                const message = `Weather forecast:\n${results.map(r => `${r.date}: High ${r.high}°C, Low ${r.low}°C, ${r.description} (${r.precipitation_chance}% rain)`).join('\n')}`
                import("../stores/useConversationStore").then(m => {
                  m.useConversationStore.getState().addMessage({
                    id: window.crypto?.randomUUID() || Math.random().toString(),
                    role: "assistant",
                    content: message,
                    timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                  })
                })
                store.showActionFeedback(`Checked forecast`)
              }).catch(err => store.showActionFeedback(err.message))
            })
          }
          break


        case "check_github_repos":
          import("../services/jarvisApi").then(api => {
            api.getGithubRepos().then(results => {
              const count = results.length
              const message = count > 0 
                ? `You have ${count} repositories:\n${results.map((r, i) => `${i+1}. ${r.full_name} (${r.language})`).join('\n')}`
                : "You have no repositories."
              import("../stores/useConversationStore").then(m => {
                m.useConversationStore.getState().addMessage({
                  id: window.crypto?.randomUUID() || Math.random().toString(),
                  role: "assistant",
                  content: message,
                  timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                })
              })
              store.showActionFeedback(`Checked GitHub repos (${count})`)
            }).catch(err => store.showActionFeedback(err.message))
          })
          break

        case "check_github_issues":
          if (action.payload) {
            import("../services/jarvisApi").then(api => {
              api.getGithubIssues(action.payload!).then(results => {
                const count = results.length
                const message = count > 0 
                  ? `You have ${count} open issues in ${action.payload}:\n${results.map((r, i) => `${i+1}. #${r.number} ${r.title}`).join('\n')}`
                  : `You have no open issues in ${action.payload}.`
                import("../stores/useConversationStore").then(m => {
                  m.useConversationStore.getState().addMessage({
                    id: window.crypto?.randomUUID() || Math.random().toString(),
                    role: "assistant",
                    content: message,
                    timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                  })
                })
                store.showActionFeedback(`Checked GitHub issues for ${action.payload}`)
              }).catch(err => store.showActionFeedback(err.message))
            })
          }
          break

        case "search_github_issues":
          if (action.payload) {
            import("../services/jarvisApi").then(api => {
              api.searchGithubIssues(action.payload!).then(results => {
                const count = results.length
                const message = count > 0 
                  ? `Found ${count} issues matching "${action.payload}":\n${results.map((r, i) => `${i+1}. #${r.number} ${r.title} (${r.state})`).join('\n')}`
                  : `No issues found for "${action.payload}".`
                import("../stores/useConversationStore").then(m => {
                  m.useConversationStore.getState().addMessage({
                    id: window.crypto?.randomUUID() || Math.random().toString(),
                    role: "assistant",
                    content: message,
                    timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                  })
                })
                store.showActionFeedback(`Searched GitHub issues`)
              }).catch(err => store.showActionFeedback(err.message))
            })
          }
          break

        case "create_github_issue":
          if (action.payload) {
            const parts = action.payload.split(":")
            if (parts.length >= 2) {
              const repo = parts[0]
              const title = parts[1]
              const body = parts.slice(2).join(":")
              import("../services/jarvisApi").then(api => {
                api.createGithubIssue(repo, title, body).then(() => {
                  store.showActionFeedback("GitHub issue created successfully.")
                }).catch(err => store.showActionFeedback(err.message))
              })
            }
          }
          break

        case "check_github_prs":
          if (action.payload) {
            import("../services/jarvisApi").then(api => {
              api.getGithubPulls(action.payload!).then(results => {
                const count = results.length
                const message = count > 0 
                  ? `You have ${count} open PRs in ${action.payload}:\n${results.map((r, i) => `${i+1}. #${r.number} ${r.title}`).join('\n')}`
                  : `You have no open PRs in ${action.payload}.`
                import("../stores/useConversationStore").then(m => {
                  m.useConversationStore.getState().addMessage({
                    id: window.crypto?.randomUUID() || Math.random().toString(),
                    role: "assistant",
                    content: message,
                    timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                  })
                })
                store.showActionFeedback(`Checked GitHub PRs for ${action.payload}`)
              }).catch(err => store.showActionFeedback(err.message))
            })
          }
          break

        case "check_pr_status":
          if (action.payload) {
            const parts = action.payload.split(":")
            if (parts.length >= 2) {
              const repo = parts[0]
              const number = parseInt(parts[1], 10)
              import("../services/jarvisApi").then(api => {
                api.getGithubPrStatus(repo, number).then(result => {
                  const message = `PR #${number} in ${repo} status: ${result.state} (${result.total_count} checks)\n${result.statuses.map((s: any) => `- ${s.context}: ${s.state} - ${s.description}`).join('\n')}`
                  import("../stores/useConversationStore").then(m => {
                    m.useConversationStore.getState().addMessage({
                      id: window.crypto?.randomUUID() || Math.random().toString(),
                      role: "assistant",
                      content: message,
                      timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                    })
                  })
                  store.showActionFeedback(`Checked PR status`)
                }).catch(err => store.showActionFeedback(err.message))
              })
            }
          }
          break

        case "search_github_code":
          if (action.payload) {
            const parts = action.payload.split(":")
            const query = parts[0]
            const repo = parts[1] || undefined
            import("../services/jarvisApi").then(api => {
              api.searchGithubCode(query, repo).then(results => {
                const count = results.length
                const message = count > 0 
                  ? `Found ${count} code results matching "${query}":\n${results.map((r, i) => `${i+1}. ${r.name} in ${r.repo}`).join('\n')}`
                  : `No code results found for "${query}".`
                import("../stores/useConversationStore").then(m => {
                  m.useConversationStore.getState().addMessage({
                    id: window.crypto?.randomUUID() || Math.random().toString(),
                    role: "assistant",
                    content: message,
                    timestamp: new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})
                  })
                })
                store.showActionFeedback(`Searched GitHub code`)
              }).catch(err => store.showActionFeedback(err.message))
            })
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

      if (action.type === "personality_mode" && action.payload) {
        feedbackMessages[`personality_mode:${action.payload}`] = `Switching personality mode to ${action.payload.toUpperCase()}, sir.`
      }

      if (action.type === "modifier" && action.payload) {
        feedbackMessages[`modifier:${action.payload}`] = `Setting modifier to ${action.payload.toUpperCase()}, sir.`
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

      if (action.type === "system_query" && action.payload) {
        feedbackMessages[`system_query:${action.payload}`] = `Querying ${action.payload.replace('_', ' ')}, sir.`
      }

      if (action.type === "close_app" && action.payload) {
        feedbackMessages[`close_app:${action.payload}`] = `Closing ${action.payload}, sir.`
      }

      if (action.type === "set_volume" && action.payload) {
        feedbackMessages[`set_volume:${action.payload}`] = `Adjusting volume (${action.payload}), sir.`
      }

      if (action.type === "lock_screen") {
        feedbackMessages["lock_screen"] = `Locking screen, sir.`
      }

      if (action.type === "confirm_action" && action.payload) {
        feedbackMessages[`confirm_action:${action.payload}`] = `Awaiting confirmation for command, sir.`
      }

      if (action.type.startsWith("check_github") || action.type.startsWith("search_github") || action.type === "create_github_issue") {
        feedbackMessages[action.payload ? `${action.type}:${action.payload}` : action.type] = `Processing GitHub request...`
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
