# ChatComposer

The permanent input area where users type and send messages.

## Features
- **Auto-growing Textarea**: Automatically expands vertically as the user types (up to a visual limit) without relying on a full scrolling element immediately.
- **Keyboard Shortcuts**: Supports `Enter` to send, and `Shift+Enter` for a new line.
- **Character Count**: Warns the user when they exceed 500 characters by displaying a right-aligned token counter.
- **Accessible & Token-Driven**: Employs semantic design tokens directly on a standard HTML `<textarea>` to maintain high visual standards without forcing a visible field label.

## Example
```tsx
import { ChatComposer } from "./ChatComposer";

<ChatComposer 
  onSend={(msg) => console.log(msg)} 
  placeholder="Message JARVIS..." 
/>
```
