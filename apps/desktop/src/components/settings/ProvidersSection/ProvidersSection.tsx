import { useState, useEffect } from "react";
import { Button } from "../../ui/Button/Button";
import { getSettings, updateProviderConfig } from "../../../services/jarvisApi";

export function ProvidersSection() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string, type: "success" | "error" } | null>(null);

  const [geminiKey, setGeminiKey] = useState("");
  const [groqKey, setGroqKey] = useState("");
  const [openrouterKey, setOpenrouterKey] = useState("");
  const [ollamaHost, setOllamaHost] = useState("");

  const [configured, setConfigured] = useState({
    gemini: false,
    groq: false,
    openrouter: false,
    ollama: false
  });

  const fetchConfig = async () => {
    try {
      const settings = await getSettings();
      setConfigured({
        gemini: !!settings.gemini_configured,
        groq: !!settings.groq_configured,
        openrouter: !!settings.openrouter_configured,
        ollama: !!settings.ollama_configured,
      });
    } catch (err) {
      console.error("Failed to fetch provider config status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const payload: any = {};
      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
      if (groqKey.trim()) payload.groq_api_key = groqKey.trim();
      if (openrouterKey.trim()) payload.openrouter_api_key = openrouterKey.trim();
      if (ollamaHost.trim()) payload.ollama_host = ollamaHost.trim();

      if (Object.keys(payload).length === 0) {
        setMessage({ text: "No changes to save.", type: "error" });
        return;
      }

      await updateProviderConfig(payload);
      
      setGeminiKey("");
      setGroqKey("");
      setOpenrouterKey("");
      setOllamaHost("");
      
      setMessage({ text: "Provider configuration updated successfully! Changes take effect immediately.", type: "success" });
      await fetchConfig();
    } catch (err) {
      console.error(err);
      setMessage({ text: "Failed to save configuration.", type: "error" });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-6 text-[var(--color-text-secondary)]">Loading...</div>;
  }

  const renderField = (
    label: string, 
    value: string, 
    onChange: (value: string) => void,
    isConfigured: boolean,
    placeholder: string
  ) => (
    <div className="flex flex-col gap-2 p-4 rounded-lg bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-[var(--color-text-primary)]">{label}</label>
        {isConfigured && (
          <span className="text-xs px-2 py-1 rounded-full bg-[var(--color-primary-500)] bg-opacity-20 text-[var(--color-primary-400)] font-medium">
            Active Override
          </span>
        )}
      </div>
      <input
        type={label.includes("Host") ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={isConfigured ? "••••••••••••••••" : placeholder}
        className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-2 text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-primary-500)]"
      />
    </div>
  );

  return (
    <div className="flex flex-col gap-[var(--space-6)] p-6 max-w-2xl">
      <div className="flex flex-col gap-[var(--space-2)]">
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">
          Providers
        </h2>
        <p className="text-[var(--color-text-secondary)]">
          Configure API keys and endpoints dynamically without restarting JARVIS. Saved values override .env defaults. Leave fields empty to keep current values.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        {renderField("Gemini API Key", geminiKey, setGeminiKey, configured.gemini, "Enter new Gemini key...")}
        {renderField("Groq API Key", groqKey, setGroqKey, configured.groq, "Enter new Groq key...")}
        {renderField("OpenRouter API Key", openrouterKey, setOpenrouterKey, configured.openrouter, "Enter new OpenRouter key...")}
        {renderField("Ollama Host", ollamaHost, setOllamaHost, configured.ollama, "e.g. http://192.168.1.x:11434")}
      </div>

      <div className="flex items-center justify-between mt-2">
        <div className="flex-1">
          {message && (
            <p className={`text-sm ${message.type === "success" ? "text-green-400" : "text-red-400"}`}>
              {message.text}
            </p>
          )}
        </div>
        <Button 
          variant="primary" 
          onClick={handleSave} 
          disabled={saving || (!geminiKey && !groqKey && !openrouterKey && !ollamaHost)}
        >
          {saving ? "Saving..." : "Save Providers"}
        </Button>
      </div>
    </div>
  );
}
