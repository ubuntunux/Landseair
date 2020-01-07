from enum import Enum
import math

from PyEngine3D.UI import Widget
from PyEngine3D.Utilities import *
from GameClient.Constants import *

game_ui_manager = None


class GameIconTypes(Enum):
    ALERT = 0


class GameUIManager:
    def __init__(self):
        self.game_client = None
        self.main_viewport = None
        self.actor_manager = None
        self.resource_manager = None
        self.scene_manager = None

        self.player_hp_bar = None
        self.target_hp_bar = None
        self.icon_3d_list = []

    def initialize(self, game_client):
        global game_ui_manager
        game_ui_manager = self
        self.game_client = game_client
        self.main_viewport = game_client.main_viewport
        self.actor_manager = game_client.actor_manager
        self.resource_manager = game_client.resource_manager
        self.scene_manager = game_client.scene_manager

        self.player_hp_bar = GameUI_HPBar(offset=-20.0)
        self.target_hp_bar = GameUI_HPBar(offset=-70.0)

    def destroy(self):
        self.player_hp_bar = None
        self.target_hp_bar = None
        self.icon_3d_list = []

    def create_game_icon_3d(self, game_icon_type, position):
        if GameIconTypes.ALERT == game_icon_type:
            icon_3d = GameUI_Icon3D(TEXTURE_ALERT, position)
        else:
            icon_3d = None
        if icon_3d is not None:
            self.icon_3d_list.append(icon_3d)
        return icon_3d

    def update(self, dt):
        self.player_hp_bar.update(dt)
        self.target_hp_bar.update(dt)

        index = 0
        icon_count = len(self.icon_3d_list)
        for i in range(icon_count):
            icon_3d = self.icon_3d_list[index]
            if icon_3d.is_alive():
                icon_3d.update(dt)
                index += 1
            else:
                self.icon_3d_list.pop(index)


class GameUI_HPBar:
    def __init__(self, offset):
        main_viewport = game_ui_manager.main_viewport

        pos_x = 15.0
        pos_y = main_viewport.height + offset

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

        main_viewport.add_widget(self.hp_bar_background)
        main_viewport.add_widget(self.hp_bar)
        main_viewport.add_widget(self.hp_bar_text)

    def update(self, dt):
        pass


class GameUI_Icon3D:
    offset_y = 10.0

    def __init__(self, texture_name, posisiton):
        self.posisiton = posisiton
        self.life_time = 1.0
        self.flicking_speed = 2.0

        size = 50.0
        texture = game_ui_manager.resource_manager.get_texture(texture_name)
        self.icon = Widget(texture=texture, width=size, height=size, opacity=0.5)

        self.update_position()

        game_ui_manager.main_viewport.add_widget(self.icon)

    def is_alive(self):
        return 0.0 < self.life_time

    def update_position(self):
        self.icon.x, self.icon.y = game_ui_manager.game_client.to_2d_position(self.posisiton)
        self.icon.x -= self.icon.width / 2
        self.icon.y += self.offset_y

    def update(self, dt):
        self.update_position()

        self.life_time -= dt

        if 0.0 < self.flicking_speed:
            self.icon.opacity = abs(math.fmod(self.life_time * self.flicking_speed, 1.0) * 2.0 - 1.0)

        if self.life_time <= 0.0:
            game_ui_manager.main_viewport.remove_widget(self.icon)
