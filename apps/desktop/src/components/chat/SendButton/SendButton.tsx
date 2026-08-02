import { Send } from "lucide-react";
import { IconButton } from "../../ui/IconButton/IconButton";

export interface SendButtonProps {
  disabled?: boolean;
  onClick: () => void;
}

export function SendButton({ disabled = false, onClick }: SendButtonProps) {
  return (
    <IconButton
      aria-label="Send message"
      disabled={disabled}
      onClick={onClick}
      variant="primary"
    >
      <Send aria-hidden="true" className="size-[var(--font-size-lg)]" />
    </IconButton>
  );
}
