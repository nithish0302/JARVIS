/* global HTMLSelectElement */
import { useState } from "react";
import type { ChangeEvent } from "react";
import { SettingsSection } from "../SettingsSection/SettingsSection";
import { Select } from "../../ui/Select/Select";
import { Input } from "../../ui/Input/Input";
import { Button } from "../../ui/Button/Button";
import { useAIStore } from "../../../stores/useAIStore";
import { switchProvider, checkHealth, setOpenRouterKey } from "../../../services/jarvisApi";

export function AIProviderSection() {
  const { 
    provider, setProvider, 
    model, setModel, 
    openrouterKey, setOpenrouterKey 
  } = useAIStore();
  
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleProviderChange = async (e: ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value as "ollama" | "openrouter" | "claude";
    setProvider(newProvider);
    await switchProvider(newProvider, model);
  };

  const handleModelBlur = async () => {
    await switchProvider(provider, model);
  };

  const testConnection = async () => {
    try {
      const health = await checkHealth();
      const current = health.providers.find(p => p.name === provider);
      if (current?.available) {
        setTestResult(`✓ Connected · ${current.model}`);
      } else {
        setTestResult("✗ Offline");
      }
    } catch {
      setTestResult("✗ Offline");
    }
  };
  
  const suggestions = provider === "ollama" ? [
    { id: "llama3.2:3b", desc: "current" },
    { id: "qwen2.5-coder:3b", desc: "coding" },
    { id: "mistral:7b", desc: "reasoning" },
    { id: "phi3:mini", desc: "fast" }
  ] : provider === "openrouter" ? [
    { id: "google/gemma-4-27b-it:free", desc: "general" },
    { id: "google/gemma-4-31b-it:free", desc: "reasoning" },
    { id: "meta-llama/llama-3.3-70b-instruct:free", desc: "capable" },
    { id: "qwen/qwen3-235b-a22b:free", desc: "coding" }
  ] : [];

  return (
    <SettingsSection
      description="Configure the AI engine that powers JARVIS."
      title="AI Provider"
    >
      <div className="flex max-w-md flex-col gap-[var(--space-4)]">
        <Select 
          label="Provider" 
          value={provider} 
          onChange={handleProviderChange}
        >
          <option value="ollama">Ollama (Local)</option>
          <option value="openrouter">OpenRouter</option>
          <option value="nvidia">NVIDIA NIM</option>
          <option value="openai">OpenAI</option>
        </Select>
        
        <div>
          <Input 
            label="Model name" 
            placeholder="e.g. qwen2.5:7b" 
            value={model}
            onChange={(e) => setModel(e.target.value)}
            onBlur={handleModelBlur}
          />
          
          {suggestions.length > 0 && (
            <div className="mt-[var(--space-2)] flex flex-wrap gap-[var(--space-2)]">
              {suggestions.map(s => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => {
                    setModel(s.id);
                    switchProvider(provider, s.id);
                  }}
                  className="flex flex-col items-start rounded border border-[var(--color-border)] bg-[var(--color-surface-sunken)] p-[var(--space-2)] hover:border-[var(--color-primary)] transition-colors"
                >
                  <span className="text-[length:var(--font-size-sm)] font-medium text-[var(--color-text-primary)]">
                    {s.id}
                  </span>
                  <span className="text-[length:var(--font-size-xs)] text-[var(--color-text-secondary)]">
                    {s.desc}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
        
        <Input
          label="OpenRouter API Key"
          placeholder="sk-or-..."
          type="password"
          description="Required for cloud fallback"
          value={openrouterKey}
          onChange={(e) => setOpenrouterKey(e.target.value)}
          onBlur={() => setOpenRouterKey(openrouterKey)}
        />
        
        <div className="flex items-center gap-[var(--space-3)]">
          <Button variant="secondary" onClick={testConnection}>
            Test Connection
          </Button>
          {testResult && (
            <span className={`text-[length:var(--font-size-sm)] ${
              testResult.includes("Connected") 
                ? "text-[var(--color-success)]" 
                : "text-[var(--color-error)]"
            }`}>
              {testResult}
            </span>
          )}
        </div>
      </div>
    </SettingsSection>
  );
}
