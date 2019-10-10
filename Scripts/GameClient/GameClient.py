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

        self.camera_distance = 10.0
        self.scene_manager.main_camera.transform.set_rotation((-0.5, 0.0, 0.0))

        self.build_ui()

    def exit(self):
        logger.info("GameClient::exit")
        self.player.destroy(self.scene_manager)
        self.game_backend.set_mouse_grab(False)

    def build_ui(self):
        crosshair_texture = self.resource_manager.get_texture('crosshair')
        self.crosshair = Widget(name="crosshair", width=100.0, height=100.0, texture=crosshair_texture)
        self.crosshair.x = (self.main_viewport.width - self.crosshair.width) / 2
        self.crosshair.y = (self.main_viewport.height - self.crosshair.height) / 2
        self.main_viewport.add_widget(self.crosshair)

    def update_player(self, delta_time):
        keydown = self.game_backend.get_keyboard_pressed()
        keyup = self.game_backend.get_keyboard_released()
        mouse_delta = self.game_backend.mouse_delta
        mouse_pos = self.game_backend.mouse_pos
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
        camera = self.scene_manager.main_camera
        camera_transform = camera.transform
        is_mouse_grab = self.game_backend.get_mouse_grab()
        screen_width = self.main_viewport.width
        screen_height = self.main_viewport.height

        # crosshair
        crosshair_halfsize = self.crosshair.width / 2
        self.crosshair.x = min(max(-crosshair_halfsize, self.crosshair.x + mouse_delta[0]), screen_width - crosshair_halfsize)
        self.crosshair.y = min(max(-crosshair_halfsize, self.crosshair.y + mouse_delta[1]), screen_height - crosshair_halfsize)

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
            rotation_speed = ROTATION_SPEED * delta_time
            ratio_x = -1.0 if 0.0 <= camera_transform.up[1] else 1.0
            speed_x = (self.crosshair.center_x / screen_width - 0.5) * 2.0
            speed_y = (self.crosshair.center_y / screen_height - 0.5) * 2.0
            camera_transform.rotation_pitch(rotation_speed * speed_y)
            camera_transform.rotation_yaw(rotation_speed * speed_x * ratio_x)
            camera_transform.update_transform()

            # camera_transform.set_use_quaternion(True)
            # rotation_speed = ROTATION_SPEED * delta_time
            # speed_x = (self.crosshair.center_x / screen_width - 0.5) * 2.0
            # speed_y = (self.crosshair.center_y / screen_height - 0.5) * 2.0
            # ql = QUATERNION_IDENTITY.copy()
            # qf = QUATERNION_IDENTITY.copy()
            # qu = QUATERNION_IDENTITY.copy()
            # ql = get_quaternion(camera_transform.left, rotation_speed * speed_y)
            # # qf = get_quaternion(camera_transform.front, -rotation_speed * speed_x)
            # qu = get_quaternion(Float3(0.0, 1.0, 0.0), -rotation_speed * speed_x)
            # quat = muliply_quaternions(ql, qf, qu)
            # camera_transform.rotation_quaternion(quat)
            # camera_transform.update_transform()

        if keydown[Keyboard.Q]:
            self.camera_distance -= ZOOM_SPEED * delta_time
        elif keydown[Keyboard.E]:
            self.camera_distance += ZOOM_SPEED * delta_time

        self.player.update(delta_time, self)

        self.state_manager.update_state(delta_time)

        camera_transform.set_pos(self.player.get_pos() + camera_transform.front * self.camera_distance)

    def update(self, delta_time):
        self.update_player(delta_time)
