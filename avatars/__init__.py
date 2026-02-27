"""Avatar system for agent personality and style management."""
"""Avatar wrapper system for agent personality deployment."""

from avatars.avatar import Avatar, AvatarProfile, AvatarStyle
from avatars.registry import AvatarRegistry, get_avatar_registry
from avatars.setup import setup_default_avatars, reset_avatars

__all__ = [
    "Avatar",
    "AvatarProfile",
    "AvatarStyle",
    "AvatarRegistry",
    "get_avatar_registry",
]
