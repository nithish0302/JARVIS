from .registry import registry, PluginDefinition

def register_placeholders():
    registry.register(PluginDefinition(
        id="gmail",
        name="Gmail",
        description="Read, search, and send emails via Google Workspace.",
        required_credentials=["oauth_token"],
        capabilities=["Read emails", "Send emails"],
        ui_actions=["[UI_ACTION:gmail_compose]"]
    ))
    registry.register(PluginDefinition(
        id="google_calendar",
        name="Google Calendar",
        description="Manage events and check schedule.",
        required_credentials=["oauth_token"],
        capabilities=["Read events", "Create events"],
        ui_actions=["[UI_ACTION:calendar_view]"]
    ))
    registry.register(PluginDefinition(
        id="whatsapp",
        name="WhatsApp",
        description="Send and receive WhatsApp messages.",
        required_credentials=["api_key"],
        capabilities=["Send messages", "Read messages"],
        ui_actions=["[UI_ACTION:whatsapp_send]"]
    ))
    registry.register(PluginDefinition(
        id="spotify",
        name="Spotify",
        description="Control music playback and search tracks.",
        required_credentials=["oauth_token"],
        capabilities=["Play music", "Pause music", "Search tracks"],
        ui_actions=["[UI_ACTION:spotify_play]", "[UI_ACTION:spotify_pause]"]
    ))
    registry.register(PluginDefinition(
        id="weather",
        name="Weather",
        description="Check current weather conditions and forecasts.",
        required_credentials=[],
        capabilities=["Check weather"],
        ui_actions=["[UI_ACTION:weather_show]"]
    ))
