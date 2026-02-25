"""Avatar registry for managing agent-avatar bindings."""

from typing import Dict, Optional, List
from avatars.avatar import Avatar, AvatarProfile, AvatarStyle


class AvatarRegistry:
    """
    Centralized registry for avatar profiles and agent-avatar bindings.
    Singleton pattern provides global access.
    """

    _instance: Optional["AvatarRegistry"] = None
    _avatars: Dict[str, Avatar] = {}
    _profiles: Dict[str, AvatarProfile] = {}
    _agent_bindings: Dict[str, str] = {}  # agent_name -> avatar_id

    def __new__(cls) -> "AvatarRegistry":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_defaults()
        return cls._instance

    def _load_defaults(self) -> None:
        """Initialize default avatar profiles."""
        profiles = {
            "engineer": AvatarProfile(
                avatar_id="avatar-engineer-001",
                name="Engineer",
                style=AvatarStyle.ENGINEER,
                bound_agent="ArchitectureAgent",
                system_prompt=(
                    "You are an engineer avatar. Be precise, logical, and safety-conscious. "
                    "Focus on specs, constraints, and failure modes. Minimize ambiguity."
                ),
                ui_config={
                    "color": "#2E86DE",
                    "icon": "⚙️",
                    "theme": "dark-mono"
                }
            ),
            "designer": AvatarProfile(
                avatar_id="avatar-designer-001",
                name="Designer",
                style=AvatarStyle.DESIGNER,
                bound_agent="ArchitectureAgent",
                system_prompt=(
                    "You are a designer avatar. Be visual, creative, and metaphor-friendly. "
                    "Focus on aesthetics, UX, and narrative coherence."
                ),
                ui_config={
                    "color": "#A29BFE",
                    "icon": "🎨",
                    "theme": "gradient"
                }
            ),
            "driver": AvatarProfile(
                avatar_id="avatar-driver-001",
                name="Driver",
                style=AvatarStyle.DRIVER,
                bound_agent="CoderAgent",
                system_prompt=(
                    "You are a driver avatar. Be conversational, game-aware, and responsive. "
                    "Understand in-universe context and player intent. Keep tone engaging."
                ),
                ui_config={
                    "color": "#FF6348",
                    "icon": "🏁",
                    "theme": "neon"
                }
            ),
            "gemini": AvatarProfile(
                avatar_id="avatar-gemini-001",
                name="Gemini",
                style=AvatarStyle.ENGINEER,
                bound_agent="GeminiAgent",
                system_prompt=(
                    "You are a Gemini avatar. You are a helpful assistant that can answer questions and complete tasks."
                ),
                ui_config={
                    "color": "#4285F4",
                    "icon": "✨",
                    "theme": "light"
                }
            )
        }

        for profile in profiles.values():
            self.register_avatar(profile)

    def register_avatar(self, profile: AvatarProfile) -> Avatar:
        """Register a new avatar and optionally bind to an agent."""
        avatar = Avatar(profile)
        self._avatars[profile.avatar_id] = avatar
        self._profiles[profile.avatar_id] = profile

        if profile.bound_agent:
            self._agent_bindings[profile.bound_agent] = profile.avatar_id

        return avatar

    def get_avatar(self, avatar_id: str) -> Optional[Avatar]:
        """Get avatar by ID."""
        return self._avatars.get(avatar_id)

    def get_profile(self, avatar_id: str) -> Optional[AvatarProfile]:
        """Retrieve an avatar profile by ID."""
        return self._profiles.get(avatar_id)

    def get_avatar_for_agent(self, agent_name: str) -> Optional[Avatar]:
        """Get avatar bound to a specific agent."""
        avatar_id = self._agent_bindings.get(agent_name)
        if avatar_id:
            return self._avatars.get(avatar_id)
        return None

    def bind_agent_to_avatar(self, agent_name: str, avatar_id: str) -> None:
        """Bind an agent to an avatar."""
        if avatar_id not in self._avatars:
            raise ValueError(f"Avatar {avatar_id} not found")
        self._agent_bindings[agent_name] = avatar_id

    def list_avatars(self) -> List[Avatar]:
        """Get all registered avatars."""
        return list(self._avatars.values())

    def list_bindings(self) -> Dict[str, str]:
        """Get all agent-avatar bindings."""
        return self._agent_bindings.copy()

    def clear(self) -> None:
        """Clear all avatars and bindings (for testing)."""
        self._avatars.clear()
        self._profiles.clear()
        self._agent_bindings.clear()

    def __repr__(self) -> str:
        return (
            f"<AvatarRegistry avatars={len(self._avatars)} "
            f"bindings={len(self._agent_bindings)}>"
        )


def get_avatar_registry() -> AvatarRegistry:
    """Access the global avatar registry singleton."""
    return AvatarRegistry()


def get_registry() -> AvatarRegistry:
    """Compatibility alias."""
    return get_avatar_registry()
