# ConversationArea

Main presentation container for the conversation flow. It receives the list of messages, passes them to the `MessageList`, and implements an auto-scroll to the bottom.

## Usage

```tsx
import { ConversationArea } from "./ConversationArea";

<ConversationArea messages={messagesArray} isTyping={true} />
```
