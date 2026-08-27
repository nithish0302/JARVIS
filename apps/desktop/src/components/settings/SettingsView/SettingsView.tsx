import { useEffect, useState } from "react";
import { SettingsLayout } from "../SettingsLayout/SettingsLayout";
import { SettingsSidebar } from "../SettingsSidebar/SettingsSidebar";
import { AIProviderSection } from "../AIProviderSection/AIProviderSection";
import { PersonalitySection } from "../PersonalitySection/PersonalitySection";
import { AppearanceSection } from "../AppearanceSection/AppearanceSection";
import { PluginSection } from "../PluginSection/PluginSection";
import { ProvidersSection } from "../ProvidersSection/ProvidersSection";
import { AboutSection } from "../AboutSection/AboutSection";
import { useAppStore } from "../../../stores/useAppStore";

export function SettingsView() {
  // Read once on mount (e.g. the first-run auto-open wants "providers"
  // instead of the default "ai-provider") then clear it - a later plain
  // navigation to the settings view shouldn't keep forcing this section.
  const [activeSection, setActiveSection] = useState(
    () => useAppStore.getState().settingsInitialSection ?? "ai-provider"
  );

  useEffect(() => {
    if (useAppStore.getState().settingsInitialSection) {
      useAppStore.getState().setSettingsInitialSection(null);
    }
  }, []);

  return (
    <div className="flex h-full w-full flex-col">
      <SettingsLayout
        sidebar={
          <SettingsSidebar
            activeSection={activeSection}
            onSectionSelect={setActiveSection}
          />
        }
      >
        {/* h-full (not flex-1): this div's parent is a plain block, not a
            flex container, so flex-1 would be a no-op here and leave this
            box sized to its content - the same "no bounded height, nothing
            for overflow-y-auto to clip against" bug as SettingsLayout's
            root. h-full resolves against the parent's own bounded height
            (see SettingsLayout.tsx) instead. */}
        {/* no-scrollbar (globals.css): hides the scrollbar track/thumb while
            leaving overflow-y-auto's actual scroll behavior untouched -
            wheel/trackpad scrolling still works, only the visual indicator
            is gone. Same utility LeftColumn/ChatFullView already use. */}
        <div className="h-full min-h-0 overflow-y-auto no-scrollbar">
          {activeSection === "ai-provider" && <AIProviderSection />}
          {activeSection === "personality" && <PersonalitySection />}
          {activeSection === "appearance" && <AppearanceSection />}
          {activeSection === "plugins" && <PluginSection />}
          {activeSection === "providers" && <ProvidersSection />}
          {activeSection === "about" && <AboutSection />}
        </div>
      </SettingsLayout>
    </div>
  );
}
