# JARVIS DESKTOP APP - BUG AUDIT REPORT

**Generated:** August 17, 2026  
**Audited Files:**
- apps/desktop/src/hooks/ (all)
- apps/desktop/src/stores/ (all)
- apps/desktop/src/services/jarvisApi.ts
- apps/desktop/src/utils/ (all)
- apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx
- apps/desktop/src/components/chat/ (all)

---

## EXECUTIVE SUMMARY

This report documents a comprehensive code quality and bug audit of the JARVIS Desktop App frontend codebase. The audit focused on:

- React hooks and custom state management
- Zustand stores and state synchronization
- API integration and error handling
- UI action parsing and execution
- Graph visualization canvas
- Chat components and streaming messages

### Summary Statistics

| Priority | Count | Category |
|----------|-------|----------|
| **P1 Critical** | 8 | Memory leaks, race conditions, state corruption, XSS vulnerabilities |
| **P2 High** | 12 | Error handling, async issues, UX bugs, state inconsistencies |
| **P3 Medium** | 15 | Code quality, validation issues, performance concerns |
| **P4 Low** | 8 | Type safety, code duplication, minor UX issues |
| **TOTAL** | **43** | All categories |

---

## P1 - CRITICAL BUGS

### 1. Memory Leak: Timer Not Cleared on Unmount

**File:** `apps/desktop/src/hooks/useJarvisChat.ts:122-124`

**Code:**
```typescript
// Execute UI actions after message renders
if (actions.length > 0) {
  setTimeout(() => {
    executeUIActions(actions)
  }, 500)
}
```

**Issue:** `setTimeout` is not cancelled if the component unmounts before the timer fires. No cleanup in useEffect.

**Impact:** Memory leaks if user navigates away during AI response streaming.

---

### 2. Memory Leak: Multiple Timers in Action Feedback

**File:** `apps/desktop/src/stores/useAppStore.ts:47-51`

**Code:**
```typescript
showActionFeedback: (message) => {
  set({ actionFeedback: message, actionFeedbackVisible: true });
  setTimeout(() => {
    set({ actionFeedback: "", actionFeedbackVisible: false });
  }, 5000);
}
```

**Issue:** Calling `showActionFeedback` multiple times creates multiple overlapping timers with no cleanup. Previous timers aren't cleared.

**Impact:** Multiple timers accumulate, causing stale state updates and memory leaks.

---

### 3. Race Condition: Conversation Loading vs. New Messages

**File:** `apps/desktop/src/hooks/useConversationLoader.ts:18-97`

**Code:**
```typescript
useEffect(() => {
  if (hasLoaded.current) return
  if (messages.length > 0) return  // Check happens BEFORE async load
  if (status !== "idle") return
  // ...
  const load = async () => {
    // ...long async operation
    history.forEach((msg: any) => {
      addMessage({...})  // Race: messages.length may have changed
    })
  }
  load()
}, [status, messages.length, addMessage, setConversationId])
```

**Issue:** The `messages.length > 0` check happens before async `load()` completes. If a user sends a message during loading, new message gets added, then history loads and adds duplicate messages or corrupts conversation state.

**Impact:** Duplicate messages in UI, conversation state corruption.

---

### 4. XSS Vulnerability: Unescaped User Content in Graph Canvas

**File:** `apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx:159-160`

**Code:**
```typescript
let label = c.title || c.preview || "Session";
if (label.length > 20) label = label.substring(0, 20) + "...";
```

**Issue:** Conversation title from API is directly rendered to canvas via `ctx.fillText()` at line 292 without sanitization. If title contains control characters or injection payloads, they render directly.

**Impact:** Potential canvas injection attacks, UI corruption.

---

### 5. State Corruption: Clearing Conversation While Streaming

**File:** `apps/desktop/src/components/chat/ChatShell\ChatShell.tsx:70, apps/desktop/src/components/chat/ChatFullView\ChatFullView.tsx:35-37`

**Code:**
```typescript
<button onClick={() => clearConversation()}>
  New
</button>
```

**Issue:** User can click "New Chat" while AI is streaming a response. This clears `messages` and `conversationId` but doesn't cancel the ongoing stream. The stream completion handler then tries to add a message to a cleared conversation, causing state corruption.

**Impact:** Messages appear in wrong conversations, orphaned streaming state, UI crashes.

---

### 6. Uncaught Promise Rejection: No Error Boundary

**File:** `apps/desktop/src/hooks/useJarvisChat.ts:182-187, apps/desktop/src/services/jarvisApi.ts` (all async functions)

**Code:**
```typescript
} catch (error) {
  console.error("sendUserMessage failed:", error)
  useConversationStore.getState().finishStreaming()
  setStatus("error")
  setTyping(false)
}
```

**Issue:** No React Error Boundary to catch rendering errors or unhandled promise rejections. If any async API call rejects and isn't caught, it crashes the entire app.

**Impact:** App crashes with white screen on network errors.

---

### 7. Regex Catastrophic Backtracking Vulnerability

**File:** `apps/desktop/src/utils/uiActionParser.ts:11`

**Code:**
```typescript
const ACTION_REGEX = /\[UI_ACTION:([^\]]+)\]/g
```

**Issue:** The pattern `[^\]]+` can cause catastrophic backtracking if the AI returns a malformed tag like `[UI_ACTION:` followed by thousands of non-`]` characters with no closing bracket.

**Impact:** Frontend freeze/hang when processing malicious AI response.

---

### 8. Synchronous localStorage Access Blocks Rendering

**File:** `apps/desktop/src/stores/useConversationStore.ts:36-37, 41`

**Code:**
```typescript
setConversationId: (id) => {
  window.localStorage?.setItem("jarvis_conversation_id", id);  // SYNC
  set({ currentConversationId: id });
}
```

**Issue:** Synchronous `localStorage` access on every conversation ID change. If localStorage is slow (disk latency, quota exceeded), it blocks the render thread.

**Impact:** UI freezes during conversation switches.

---

## P2 - HIGH PRIORITY BUGS

### 9. No Abort Signal for Fetch Requests

**File:** `apps/desktop/src/services/jarvisApi.ts:37-44, 118-127`

**Code:**
```typescript
const response = await window.fetch(
  `${JARVIS_ENGINE_URL}/chat`,
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  }
)
```

**Issue:** No `AbortController` for any fetch request. User cannot cancel an in-flight request. If component unmounts, fetch continues in background.

**Impact:** Wasted network resources, memory leaks, stale state updates after unmount.

---

### 10. Silent Error Swallowing in API Calls

**File:** `apps/desktop/src/services/jarvisApi.ts:202-218, 221-238, 240-257`

**Code:**
```typescript
export async function setOpenRouterKey(apiKey: string): Promise<void> {
  try {
    await window.fetch(...)
  } catch {
    console.error("Failed to set OpenRouter key")  // Only logs, no throw
  }
}
```

**Issue:** API key setting functions swallow all errors silently. Caller has no way to know if the operation succeeded.

**Impact:** User thinks API key is saved but it's not. Silent failures.

---

### 11. Infinite Re-render Loop Potential

**File:** `apps/desktop/src/hooks/useEngineStatus.ts:8-45`

**Code:**
```typescript
useEffect(() => {
  const check = async () => {
    // ...
    useAIStore.getState().setProvider(activeProvider.name as any)
    useAIStore.getState().setModel(activeProvider.model)
  }
  check()
  const interval = window.setInterval(check, 30000)
  return () => {
    window.clearInterval(interval)
    window.clearInterval(memoryInterval)
  }
}, [setStatus, setError, setMemoryCount])
```

**Issue:** If `setProvider` or `setModel` trigger a re-render of a parent component that depends on these values, and that parent re-mounts this hook, it can cause an infinite loop. Also, `setStatus/setError/setMemoryCount` in deps are Zustand setters which are stable, but if they weren't, this would re-run constantly.

**Impact:** Potential infinite re-renders, excessive API calls.

---

### 12. Missing Cleanup for Animation Frame

**File:** `apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx:462, 464-467`

**Code:**
```typescript
animationId = requestAnimationFrame(loop);

return () => {
  window.removeEventListener("resize", sizeCanvas);
  cancelAnimationFrame(animationId);
};
```

**Issue:** `animationId` is a local variable inside the effect. If the effect re-runs before cleanup, the old `animationId` is lost, and the old animation loop continues forever.

**Impact:** Multiple animation loops run simultaneously, causing performance degradation and memory leaks.

---

### 13. Async State Update After Unmount

**File:** `apps/desktop/src/utils/uiActionExecutor.ts:17-30, 38-48, 52-76, 79-106`

**Code:**
```typescript
case "new_chat":
  import("../stores/useConversationStore").then(m => {
    m.useConversationStore.getState().clearConversation()
    if (action.payload) {
      const newId = window.crypto?.randomUUID() || Math.random().toString()
      m.useConversationStore.getState().setConversationId(newId)
      import("../services/jarvisApi").then(api => {
        api.updateConversationTitle(newId, action.payload!).then(() => {
          m.useConversationStore.getState().setConversationTitle(action.payload!)
        })
      })
    }
  })
```

**Issue:** Multiple chained async operations with no cancellation. If component unmounts during this chain, state updates still fire.

**Impact:** State updates on unmounted components, console warnings, potential memory leaks.

---

### 14. Canvas Context Lost on Resize

**File:** `apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx:184-192`

**Code:**
```typescript
const sizeCanvas = () => {
  if (!wrapRef.current) return;
  const rect = wrapRef.current.getBoundingClientRect();
  canvas.width = rect.width * window.devicePixelRatio;
  canvas.height = rect.height * window.devicePixelRatio;
  canvas.style.width = rect.width + "px";
  canvas.style.height = rect.height + "px";
  ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
}
```

**Issue:** Changing `canvas.width` or `canvas.height` **clears the entire canvas** and resets the context. The `ctx.setTransform` happens after clear, but the canvas is blank until next draw. During rapid resizes, canvas flickers.

**Impact:** Visual glitches, flickering canvas during window resize.

---

### 15. No Debounce on Auto-Growing Textarea

**File:** `apps/desktop/src/components/chat/ChatComposer/ChatComposer.tsx:22-30`

**Code:**
```typescript
useEffect(() => {
  const textarea = textareaRef.current;
  if (!textarea) return;
  textarea.style.height = "auto";
  const nextHeight = Math.min(textarea.scrollHeight, 120);
  textarea.style.height = `${nextHeight}px`;
}, [inputText]);
```

**Issue:** Effect runs on **every keystroke**. Causes forced reflow/layout recalculation on each character typed. No debouncing.

**Impact:** Input lag on slower devices, performance degradation with long text.

---

### 16. Hardcoded 500ms Delay for UI Actions

**File:** `apps/desktop/src/hooks/useJarvisChat.ts:122-124`

**Code:**
```typescript
setTimeout(() => {
  executeUIActions(actions)
}, 500)
```

**Issue:** Arbitrary 500ms delay before executing UI actions. If AI response is short, user waits unnecessarily. If response is long, 500ms may not be enough for DOM update.

**Impact:** Poor UX, timing issues with UI actions.

---

### 17. No Validation on Conversation Title Length

**File:** `apps/desktop/src/utils/uiActionExecutor.ts:57, 67`

**Code:**
```typescript
api.updateConversationTitle(currentId, action.payload!).then(...)
```

**Issue:** `action.payload` (conversation title) is sent to API without validation. Backend may have length limits. No client-side check.

**Impact:** API errors, user sees error feedback with no context.

---

### 18. Streaming Content Regex Performance Issue

**File:** `apps/desktop/src/stores/useConversationStore.ts:53-55`

**Code:**
```typescript
appendStreamToken: (token) => set((state) => ({ 
  streamingContent: (state.streamingContent + token).replace(/\[UI_ACTION:[^\]]*\]/g, "")
}))
```

**Issue:** Regex runs on **every token** appended, scanning the entire accumulated `streamingContent`. For a 2000-word response streamed one word at a time, this is O(n²) complexity.

**Impact:** Severe performance degradation during long AI responses.

---

### 19. GraphCanvas: hubNodesRef Not Updated on Conversation Changes

**File:** `apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx:152-175`

**Code:**
```typescript
useEffect(() => {
  // Initialize nodes
  hubNodesRef.current = HUBS.map(...)
  // Fetch dynamic conversations
  import("../services/jarvisApi").then(({ getConversations }) => {
    getConversations().then(data => {
      const convoHub = hubNodesRef.current.find(h => h.key === "conversations");
      if (convoHub) {
        convoHub.leavesList = recent.map(...)
      }
    })
  })
}, [])  // Empty deps - runs ONCE
```

**Issue:** Conversations are fetched ONCE on mount. If user creates/deletes conversations, the graph never updates. Empty dependency array means no re-fetch.

**Impact:** Stale conversation list in graph visualization.

---

### 20. No Loading State During Conversation Load

**File:** `apps/desktop/src/hooks/useConversationLoader.ts:34-95`

**Code:**
```typescript
const load = async () => {
  try {
    const history = await getConversation(savedId)
    // ...
    history.forEach((msg: any) => {
      addMessage({...})
    })
  } catch (error) {
    // ...
  }
}
load()
```

**Issue:** No loading indicator while fetching conversation history. User sees blank screen until load completes.

**Impact:** Poor UX, user thinks app is frozen.

---

## P3 - MEDIUM PRIORITY BUGS

### 21. Fallback to Math.random() for IDs

**Files:** Multiple locations

**Code:**
```typescript
id: window.crypto?.randomUUID() || Math.random().toString()
```

**Issue:** `Math.random()` is not cryptographically secure and has collision risk. Used as fallback for message IDs.

**Impact:** Potential ID collisions in environments without `crypto.randomUUID()`.

---

### 22. No Validation on Search Source Data

**File:** `apps/desktop/src/hooks/useJarvisChat.ts:106-112`

**Code:**
```typescript
sources: Array.isArray(sources)
  ? sources.map(s => ({
      title: String(s?.title || ""),
      url: String(s?.url || ""),
      snippet: String(s?.snippet || ""),
      source: String(s?.source || "")
    }))
  : []
```

**Issue:** No URL validation. Malicious backend could return `javascript:` URLs or XSS payloads in title/snippet.

**Impact:** Potential XSS if sources are rendered as links without sanitization.

---

### 23. Hardcoded Engine URL

**File:** `apps/desktop/src/services/jarvisApi.ts:3`

**Code:**
```typescript
export const JARVIS_ENGINE_URL = "http://localhost:8765"
```

**Issue:** Hardcoded URL. No environment variable support. Cannot connect to remote engines or different ports.

**Impact:** Cannot configure for different environments without code change.

---

### 24. No Retry Logic for Health Checks

**File:** `apps/desktop/src/hooks/useEngineStatus.ts:9-28`

**Code:**
```typescript
const check = async () => {
  try {
    const health = await checkHealth()
    // ...
  } catch {
    setStatus("offline")
    setError("JARVIS engine not running")
  }
}
```

**Issue:** Single failed health check marks engine as offline. No retry with backoff. Transient network errors cause false negatives.

**Impact:** Engine shows offline on temporary network glitches.

---

### 25. Timezone Issues with Timestamp Formatting

**File:** `apps/desktop/src/components/chat/ChatFullView/ChatFullView.tsx:39-51`

**Code:**
```typescript
const formatTime = (timestamp: string) => {
  if (!timestamp) return "";
  try {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return timestamp;
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return timestamp;
  }
};
```

**Issue:** No timezone handling. Backend sends UTC, frontend shows local time without indication. Inconsistent with backend timestamp format.

**Impact:** Confusing timestamps, time math errors.

---

### 26. No Max Length on Input Text

**File:** `apps/desktop/src/components/chat/ChatComposer/ChatComposer.tsx:52-53`

**Code:**
```typescript
const isOverLimit = inputText.length > 500;
const isSendDisabled = disabled || inputText.trim().length === 0;
```

**Issue:** Shows warning at 500 chars but doesn't prevent sending. User can send 10,000 character message.

**Impact:** Backend may reject, or waste resources processing huge messages.

---

### 27. Duplicate Message Rendering Logic

**Files:** `apps/desktop/src/components/chat/ChatShell/ChatShell.tsx:39-48` and `apps/desktop/src/components/chat/ChatFullView/ChatFullView.tsx:61-71`

**Code:**
```typescript
// Both files have identical logic
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
```

**Issue:** Same logic duplicated in two components. No shared hook or util.

**Impact:** Maintenance burden, potential divergence.

---

### 28. No Null Check on Canvas getBoundingClientRect

**File:** `apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx:470-479`

**Code:**
```typescript
const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
  const canvas = canvasRef.current;
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
```

**Issue:** If canvas is being removed from DOM during click handler, `getBoundingClientRect()` may throw or return unexpected values.

**Impact:** Potential runtime errors on rapid interactions.

---

### 29. Graph Caption Timer Not Cleaned Up

**File:** `apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx:44-52`

**Code:**
```typescript
useEffect(() => {
  if (graphOpen) {
    setShowCaption(true);
    const timer = setTimeout(() => setShowCaption(false), 3000);
    return () => clearTimeout(timer);
  } else {
    setShowCaption(true);  // No timer cleanup in else branch
  }
}, [graphOpen]);
```

**Issue:** When `graphOpen` is false, there's no timer but also no cleanup of previous timer if graphOpen changed from true→false→true rapidly.

**Impact:** Caption flickers, stale timers accumulate.

---

### 30. No Error Handling in Dynamic Imports

**Files:** Multiple `executeUIActions` cases

**Code:**
```typescript
import("../stores/useConversationStore").then(m => {
  m.useConversationStore.getState().clearConversation()
})
```

**Issue:** Dynamic imports have no `.catch()`. If import fails (rare but possible with module loading errors), it's silently ignored.

**Impact:** UI actions fail silently, user gets no feedback.

---

### 31. Floating Point Precision in Canvas Calculations

**File:** `apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx:450`

**Code:**
```typescript
stateRef.current.angleBase += 0.0018 * speedMultiplier;
```

**Issue:** Accumulating floating point errors over long runtime. After hours, `angleBase` could drift.

**Impact:** Graph rotation becomes jittery after extended use.

---

### 32. No Debounce on Mouse Move Events

**File:** `apps/desktop/src/components/graph/GraphCanvas/GraphCanvas.tsx:572-578`

**Code:**
```typescript
const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
  const canvas = canvasRef.current;
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  stateRef.current.mouseX = e.clientX - rect.left;
  stateRef.current.mouseY = e.clientY - rect.top;
};
```

**Issue:** `getBoundingClientRect()` called on EVERY mouse move. Expensive reflow calculation.

**Impact:** High CPU usage when moving mouse over canvas.

---

### 33. Search Badge Visibility Logic Incomplete

**File:** `apps/desktop/src/components/chat/ChatFullView/ChatFullView.tsx:101, 122`

**Code:**
```typescript
<SearchBadge query={msg.searchQuery || ""} visible={msg.searchPerformed === true} />
<SourcesList sources={msg.sources || []} visible={msg.searchPerformed === true} />
```

**Issue:** If `searchPerformed` is undefined (default for old messages), badge never shows even if `searchQuery` exists.

**Impact:** Search indicators missing for some messages.

---

### 34. No Scroll Restoration on Navigation

**File:** `apps/desktop/src/components/chat/ConversationArea/ConversationArea.tsx:21-25`

**Code:**
```typescript
useEffect(() => {
  if (typeof bottomRef.current?.scrollIntoView === "function") {
    bottomRef.current.scrollIntoView({ behavior: "smooth" });
  }
}, [messages, isTyping, streamingContent]);
```

**Issue:** Always scrolls to bottom on ANY message change. If user scrolls up to read history, they're yanked back down.

**Impact:** Cannot read message history while new messages arrive.

---

### 35. Inconsistent String Comparison (Case Sensitivity)

**File:** `apps/desktop/src/utils/uiActionExecutor.ts:40, 84, 103`

**Code:**
```typescript
const target = convos.find(c => c.title.toLowerCase().includes(action.payload!.toLowerCase()))
```

**Issue:** Case-insensitive search for conversations, but exact match might be better. "AI News" matches "AI news summary".

**Impact:** Wrong conversation selected if multiple partial matches exist.

---

## P4 - LOW PRIORITY / CODE QUALITY

### 36. Type Casting with `as any` in Multiple Locations

**Files:** `apps/desktop/src/hooks/useEngineStatus.ts:18`, `apps/desktop/src/utils/uiActionExecutor.ts:164`

**Code:**
```typescript
useAIStore.getState().setProvider(activeProvider.name as any)
m.useAIStore.getState().setProvider(action.payload as any)
```

**Issue:** Type safety bypassed with `as any`. Provider name might not match the allowed literal types.

**Impact:** Runtime type errors, provider mismatch.

---

### 37. Inconsistent Error Message Formatting

**Files:** Multiple API functions

**Code:**
```typescript
throw new Error(`Chat request failed: ${response.status}`)  // Template literal
throw new Error("Health check failed")  // String literal
```

**Issue:** No consistent error message format across API layer.

**Impact:** Difficult to parse errors programmatically.

---

### 38. No TypeScript Strict Mode Violations

**Files:** Multiple files with `/* eslint-disable no-unused-vars */`

**Issue:** ESLint rule disabled at file level instead of fixing the issues. Unused variables and imports remain.

**Impact:** Code clutter, potential bugs from dead code.

---

### 39. Hardcoded Magic Numbers

**Examples:**
- `ChatComposer.tsx:52` - `500` character limit
- `GraphCanvas.tsx:366-368` - `0.12`, `0.70` radius multipliers
- `useAppStore.ts:51` - `5000` ms timeout
- `useEngineStatus.ts:38-39` - `30000`, `60000` intervals

**Issue:** No constants defined, hard to maintain.

**Impact:** Difficult to tune behavior consistently.

---

### 40. Duplicate Timestamp Formatting Logic

**Files:** Multiple components format timestamps differently

**Issue:** No shared utility for timestamp formatting. Some use `toLocaleTimeString`, some use `toISOString`.

**Impact:** Inconsistent timestamp display.

---

### 41. No PropTypes or Runtime Validation

**Files:** All React components

**Issue:** TypeScript provides compile-time types, but no runtime validation of props.

**Impact:** Unexpected runtime errors if props are wrong shape at runtime.

---

### 42. Streaming Content Not Cleared on Error

**File:** `apps/desktop/src/hooks/useJarvisChat.ts:151-179`

**Code:**
```typescript
// onError
(error: string) => {
  try {
    useConversationStore.getState().finishStreaming()
    const currentContent = useConversationStore.getState().streamingContent
    if (!currentContent || currentContent.trim().length === 0) {
      // Add error message
    }
    // streamingContent is cleared in finishStreaming()
```

**Issue:** If streaming has partial content and then errors, the partial content is cleared but not saved as a message.

**Impact:** User loses partial AI response on error.

---

### 43. useConversationLoader Depends on Unstable Reference

**File:** `apps/desktop/src/hooks/useConversationLoader.ts:97`

**Code:**
```typescript
}, [status, messages.length, addMessage, setConversationId])
```

**Issue:** `addMessage` and `setConversationId` are Zustand actions (stable), but including them in deps is unnecessary. `messages.length` changes during the effect's execution, causing potential issues.

**Impact:** Effect may re-run unexpectedly.

---

## RECOMMENDATIONS

### Immediate Actions (P1 Issues)

1. **Add React Error Boundary** to catch unhandled promise rejections and rendering errors
2. **Implement AbortController** for all fetch requests with cleanup on unmount
3. **Add timer cleanup** in all setTimeout/setInterval usages with refs to track IDs
4. **Prevent concurrent operations**: Disable "New Chat" button while streaming
5. **Sanitize all user-generated content** before rendering to canvas or DOM
6. **Add cancellation checks** in async chains before state updates
7. **Debounce regex operations** in streaming content processing
8. **Move localStorage to async utility** with debouncing

### Short-term Actions (P2 Issues)

1. **Implement retry logic** for API calls with exponential backoff
2. **Add loading states** for all async operations
3. **Fix animation frame cleanup** by using useRef for animationId
4. **Add validation** on all user inputs (title length, message length)
5. **Implement proper error propagation** in API layer
6. **Add URL validation** for search sources
7. **Fix canvas resize** to prevent flicker
8. **Add debouncing** to textarea auto-grow

### Long-term Improvements (P3/P4 Issues)

1. **Create shared hooks** for common patterns (timestamp formatting, message aggregation)
2. **Implement environment config** for API URLs and timeouts
3. **Add comprehensive input validation** library (Zod)
4. **Create constants file** for all magic numbers
5. **Implement scroll restoration** logic for chat area
6. **Add TypeScript strict mode** and fix all violations
7. **Create error handling utilities** with consistent formatting
8. **Implement real-time graph updates** when conversations change
9. **Add comprehensive unit tests** for all hooks and utilities
10. **Create performance monitoring** for canvas operations

---

**End of Report**

*JARVIS Desktop App Bug Audit - August 17, 2026 - Confidential*
