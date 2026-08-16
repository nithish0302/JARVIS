/* global HTMLSelectElement */
import { useState } from "react";
import type { ChangeEvent } from "react";
import { SettingsSection } from "../SettingsSection/SettingsSection";
import { Select } from "../../ui/Select/Select";
import { Input } from "../../ui/Input/Input";
import { Button } from "../../ui/Button/Button";
import { useAIStore } from "../../../stores/useAIStore";
import { switchProvider, checkHealth } from "../../../services/jarvisApi";

export function AIProviderSection() {
  const { 
    provider, setProvider, 
    model, setModel, 
    openrouterKey, setOpenrouterKey,
    groqKey, setGroqKey,
    geminiKey, setGeminiKey
  } = useAIStore();
  
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleProviderChange = async (e: ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value as "ollama" | "openrouter" | "groq" | "gemini";
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
    { id: "qwen2.5-coder:3b", desc: "coding" }
  ] : provider === "openrouter" ? [
    { id: "google/gemma-4-31b-it:free", desc: "general" },
    { id: "google/gemma-4-26b-a4b:free", desc: "reasoning" },
    { id: "nvidia/nemotron-3-ultra-550b-a55b:free", desc: "capable" }
  ] : provider === "groq" ? [
    { id: "llama-3.3-70b-versatile", desc: "fast" },
    { id: "llama3-70b-8192", desc: "versatile" }
  ] : provider === "gemini" ? [
    { id: "gemini-2.5-flash", desc: "flash" },
    { id: "gemini-2.5-pro", desc: "pro" }
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
          <option value="gemini">Gemini (2.5 Flash - Fast)</option>
          <option value="openrouter">OpenRouter (Gemma 4 31B - Recommended)</option>
          <option value="groq">Groq (Llama 3.3 70B - Fast)</option>
          <option value="ollama">Ollama (Local - Offline)</option>
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
        
        {provider === "openrouter" && (
          <Input
            label="OpenRouter API Key"
            placeholder="sk-or-..."
            type="password"
            description="Required for OpenRouter"
            value={openrouterKey}
            onChange={(e) => setOpenrouterKey(e.target.value)}
            onBlur={() => {
              import("../../../services/jarvisApi").then(m => m.setOpenRouterKey(openrouterKey))
            }}
          />
        )}
        {provider === "groq" && (
          <Input
            label="Groq API Key"
            placeholder="gsk_..."
            type="password"
            description="Required for Groq"
            value={groqKey}
            onChange={(e) => setGroqKey(e.target.value)}
            onBlur={() => {
              import("../../../services/jarvisApi").then(m => m.setGroqKey(groqKey))
            }}
          />
        )}
        {provider === "gemini" && (
          <Input
            label="Gemini API Key"
            placeholder="AIza..."
            type="password"
            description="Required for Gemini"
            value={geminiKey}
            onChange={(e) => setGeminiKey(e.target.value)}
            onBlur={() => {
              import("../../../services/jarvisApi").then(m => m.setGeminiKey(geminiKey))
            }}
          />
        )}
        
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
