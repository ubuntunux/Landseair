from PyEngine3D.UI import Widget
from PyEngine3D.Utilities import *


class GameUIManager:
    def __init__(self):
        self.game_client = None
        self.main_viewport = None
        self.actor_manager = None
        self.hp_bar = None

    def initialize(self, game_client):
        self.game_client = game_client
        self.main_viewport = game_client.main_viewport
        self.actor_manager = game_client.actor_manager
        self.player_hp_bar = GameUI_HPBar(self, game_client, -20.0)
        self.target_hp_bar = GameUI_HPBar(self, game_client, -70.0)

    def destroy(self):
        pass

    def update(self, dt):
        self.player_hp_bar.update(dt)
        self.target_hp_bar.update(dt)


class GameUI_HPBar:
    def __init__(self, game_ui_manager, game_client, offset):
        self.game_ui_manager = game_ui_manager
        self.game_client = game_client
        self.main_viewport = game_client.main_viewport
        self.actor_manager = game_client.actor_manager

        pos_x = 15.0
        pos_y = self.main_viewport.height + offset

        self.hp_bar_text = Widget(name="hp_bar_text", width=200.0, height=15.0, text="hp_bar_text", font_size=12)
        self.hp_bar_text.x = pos_x
        self.hp_bar_text.y = pos_y

        self.hp_bar_background = Widget(name="hp_bar_background", width=200.0, height=25.0, color=Float4(0.0, 0.0, 0.0, 0.5))
        self.hp_bar_background.x = pos_x
        self.hp_bar_background.y = self.hp_bar_text.y - self.hp_bar_background.height - 5

        padding = 5
        self.hp_bar = Widget(name="hp_bar", width=self.hp_bar_background.width - padding * 2, height=self.hp_bar_background.height - padding * 2, color=Float4(1.0, 1.0, 0.3, 0.8))
        self.hp_bar.x = self.hp_bar_background.x + padding
        self.hp_bar.y = self.hp_bar_background.y + padding

        self.main_viewport.add_widget(self.hp_bar_background)
        self.main_viewport.add_widget(self.hp_bar)
        self.main_viewport.add_widget(self.hp_bar_text)

    def update(self, dt):
        pass
