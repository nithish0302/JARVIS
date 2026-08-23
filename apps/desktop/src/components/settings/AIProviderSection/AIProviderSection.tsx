/* global HTMLSelectElement */
import { useState } from "react";
import type { ChangeEvent } from "react";
import { SettingsSection } from "../SettingsSection/SettingsSection";
import { Select } from "../../ui/Select/Select";
import { Input } from "../../ui/Input/Input";
import { Button } from "../../ui/Button/Button";
import { Switch } from "../../ui/Switch/Switch";
import { useAIStore } from "../../../stores/useAIStore";
import { switchProvider, checkHealth, updateSettings } from "../../../services/jarvisApi";

export function AIProviderSection() {
  const {
    provider, setProvider,
    model, setModel,
    openrouterKey, setOpenrouterKey,
    groqKey, setGroqKey,
    geminiKey, setGeminiKey,
    personalityMode, setPersonalityMode,
    modifier, setModifier,
    addressPreference, setAddressPreference,
    dailyBriefingEnabled, setDailyBriefingEnabled
  } = useAIStore();
  
  const [testResult, setTestResult] = useState<string | null>(null);

  const [newPin, setNewPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [pinResult, setPinResult] = useState<string | null>(null);
  const [pinSaving, setPinSaving] = useState(false);

  const handleProviderChange = async (e: ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value as "ollama" | "openrouter" | "groq" | "gemini";
    setProvider(newProvider);
    await switchProvider(newProvider, model);
  };

  const handlePersonalityChange = async (e: ChangeEvent<HTMLSelectElement>) => {
    const newMode = e.target.value as "assistant" | "developer" | "research";
    setPersonalityMode(newMode);
    try {
      await updateSettings({ personality_mode: newMode });
    } catch (err) {
      console.error("Failed to update personality mode:", err);
    }
  };

  const handleModifierChange = async (e: ChangeEvent<HTMLSelectElement>) => {
    const newMod = e.target.value as "none" | "planner" | "quiet";
    setModifier(newMod);
    try {
      await updateSettings({ modifier: newMod });
    } catch (err) {
      console.error("Failed to update modifier:", err);
    }
  };

  const handleModelBlur = async () => {
    await switchProvider(provider, model);
  };

  const handleAddressPreferenceBlur = async () => {
    try {
      await updateSettings({ address_preference: addressPreference });
    } catch (err) {
      console.error("Failed to update address preference:", err);
    }
  };

  const handleDailyBriefingToggle = async (e: ChangeEvent<HTMLInputElement>) => {
    const enabled = e.target.checked;
    setDailyBriefingEnabled(enabled);
    try {
      await updateSettings({ daily_briefing_enabled: enabled });
    } catch (err) {
      console.error("Failed to update daily briefing setting:", err);
    }
  };

  const handleSavePin = async () => {
    if (!/^\d{4}$/.test(newPin)) {
      setPinResult("✗ PIN must be exactly 4 digits");
      return;
    }
    if (newPin !== confirmPin) {
      setPinResult("✗ PINs don't match");
      return;
    }
    setPinSaving(true);
    try {
      await updateSettings({ conversation_delete_pin: newPin });
      setPinResult("✓ Delete PIN updated");
      setNewPin("");
      setConfirmPin("");
    } catch (err) {
      console.error("Failed to update delete PIN:", err);
      setPinResult("✗ Failed to update PIN");
    } finally {
      setPinSaving(false);
    }
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
      description="Configure the AI engine, personality mode, and response modifiers."
      title="AI & Personality"
    >
      <div className="flex max-w-md flex-col gap-[var(--space-4)]">
        <Select 
          label="Personality Mode" 
          value={personalityMode} 
          onChange={handlePersonalityChange}
        >
          <option value="assistant">Assistant (Balanced, professional & warm)</option>
          <option value="developer">Developer (High technical precision, direct engineering tone)</option>
          <option value="research">Research (Investigative, deep analysis, citation-focused)</option>
        </Select>

        <Select 
          label="Response Modifier" 
          value={modifier} 
          onChange={handleModifierChange}
        >
          <option value="none">None (Standard response)</option>
          <option value="planner">Planner (Structured plans, step breakdown & validation)</option>
          <option value="quiet">Quiet (Ultra-concise, minimum words, zero filler)</option>
        </Select>

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

        <div className="flex flex-col gap-[var(--space-3)] border-t border-[var(--color-border)] pt-[var(--space-4)]">
          <div>
            <h3 className="text-[length:var(--font-size-body)] font-medium text-[var(--color-text-primary)]">
              Address Preference
            </h3>
            <p className="text-[length:var(--font-size-sm)] text-[var(--color-text-muted)]">
              How JARVIS addresses you (e.g. "sir", a name, "boss"). Leave blank for no title or name at all.
            </p>
          </div>
          <Input
            label="Address as"
            placeholder="sir"
            maxLength={20}
            value={addressPreference}
            onChange={(e) => setAddressPreference(e.target.value.slice(0, 20))}
            onBlur={handleAddressPreferenceBlur}
          />
        </div>

        <div className="flex flex-col gap-[var(--space-3)] border-t border-[var(--color-border)] pt-[var(--space-4)]">
          <Switch
            label="Daily Briefing"
            description="A brief greeting with the date, and anything notable (system status, relevant memories), on your first message each day."
            checked={dailyBriefingEnabled}
            onChange={handleDailyBriefingToggle}
          />
        </div>

        <div className="flex flex-col gap-[var(--space-3)] border-t border-[var(--color-border)] pt-[var(--space-4)]">
          <div>
            <h3 className="text-[length:var(--font-size-body)] font-medium text-[var(--color-text-primary)]">
              Conversation Delete PIN
            </h3>
            <p className="text-[length:var(--font-size-sm)] text-[var(--color-text-muted)]">
              The 4-digit PIN required to delete a conversation. Leave blank to keep the current one.
            </p>
          </div>
          <div className="flex flex-wrap items-end gap-[var(--space-3)]">
            <Input
              label="New PIN"
              placeholder="••••"
              type="password"
              inputMode="numeric"
              maxLength={4}
              value={newPin}
              onChange={(e) => setNewPin(e.target.value.replace(/\D/g, "").slice(0, 4))}
            />
            <Input
              label="Confirm PIN"
              placeholder="••••"
              type="password"
              inputMode="numeric"
              maxLength={4}
              value={confirmPin}
              onChange={(e) => setConfirmPin(e.target.value.replace(/\D/g, "").slice(0, 4))}
            />
            <Button variant="secondary" onClick={handleSavePin} disabled={pinSaving}>
              {pinSaving ? "Saving..." : "Save PIN"}
            </Button>
          </div>
          {pinResult && (
            <span className={`text-[length:var(--font-size-sm)] ${
              pinResult.startsWith("✓")
                ? "text-[var(--color-success)]"
                : "text-[var(--color-error)]"
            }`}>
              {pinResult}
            </span>
          )}
        </div>
      </div>
    </SettingsSection>
  );
}
