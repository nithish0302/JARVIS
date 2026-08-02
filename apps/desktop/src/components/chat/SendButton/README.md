# SendButton

An icon button specifically designed to submit user messages within the `ChatComposer`.

## Features
- Uses the `IconButton` component and `Send` icon from `lucide-react`.
- Supports disabled state when the input is empty or the application is busy.
- Adheres to the `--color-accent` design token for strong visual primary hierarchy.

## Example

```tsx
import { SendButton } from "./SendButton";

<SendButton 
  disabled={inputText.length === 0} 
  onClick={() => handleSend(inputText)} 
/>
```
