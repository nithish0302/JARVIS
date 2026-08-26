import { useState } from "react";
import { SettingsLayout } from "../SettingsLayout/SettingsLayout";
import { SettingsSidebar } from "../SettingsSidebar/SettingsSidebar";
import { AIProviderSection } from "../AIProviderSection/AIProviderSection";
import { PersonalitySection } from "../PersonalitySection/PersonalitySection";
import { AppearanceSection } from "../AppearanceSection/AppearanceSection";
import { PluginSection } from "../PluginSection/PluginSection";
import { AboutSection } from "../AboutSection/AboutSection";

export function SettingsView() {
  const [activeSection, setActiveSection] = useState("ai-provider");

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
          {activeSection === "about" && <AboutSection />}
        </div>
      </SettingsLayout>
    </div>
  );
}
