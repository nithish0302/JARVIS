# JARVIS Stores

This directory contains the global state management for the JARVIS desktop client, powered by [Zustand](https://github.com/pmndrs/zustand).

## Design Philosophy

- **Small and Focused**: State is divided into logical domains rather than a single massive store.
- **Strictly Typed**: All stores use TypeScript interfaces with explicit types. No `any`.
- **No Business Logic**: Stores manage state and transitions, not complex business rules or API calls.
- **Frontend Only**: These stores exist only in the React runtime. Backend state is managed by the Rust or Python engines.

---

## Available Stores

### 1. `useConversationStore`
Manages the active chat conversation state between the user and JARVIS.

**State:**
- `messages`: Array of `Message` objects.
- `currentConversationId`: String ID of the active thread (or null).
- `isTyping`: Boolean indicating if the AI is currently generating a response.

**Actions:**
- `addMessage(message: Message)`: Appends a new message to the conversation.
- `setTyping(value: boolean)`: Toggles the typing indicator.
- `clearConversation()`: Resets the store to an empty state.

---

### 2. `useAIStore`
Manages the connection and configuration state of the AI engine.

**State:**
- `provider`: The active AI provider (`"ollama" | "openrouter" | "claude"`).
- `model`: The specific model identifier (e.g., `"llama3.2:3b"`).
- `status`: The current connection status (`"idle" | "connecting" | "streaming" | "error" | "offline"`).
- `isStreaming`: Boolean indicating active token generation.
- `error`: Any current error string (or null).

**Actions:**
- `setProvider(provider)`
- `setModel(model)`
- `setStatus(status)`
- `setStreaming(value)`
- `setError(error)`

---

### 3. `usePersonalityStore`
Manages the behavioral and tonal configuration of JARVIS.

**State:**
- `mode`: The overarching behavior preset (`"assistant" | "developer" | "focus" | "executive" | "learning" | "automation"`).
- `address`: How JARVIS refers to the user (`"sir" | "Nithish" | "boss"`).
- `formality`, `verbosity`, `humor`, `proactivity`: Numeric dials (0-100) fine-tuning the personality.

**Actions:**
- `setMode(mode)`
- `setAddress(address)`
- `setDial(key, value)`

---

### 4. `useAppStore`
Manages global application-level UI state that spans across multiple features.

**State:**
- `view`: The active full-screen view (`"chat" | "settings"`).

**Actions:**
- `setView(view)`
