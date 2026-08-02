import { useState } from "react";
import { SettingsLayout } from "../SettingsLayout/SettingsLayout";
import { SettingsSidebar } from "../SettingsSidebar/SettingsSidebar";
import { AIProviderSection } from "../AIProviderSection/AIProviderSection";
import { AppearanceSection } from "../AppearanceSection/AppearanceSection";
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
        <div className="flex-1 overflow-y-auto">
          {activeSection === "ai-provider" && <AIProviderSection />}
          {activeSection === "appearance" && <AppearanceSection />}
          {activeSection === "about" && <AboutSection />}
        </div>
      </SettingsLayout>
    </div>
  );
}
