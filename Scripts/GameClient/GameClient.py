import sys
import numpy as np

from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND
from PyEngine3D.UI import Widget
from PyEngine3D.Utilities import *

from GameClient.GameState import *
from GameClient.Player import Player
from GameClient.Constants import *


class GameClient(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.scene_manager = None
        self.viewport_manager = None
        self.main_viewport = None
        self.crosshair = None
        self.player_aim = None
        self.player = None
        self.camera_distance = 0.0
        self.animation_meshes = {}
        self.state_manager = GameStateManager()

    def initialize(self, core_manager):
        logger.info("GameClient::initialize")

        self.core_manager = core_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager
        self.viewport_manager = core_manager.viewport_manager
        self.main_viewport = core_manager.viewport_manager.main_viewport

        self.resource_manager.open_scene('stage00')

        animation_list = ['idle']

        for key in animation_list:
            # self.animation_meshes[key] = self.resource_manager.get_mesh("Plane00_" + key)
            self.animation_meshes[key] = self.resource_manager.get_mesh("Plane00")

        self.player = Player(self.scene_manager, self.resource_manager)

        self.camera_pitch_delay = 0.0
        self.camera_yaw_delay = 0.0
        self.camera_distance = 10.0
        main_camera = self.scene_manager.main_camera
        main_camera.transform.set_use_quaternion(False)
        main_camera.transform.set_rotation((0.0, 0.0, 0.0))
        main_camera.transform.euler_to_quaternion()

        self.build_ui()

    def exit(self):
        logger.info("GameClient::exit")
        self.clear_ui()
        self.player.destroy(self.scene_manager)
        self.game_backend.set_mouse_grab(False)

    def build_ui(self):
        crosshair_texture = self.resource_manager.get_texture('crosshair')
        self.crosshair = Widget(name="crosshair", width=100.0, height=100.0, texture=crosshair_texture)
        self.crosshair.x = (self.main_viewport.width - self.crosshair.width) / 2
        self.crosshair.y = (self.main_viewport.height - self.crosshair.height) / 2

        self.player_aim = None
        self.player_aim = Widget(name="player_aim", width=20.0, height=20.0, texture=crosshair_texture)
        self.player_aim.x = (self.main_viewport.width - self.player_aim.width) / 2
        self.player_aim.y = (self.main_viewport.height - self.player_aim.height) / 2

        self.main_viewport.add_widget(self.crosshair)
        self.main_viewport.add_widget(self.player_aim)

    def clear_ui(self):
        self.crosshair = None
        self.main_viewport.clear_widgets()

    def update_player(self, delta_time):
        keydown = self.game_backend.get_keyboard_pressed()
        keyup = self.game_backend.get_keyboard_released()
        mouse_delta = self.game_backend.mouse_delta
        mouse_pos = self.game_backend.mouse_pos
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
        camera = self.scene_manager.main_camera
        camera_transform = camera.transform
        player_transform = self.player.get_transform()
        is_mouse_grab = self.game_backend.get_mouse_grab()
        screen_width = self.main_viewport.width
        screen_height = self.main_viewport.height

        # crosshair
        crosshair_half_width = self.crosshair.width / 2
        crosshair_half_height = self.crosshair.height / 2
        if is_mouse_grab:
            self.crosshair.x = min(max(-crosshair_half_width, self.crosshair.x + mouse_delta[0]), screen_width - crosshair_half_width)
            self.crosshair.y = min(max(-crosshair_half_height, self.crosshair.y + mouse_delta[1]), screen_height - crosshair_half_height)
        else:
            self.crosshair.x = mouse_pos[0] - crosshair_half_width
            self.crosshair.y = mouse_pos[1] - crosshair_half_height

        crosshair_x_ratio = ((self.crosshair.x + crosshair_half_width) / screen_width) * 2.0 - 1.0
        crosshair_y_ratio = ((self.crosshair.y + crosshair_half_height) / screen_height) * 2.0 - 1.0
        aim_x_diff_ratio = (self.crosshair.center_x - self.player_aim.center_x) / screen_width
        aim_y_diff_ratio = (self.crosshair.center_y - self.player_aim.center_y) / screen_height

        if keyup.get(Keyboard.ESCAPE):
            self.core_manager.request(COMMAND.STOP)
        elif keyup.get(Keyboard.TAB):
            self.game_backend.toggle_mouse_grab()

        # camera rotation
        if not is_mouse_grab:
            if btn_left or btn_right:
                camera_transform.set_use_quaternion(False)
                camera_transform.rotation_pitch(mouse_delta[1] * camera.rotation_speed)
                camera_transform.rotation_yaw(-mouse_delta[0] * camera.rotation_speed)
                camera_transform.update_transform()
        else:
            if player_transform.use_quaternion:
                camera_transform.set_quaternion(player_transform.get_quaternion())
            else:
                rotation = player_transform.get_rotation()
                rotation[0] *= -1.0
                rotation[1] += PI

                rotation_delay_speed = 2.0
                rotation_delay_limit = 0.3
                self.camera_yaw_delay += aim_x_diff_ratio * rotation_delay_speed * delta_time
                self.camera_yaw_delay = min(rotation_delay_limit, max(-rotation_delay_limit, self.camera_yaw_delay))
                self.camera_pitch_delay += aim_y_diff_ratio * rotation_delay_speed * delta_time
                self.camera_pitch_delay = min(rotation_delay_limit, max(-rotation_delay_limit, self.camera_pitch_delay))
                rotation[0] -= self.camera_pitch_delay
                rotation[1] += self.camera_yaw_delay

                camera_transform.set_rotation(rotation)

        if keydown[Keyboard.Q]:
            self.camera_distance -= ZOOM_SPEED * delta_time
        elif keydown[Keyboard.E]:
            self.camera_distance += ZOOM_SPEED * delta_time

        self.player.update(delta_time, self, aim_x_diff_ratio, aim_y_diff_ratio)

        self.state_manager.update_state(delta_time)

        aim_pos = self.player.get_pos() + player_transform.front * 1000.0 - camera_transform.get_pos()
        aim_pos = np.dot(Float4(*aim_pos, 0.0), camera.view_origin_projection)
        aim_pos[0] = (aim_pos[0] / aim_pos[3]) * 0.5 + 0.5
        aim_pos[1] = (aim_pos[1] / aim_pos[3]) * 0.5 + 0.5
        self.player_aim.x = aim_pos[0] * screen_width - self.player_aim.width / 2
        self.player_aim.y = aim_pos[1] * screen_height - self.player_aim.height / 2

        camera_pos = self.player.get_pos() + camera_transform.front * self.camera_distance
        camera_pos[1] += 2.5
        camera_transform.set_pos(camera_pos)

    def update(self, delta_time):
        self.update_player(delta_time)
