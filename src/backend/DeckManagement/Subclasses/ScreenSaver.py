"""
Author: Core447
Year: 2024

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This programm comes with ABSOLUTELY NO WARRANTY!

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
# Import python modules
import time
import threading
from loguru import logger as log
from copy import copy

# Import typing
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.DeckManagement.DeckController import DeckController, ControllerKey, Background

class ScreenSaver:
    def __init__(self, deck_controller: "DeckController"):
        self.deck_controller: "DeckController" = deck_controller

        # Init vars
        self.original_keys: list["ControllerKey"] = []
        self.original_background: "Background" = None
        self.original_brightness: int = 0

        # Time when last key state changed
        self.last_key_change_time = time.time()

        # Time delay
        self.time_delay = 5

        self.enable: bool = False
        self.showing: bool = False

        self.media_path: str = None
        self.brightness: int = 25
        self.fps: int = 30
        self.loop: bool = True

    def set_time(self, time_delay: int) -> None:
        if time_delay != self.time_delay:
            log.info(f"Setting screen saver time delay to {time_delay} minutes")
        self.time_delay = time_delay
        if hasattr(self, "timer"):
            self.timer.cancel()
        # *60 to go from minuts (how it is stored) to seconds (how the timer needs it)
        self.timer = threading.Timer(time_delay*60, self.on_timer_end)
        if self.enable and not self.showing:
            self.timer.start()

    def set_media_path(self, media_path: str) -> None:
        self.media_path = media_path

        if self.showing:
            self.deck_controller.background.set_from_path(self.media_path)

    def set_enable(self, enable: bool) -> None:
        self.enable = enable

        if not hasattr(self, "timer"):
            return
        
        # Hide if showing
        if self.showing and not enable:
            self.hide()
        
        # Stop timer if enable == False
        if enable:
            # Start time if not already running
            if not self.timer.is_alive:
                self.timer.start()
        else:
            self.timer.cancel()

    def on_timer_end(self) -> None:
        self.show()

    def show(self):
        log.info("Showing screen saver")
        # Stop timer - in case this method is called manually
        self.timer.cancel()
        # Set showing = True - in case this method is called manually
        self.showing = True

        # Store original keys and background
        self.original_keys = self.deck_controller.keys
        self.deck_controller.init_keys()
        self.original_background = copy(self.deck_controller.background)
        self.original_brightness = self.deck_controller.brightness

        self.deck_controller.set_brightness(self.brightness)

        # Clear all keys
        for key in self.deck_controller.keys:
            key.clear(update=False)

        self.deck_controller.clear_media_player_tasks()

        # Set background
        self.deck_controller.background.set_from_path(self.media_path, update=True)

        if self.deck_controller.background.video is not None:
            self.deck_controller.background.video.fps = self.fps
            self.deck_controller.background.video.loop = self.loop

    def hide(self):
        log.info("Hiding screen saver")

        # Restore original keys and background
        self.deck_controller.keys = self.original_keys
        self.deck_controller.background = self.original_background
        self.deck_controller.set_brightness(self.original_brightness)
        self.deck_controller.update_all_keys()
        self.showing = False

        self.set_time(self.time_delay)

    def on_key_change(self):
        self.last_key_change_time = time.time()
        if self.showing:
            self.hide()
        else:
            self.set_time(self.time_delay)

    def set_brightness(self, brightness: int) -> None:
        self.brightness = int(brightness)

        if self.showing:
            self.deck_controller.set_brightness(self.brightness)

    def set_fps(self, fps: int) -> None:
        self.fps = fps
        if not self.showing:
            return
        if self.deck_controller.background.video is not None:
            self.deck_controller.background.video.fps = fps
            print(f"FPS: {self.deck_controller.background.video.fps}")

    def set_loop(self, loop: bool) -> None:
        self.loop = loop
        if not self.showing:
            return
        if self.deck_controller.background.video is not None:
            self.deck_controller.background.video.loop = loop
            print(f"Loop: {self.deck_controller.background.video.loop}")