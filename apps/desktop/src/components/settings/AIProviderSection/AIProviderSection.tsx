import { useState } from "react";
import type { ChangeEvent } from "react";
import { SettingsSection } from "../SettingsSection/SettingsSection";
import { Select } from "../../ui/Select/Select";
import { Input } from "../../ui/Input/Input";
import { Button } from "../../ui/Button/Button";
import { useAIStore } from "../../../stores/useAIStore";
import { switchProvider, checkHealth, updateSettings } from "../../../services/jarvisApi";
import { CURRENT_MODEL_DEFAULTS } from "../../../data/currentModels";

export function AIProviderSection() {
  const {
    provider, setProvider,
    model, setModel,
    openrouterKey, setOpenrouterKey,
    groqKey, setGroqKey,
    geminiKey, setGeminiKey,
    providerOverride, setProviderOverride,
    fallbackMode, setFallbackMode,
  } = useAIStore();

  const [testResult, setTestResult] = useState<string | null>(null);

  const handleProviderOverrideChange = async (e: ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value === "none" ? null : e.target.value as "ollama" | "openrouter" | "groq" | "gemini";
    setProviderOverride(value);
    try {
      await updateSettings({ provider_override: value });
    } catch (err) {
      console.error("Failed to update provider override:", err);
    }
  };

  const handleFallbackModeChange = async (e: ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value as "auto" | "ask";
    setFallbackMode(value);
    try {
      await updateSettings({ fallback_mode: value });
    } catch (err) {
      console.error("Failed to update fallback mode:", err);
    }
  };

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

  // Quick-picks for ollama/groq/gemini come from CURRENT_MODEL_DEFAULTS (the
  // same single source of truth graphHubs.ts reads from), not a separate
  // hardcoded copy here - that's what let this list drift out of date with
  // core/config.py in the first place. OpenRouter has no single "current"
  // default in config.py, so its picks stay hand-curated.
  const suggestions = provider === "ollama" ? [
    { id: CURRENT_MODEL_DEFAULTS.ollama, desc: "current" },
  ] : provider === "openrouter" ? [
    { id: "google/gemma-4-31b-it:free", desc: "general" },
    { id: "google/gemma-4-26b-a4b:free", desc: "reasoning" },
    { id: "nvidia/nemotron-3-ultra-550b-a55b:free", desc: "capable" }
  ] : provider === "groq" ? [
    { id: CURRENT_MODEL_DEFAULTS.groq, desc: "current" },
  ] : provider === "gemini" ? [
    { id: CURRENT_MODEL_DEFAULTS.gemini, desc: "current" },
  ] : [];

  return (
    <SettingsSection
      description="Configure the AI engine provider, model, and API credentials."
      title="AI Provider"
    >
      <div className="flex max-w-md flex-col gap-[var(--space-4)]">
        <Select
          label="Provider"
          value={provider}
          onChange={handleProviderChange}
        >
          <option value="gemini">{`Gemini (${CURRENT_MODEL_DEFAULTS.gemini} - Fast)`}</option>
          <option value="openrouter">OpenRouter (Gemma 4 31B - Recommended)</option>
          <option value="groq">{`Groq (${CURRENT_MODEL_DEFAULTS.groq} - Fast)`}</option>
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

        <Select
          label="Provider override"
          description="Locks the AI brain to ONLY this provider - no fallback cascade, fails cleanly instead of silently substituting another provider."
          value={providerOverride ?? "none"}
          onChange={handleProviderOverrideChange}
        >
          <option value="none">None (normal fallback cascade)</option>
          <option value="gemini">Gemini only</option>
          <option value="openrouter">OpenRouter only</option>
          <option value="groq">Groq only</option>
          <option value="ollama">Ollama only</option>
        </Select>

        <Select
          label="Fallback mode"
          description="When a provider fails: Auto immediately tries the next one. Ask pauses and asks which provider to use next."
          value={fallbackMode}
          onChange={handleFallbackModeChange}
        >
          <option value="auto">Auto (switch automatically)</option>
          <option value="ask">Ask before switching</option>
        </Select>
      </div>
    </SettingsSection>
  );
}
