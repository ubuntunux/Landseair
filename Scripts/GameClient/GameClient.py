import sys
import numpy as np

from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND
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

        self.resource_manager.open_scene('stage00')

        animation_list = ['idle']

        for key in animation_list:
            # self.animation_meshes[key] = self.resource_manager.get_mesh("Plane00_" + key)
            self.animation_meshes[key] = self.resource_manager.get_mesh("Plane00")

        self.player = Player(self.scene_manager, self.resource_manager)

        self.camera_distance = 10.0
        self.scene_manager.main_camera.transform.set_rotation((-0.5, 0.0, 0.0))

    def exit(self):
        logger.info("GameClient::exit")
        self.player.destroy(self.scene_manager)
        self.game_backend.set_mouse_grab(False)

    def update_player(self, delta_time):
        keydown = self.game_backend.get_keyboard_pressed()
        keyup = self.game_backend.get_keyboard_released()
        mouse_delta = self.game_backend.mouse_delta
        mouse_pos = self.game_backend.mouse_pos
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
        camera = self.scene_manager.main_camera
        is_mouse_grab = self.game_backend.get_mouse_grab()

        if keyup.get(Keyboard.ESCAPE):
            self.core_manager.request(COMMAND.STOP)
        elif keyup.get(Keyboard.TAB):
            self.game_backend.toggle_mouse_grab()

        # camera rotation
        if not is_mouse_grab:
            if btn_left or btn_right:
                camera.transform.rotation_pitch(mouse_delta[1] * camera.rotation_speed)
                camera.transform.rotation_yaw(-mouse_delta[0] * camera.rotation_speed)
                camera.transform.update_transform()

        if keydown[Keyboard.Q]:
            self.camera_distance -= ZOOM_SPEED * delta_time
        elif keydown[Keyboard.E]:
            self.camera_distance += ZOOM_SPEED * delta_time

        self.player.update(delta_time, self.game_backend, self.scene_manager)

        self.state_manager.update_state(delta_time)

        camera.transform.set_pos(self.player.get_pos() + camera.transform.front * self.camera_distance)

    def update(self, delta_time):
        self.update_player(delta_time)
