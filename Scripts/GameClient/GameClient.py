import sys
import numpy as np

from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger
from PyEngine3D.Utilities import *
from GameClient.GameState import *


GRAVITY = 20.0
ZOOM_SPEED = 5.0
SCROLL_SPEED = 10.0
MOVE_SPEED = 10.0
ROTATION_SPEED = 1.0
BULLET_SPEED = 30.0
BOUND_BOX_OFFSET = 0.1
EPSILON = sys.float_info.epsilon


class GameClient(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.scene_manager = None
        self.player = None
        self.bullet = None
        self.fire_bullet = False
        self.enemy = None
        self.on_ground = False
        self.velocity = Float3(0.0, 0.0, 0.0)
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

        main_camera = self.scene_manager.main_camera
        pos = main_camera.transform.pos - main_camera.transform.front * 5.0
        player_model = self.resource_manager.get_model("Plane00")
        bullet_model = self.resource_manager.get_model("Cube")

        self.player = self.scene_manager.add_object(model=player_model, pos=pos)
        self.bullet = self.scene_manager.add_object(model=bullet_model, pos=pos)
        # self.enemy = self.scene_manager.add_object(model=player_model, pos=pos)

        self.player.transform.set_pos([0.0, 5.0, 0.0])
        self.player.transform.set_yaw(3.141592)
        self.player.transform.set_scale(1.0)
        self.player.transform.euler_to_quaternion()
        self.player.transform.set_use_quaternion(True)

        self.bullet.transform.set_use_quaternion(True)

        self.velocity[...] = Float3(0.0, 0.0, 0.0)

        # self.enemy.transform.set_pos([0.0, -1.99, -11.0])
        # self.enemy.transform.set_yaw(3.141592)
        # self.enemy.transform.set_scale(0.45)

        # camera
        self.camera_distance = 10.0
        main_camera.transform.set_rotation((-0.5, 0.0, 0.0))

    def exit(self):
        logger.info("GameClient::exit")
        self.scene_manager.delete_object(self.player.name)
        self.scene_manager.delete_object(self.bullet.name)

    def update_player(self, delta_time):
        keydown = self.game_backend.get_keyboard_pressed()
        mouse_delta = self.game_backend.mouse_delta
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
        camera = self.scene_manager.main_camera
        player_transform = self.player.transform
        old_player_pos = player_transform.get_pos().copy()

        # camera rotation
        if btn_left or btn_right:
            camera_rotation_speed = camera.rotation_speed * delta_time
            camera.transform.rotation_pitch(mouse_delta[1] * camera_rotation_speed)
            camera.transform.rotation_yaw(-mouse_delta[0] * camera_rotation_speed)
            camera.transform.update_transform()

        if keydown[Keyboard.Q]:
            self.camera_distance -= ZOOM_SPEED * delta_time
        elif keydown[Keyboard.E]:
            self.camera_distance += ZOOM_SPEED * delta_time

        key_flag = KEY_FLAG.NONE

        rotation_speed = ROTATION_SPEED * delta_time

        # move key flags
        ql = QUATERNION_IDENTITY.copy()
        qf = QUATERNION_IDENTITY.copy()
        qu = QUATERNION_IDENTITY.copy()
        if keydown[Keyboard.W]:
            ql = get_quaternion(player_transform.left, rotation_speed)
        elif keydown[Keyboard.S]:
            ql = get_quaternion(player_transform.left, -rotation_speed)

        if keydown[Keyboard.A]:
            qf = get_quaternion(player_transform.front, -rotation_speed)
        elif keydown[Keyboard.D]:
            qf = get_quaternion(player_transform.front, rotation_speed)

        if keydown[Keyboard.Z]:
            qu = get_quaternion(player_transform.up, rotation_speed)
        elif keydown[Keyboard.C]:
            qu = get_quaternion(player_transform.up, -rotation_speed)

        quat = muliply_quaternions(ql, qf, qu)
        player_transform.rotation_quaternion(quat)

        # fire bullet
        if keydown[Keyboard.SPACE]:
            self.fire_bullet = True
            self.bullet.transform.set_pos(old_player_pos)
            self.bullet.transform.set_quaternion(player_transform.get_quaternion())

        if self.fire_bullet:
            if length(self.bullet.transform.get_pos() - player_transform.get_pos()) < 10.0:
                self.bullet.transform.move_front((BULLET_SPEED + MOVE_SPEED) * delta_time)
            else:
                self.fire_bullet = False

        # move to forawd
        self.velocity = player_transform.front * (1.0 + (0.5 - player_transform.front[1] * 0.5)) * MOVE_SPEED

        move_delta = self.velocity * delta_time
        player_pos = old_player_pos + move_delta

        self.on_ground = False

        def compute_collide(i, old_position, position, move_delta, bound_box):
            j = (i + 1) % 3
            k = (i + 2) % 3

            def is_in_plane(index, ratio):
                if index == 1:
                    return bound_box.bound_min[index] < (old_position[index] + move_delta[index] * ratio + BOUND_BOX_OFFSET) < bound_box.bound_max[index]
                else:
                    return bound_box.bound_min[index] < (old_position[index] + move_delta[index] * ratio) < bound_box.bound_max[index]

            if move_delta[i] < 0.0 and position[i] <= bound_box.bound_max[i] <= old_position[i]:
                ratio = abs((bound_box.bound_max[i] - old_position[i]) / move_delta[i])
                if is_in_plane(j, ratio) and is_in_plane(k, ratio):
                    position[i] = bound_box.bound_max[i] + EPSILON
                    move_delta[i] = position[i] - old_position[i]
                    if 1 == i:
                        self.on_ground = True
            elif 0.0 < move_delta[i] and old_position[i] <= bound_box.bound_min[i] <= position[i]:
                ratio = abs((bound_box.bound_min[i] - old_position[i]) / move_delta[i])
                if is_in_plane(j, ratio) and is_in_plane(k, ratio):
                    position[i] = bound_box.bound_min[i] - EPSILON
                    move_delta[i] = position[i] - old_position[i]

        for collision_actor in self.scene_manager.collision_actors:
            for geometry_bound_box in collision_actor.get_geometry_bound_boxes():
                for i in range(3):
                    compute_collide(i, old_player_pos, player_pos, move_delta, geometry_bound_box)

        if self.on_ground:
            self.velocity[1] = 0.0

        self.state_manager.update_state(delta_time, self.player, self.animation_meshes, self.on_ground, key_flag)

        player_transform.set_pos(player_pos)
        camera.transform.set_pos(player_transform.get_pos() + camera.transform.front * self.camera_distance)

    def update(self, delta_time):
        self.update_player(delta_time)
