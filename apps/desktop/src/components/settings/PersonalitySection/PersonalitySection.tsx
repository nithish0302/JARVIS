/* global HTMLSelectElement, HTMLInputElement */
import { useState } from "react";
import type { ChangeEvent } from "react";
import { SettingsSection } from "../SettingsSection/SettingsSection";
import { Select } from "../../ui/Select/Select";
import { Input } from "../../ui/Input/Input";
import { Button } from "../../ui/Button/Button";
import { Switch } from "../../ui/Switch/Switch";
import { Divider } from "../../ui/Divider/Divider";
import { useAIStore } from "../../../stores/useAIStore";
import { updateSettings } from "../../../services/jarvisApi";

const subHeadingClasses =
  "text-[length:var(--font-size-sm)] font-semibold uppercase tracking-wide text-[var(--color-text-secondary)]";

export function PersonalitySection() {
  const {
    personalityMode, setPersonalityMode,
    modifier, setModifier,
    addressPreference, setAddressPreference,
    dailyBriefingEnabled, setDailyBriefingEnabled
  } = useAIStore();

  const [newPin, setNewPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [pinResult, setPinResult] = useState<string | null>(null);
  const [pinSaving, setPinSaving] = useState(false);

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

  return (
    <SettingsSection
      description="Configure how JARVIS behaves, addresses you, and protects your conversations."
      title="Personality"
    >
      <div className="flex max-w-md flex-col gap-[var(--space-6)]">
        {/* --- Personality: mode, modifier, address preference, daily briefing --- */}
        <div className="flex flex-col gap-[var(--space-4)]">
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

          <Input
            label="Address as"
            description={`How JARVIS addresses you (e.g. "sir", a name, "boss"). Leave blank for no title or name at all.`}
            placeholder="sir"
            maxLength={20}
            value={addressPreference}
            onChange={(e) => setAddressPreference(e.target.value.slice(0, 20))}
            onBlur={handleAddressPreferenceBlur}
          />

          <Switch
            label="Daily Briefing"
            description="A brief greeting with the date, and anything notable (system status, relevant memories), on your first message each day."
            checked={dailyBriefingEnabled}
            onChange={handleDailyBriefingToggle}
          />
        </div>

        <Divider />

        {/* --- Security: conversation delete PIN. Grouped here rather than
            under AI Provider - it's a personal/privacy setting, not an
            AI-provider one. --- */}
        <div className="flex flex-col gap-[var(--space-3)]">
          <h3 className={subHeadingClasses}>Security</h3>
          <p className="text-[length:var(--font-size-sm)] text-[var(--color-text-muted)]">
            The 4-digit PIN required to delete a conversation. Leave blank to keep the current one.
          </p>
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
