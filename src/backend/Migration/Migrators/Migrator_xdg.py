"""
Author: Patrickdag
Year: 2024

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This programm comes with ABSOLUTELY NO WARRANTY!

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from src.backend.Migration.Migrator import Migrator
import sys
import os
import shutil
from loguru import logger as log

import globals as gl


class Migrator_xdg(Migrator):
    """
    Migrates data from the legacy flatpak data path (~/.var/app/com.core447.StreamController/data/)
    to XDG Base Directory compliant paths:
    - CONFIG_PATH: ~/.config/streamcontroller (pages, settings, deck configs)
    - DATA_PATH: ~/.local/share/streamcontroller (icons, wallpapers, assets, plugins, backups)
    - CACHE_PATH: ~/.cache/streamcontroller (cache, logs, store cache)
    """
    def __init__(self):
        super().__init__("1.5.1")

    def get_need_migration(self) -> bool:
        # Skip if using legacy data path (custom --data flag or settings override)
        if gl.USE_LEGACY_DATA_PATH:
            log.info("Skipping XDG migration: using custom/legacy data path")
            return False

        # Skip if legacy data path doesn't exist
        if not os.path.exists(gl.LEGACY_DATA_PATH):
            log.info("Skipping XDG migration: legacy data path does not exist")
            return False

        # Use parent class logic to check if already migrated
        return super().get_need_migration()

    def migrate(self):
        log.info("Starting XDG Base Directory migration...")

        migrated_items = []
        skipped_items = []

        # Migrate to CONFIG_PATH (configuration files)
        # Note: XDG structure is flattened - no 'settings/' subfolder
        config_migrations = [
            ("pages", os.path.join(gl.LEGACY_DATA_PATH, "pages"), os.path.join(gl.CONFIG_PATH, "pages")),
            ("decks", os.path.join(gl.LEGACY_DATA_PATH, "settings", "decks"), gl.DECKS_PATH),
            ("settings.json", os.path.join(gl.LEGACY_DATA_PATH, "settings", "settings.json"), gl.APP_SETTINGS_FILE),
            ("pages.json", os.path.join(gl.LEGACY_DATA_PATH, "settings", "pages.json"), gl.PAGES_SETTINGS_FILE),
            ("migrations.json", os.path.join(gl.LEGACY_DATA_PATH, "settings", "migrations.json"), gl.MIGRATIONS_FILE),
            ("plugin settings", os.path.join(gl.LEGACY_DATA_PATH, "settings", "plugins"), gl.PLUGIN_SETTINGS_PATH),
            ("ui settings", os.path.join(gl.LEGACY_DATA_PATH, "settings", "ui"), gl.UI_SETTINGS_PATH),
            (".skip-onboarding", os.path.join(gl.LEGACY_DATA_PATH, ".skip-onboarding"), os.path.join(gl.CONFIG_PATH, ".skip-onboarding")),
            (".skip-permissions", os.path.join(gl.LEGACY_DATA_PATH, ".skip-permissions"), os.path.join(gl.CONFIG_PATH, ".skip-permissions")),
        ]

        for name, src, dst in config_migrations:
            if self._safe_copy(src, dst):
                migrated_items.append(f"CONFIG: {name}")
            elif os.path.exists(src):
                skipped_items.append(f"CONFIG: {name} (destination exists)")

        # Migrate to DATA_PATH (user data)
        data_migrations = [
            ("icons", os.path.join(gl.LEGACY_DATA_PATH, "icons"), os.path.join(gl.DATA_PATH, "icons")),
            ("wallpapers", os.path.join(gl.LEGACY_DATA_PATH, "wallpapers"), os.path.join(gl.DATA_PATH, "wallpapers")),
            ("sd_plus_bar_wallpapers", os.path.join(gl.LEGACY_DATA_PATH, "sd_plus_bar_wallpapers"), os.path.join(gl.DATA_PATH, "sd_plus_bar_wallpapers")),
            ("Assets", os.path.join(gl.LEGACY_DATA_PATH, "Assets"), os.path.join(gl.DATA_PATH, "Assets")),
            ("backups", os.path.join(gl.LEGACY_DATA_PATH, "backups"), os.path.join(gl.DATA_PATH, "backups")),
            ("plugins", os.path.join(gl.LEGACY_DATA_PATH, "plugins"), os.path.join(gl.DATA_PATH, "plugins")),
        ]

        for name, src, dst in data_migrations:
            if self._safe_copy(src, dst):
                migrated_items.append(f"DATA: {name}")
            elif os.path.exists(src):
                skipped_items.append(f"DATA: {name} (destination exists)")

        # Migrate to CACHE_PATH (cache and logs)
        cache_migrations = [
            ("cache", os.path.join(gl.LEGACY_DATA_PATH, "cache"), gl.CACHE_PATH),
            ("logs", os.path.join(gl.LEGACY_DATA_PATH, "logs"), os.path.join(gl.CACHE_PATH, "logs")),
            ("store cache", os.path.join(gl.LEGACY_DATA_PATH, "Store", "cache"), os.path.join(gl.CACHE_PATH, "store")),
        ]

        for name, src, dst in cache_migrations:
            if self._safe_copy(src, dst):
                migrated_items.append(f"CACHE: {name}")
            elif os.path.exists(src):
                skipped_items.append(f"CACHE: {name} (destination exists)")

        # Log results
        if migrated_items:
            log.info(f"Migrated {len(migrated_items)} items: {', '.join(migrated_items)}")
        if skipped_items:
            log.info(f"Skipped {len(skipped_items)} items: {', '.join(skipped_items)}")

        # Show user message
        if migrated_items:
            print(f"""
================================================================================
XDG Base Directory Migration Complete
================================================================================

Your files have been migrated to the new XDG-compliant folder structure:
  - Config: {gl.CONFIG_PATH}
  - Data:   {gl.DATA_PATH}
  - Cache:  {gl.CACHE_PATH}

Migrated {len(migrated_items)} item(s).
{f"Skipped {len(skipped_items)} item(s) (destinations already exist)." if skipped_items else ""}

IMPORTANT: We have NOT deleted any old files. Once you have verified that
StreamController works correctly, you can safely delete the old folder:
  {gl.VAR_APP_PATH}

================================================================================
""", file=sys.stderr)

        self.set_migrated(True)

    def _safe_copy(self, src: str, dst: str) -> bool:
        """
        Safely copy a file or directory from src to dst.

        Returns True if copy was successful, False if:
        - Source doesn't exist
        - Destination already exists
        - Copy failed
        """
        if not os.path.exists(src):
            return False

        if os.path.exists(dst):
            log.info(f"Skipping migration of {src} - destination {dst} already exists")
            return False

        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            if os.path.isdir(src):
                shutil.copytree(src, dst)
                log.info(f"Migrated directory: {src} -> {dst}")
            else:
                shutil.copy2(src, dst)
                log.info(f"Migrated file: {src} -> {dst}")

            return True
        except Exception as e:
            log.error(f"Failed to migrate {src} to {dst}: {e}")
            return False
