import { SettingsSection } from "../SettingsSection/SettingsSection";
import { Select } from "../../ui/Select/Select";
import { Input } from "../../ui/Input/Input";

export function AIProviderSection() {
  return (
    <SettingsSection
      description="Configure the AI engine that powers JARVIS."
      title="AI Provider"
    >
      <div className="flex max-w-md flex-col gap-[var(--space-4)]">
        <Select label="Provider">
          <option value="ollama">Ollama (Local)</option>
          <option value="openrouter">OpenRouter</option>
          <option value="nvidia">NVIDIA NIM</option>
          <option value="openai">OpenAI</option>
        </Select>
        <Input label="Model name" placeholder="e.g. qwen2.5:7b" />
      </div>
    </SettingsSection>
  );
}
