import sys
import numpy as np

from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND
from PyEngine3D.UI import Widget
from PyEngine3D.Utilities import *
from PyEngine3D.Render import RenderOption

from GameClient.CameraShake import CameraShake
from GameClient.Actor import ActorManager
from GameClient.Bullet import BulletManager
from GameClient.GameEffectManager import GameEffectManager
from GameClient.Constants import *


class GameClient:
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.scene_manager = None
        self.viewport_manager = None
        self.main_viewport = None
        self.actor_manager = None
        self.bullet_manager = None
        self.game_effect_manager = None
        self.main_camera = None
        self.crosshair = None
        self.player_aim = None
        self.target_actor = None
        self.target_actor_distance = 0.0
        self.camera_distance = 0.0
        self.camera_shake = CameraShake()
        self.animation_meshes = {}
        self.stage = 'stage00'

    def initialize(self, core_manager):
        logger.info("GameClient::initialize")

        self.core_manager = core_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager
        self.viewport_manager = core_manager.viewport_manager
        self.main_viewport = core_manager.viewport_manager.main_viewport
        self.actor_manager = ActorManager()
        self.bullet_manager = BulletManager()
        self.game_effect_manager = GameEffectManager()

        self.resource_manager.open_scene(self.stage, force=True)

        game_client = self
        self.bullet_manager.initialize(game_client)
        self.actor_manager.initialize(game_client)
        self.game_effect_manager.initialize(game_client)

        self.camera_pitch_delay = 0.0
        self.camera_yaw_delay = 0.0
        self.camera_offset_horizontal = 0.0
        self.camera_offset_vertical = 0.0
        self.camera_distance = 10.0
        self.main_camera = self.scene_manager.main_camera
        self.main_camera.transform.set_rotation((0.0, 0.0, 0.0))
        self.main_camera.transform.euler_to_quaternion()

        self.build_ui()

        self.game_backend.set_mouse_grab(False)
        RenderOption.RENDER_GIZMO = False
        RenderOption.RENDER_OBJECT_ID = False

    def exit(self):
        logger.info("GameClient::exit")
        self.clear_ui()
        self.actor_manager.destroy()
        self.bullet_manager.destroy()
        self.game_backend.set_mouse_grab(False)
        RenderOption.RENDER_GIZMO = True
        RenderOption.RENDER_OBJECT_ID = True

        self.restore_edit_mode()

    def restore_edit_mode(self):
        camera_transform = TransformObject()
        camera_transform.clone(self.scene_manager.main_camera.transform)
        self.resource_manager.open_scene(self.stage, force=True)
        self.scene_manager.main_camera.transform.clone(camera_transform)

    def build_ui(self):
        crosshair_texture = self.resource_manager.get_texture('crosshair')
        crosshair_box_texture = self.resource_manager.get_texture('crosshair_box')
        self.crosshair = Widget(name="crosshair", width=50.0, height=50.0, texture=crosshair_box_texture)
        self.crosshair.x = (self.main_viewport.width - self.crosshair.width) / 2
        self.crosshair.y = (self.main_viewport.height - self.crosshair.height) / 2

        self.player_aim = None
        self.player_aim = Widget(name="player_aim", width=40.0, height=40.0, texture=crosshair_texture)
        self.player_aim.x = (self.main_viewport.width - self.player_aim.width) / 2
        self.player_aim.y = (self.main_viewport.height - self.player_aim.height) / 2

        self.main_viewport.add_widget(self.crosshair)
        self.main_viewport.add_widget(self.player_aim)

    def clear_ui(self):
        self.crosshair = None
        self.main_viewport.clear_widgets()

    def set_cross_hair_center(self):
        self.crosshair.x = (self.main_viewport.width - self.crosshair.width) / 2
        self.crosshair.y = (self.main_viewport.height - self.crosshair.height) / 2

    def update_player(self, delta_time):
        keydown = self.game_backend.get_keyboard_pressed()
        keyup = self.game_backend.get_keyboard_released()
        mouse_delta = self.game_backend.mouse_delta
        mouse_pos = self.game_backend.mouse_pos
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
        camera = self.main_camera
        camera_transform = camera.transform
        is_mouse_grab = self.game_backend.get_mouse_grab()
        screen_width = self.main_viewport.width
        screen_height = self.main_viewport.height
        player_actor = self.actor_manager.player_actor
        player_transform = player_actor.get_transform()
        crosshair_half_width = self.crosshair.width / 2
        crosshair_half_height = self.crosshair.height / 2

        if is_mouse_grab:
            self.crosshair.x = min(max(-crosshair_half_width, self.crosshair.x + mouse_delta[0]), screen_width - crosshair_half_width)
            self.crosshair.y = min(max(-crosshair_half_height, self.crosshair.y + mouse_delta[1]), screen_height - crosshair_half_height)

        crosshair_x_ratio = (self.crosshair.x + crosshair_half_width) / screen_width
        crosshair_y_ratio = (self.crosshair.y + crosshair_half_height) / screen_height
        aim_x_ratio = (self.player_aim.x + self.player_aim.width / 2) / screen_width
        aim_y_ratio = (self.player_aim.y + self.player_aim.height / 2) / screen_height
        aim_x_diff_ratio = crosshair_x_ratio - aim_x_ratio
        aim_y_diff_ratio = crosshair_y_ratio - aim_y_ratio

        crosshair_pos = np.dot(Float4(crosshair_x_ratio * 2.0 - 1.0, crosshair_y_ratio * 2.0 - 1.0, 0.0, 1.0), camera.inv_view_origin_projection)
        crosshair_dir = normalize(crosshair_pos[0:3])
        to_player = player_transform.get_pos() - camera_transform.get_pos()
        dir_amount = np.dot(to_player, crosshair_dir)
        diff_dir = crosshair_dir * dir_amount - to_player
        dist = math.sqrt(AIM_DISTANCE * AIM_DISTANCE - length(diff_dir))

        relative_goal_aim_pos = crosshair_dir * (dir_amount + dist) - to_player
        goal_aim_dir = normalize(relative_goal_aim_pos)
        goal_aim_pitch = clamp_radian(math.asin(-goal_aim_dir[1]))
        goal_aim_yaw = clamp_radian(math.atan2(goal_aim_dir[0], goal_aim_dir[2]))

        if keyup.get(Keyboard.ESCAPE):
            self.core_manager.request(COMMAND.STOP)
        elif keyup.get(Keyboard.TAB):
            self.game_backend.toggle_mouse_grab()

        # camera rotation
        rotation = player_transform.get_rotation().copy()
        rotation[0] = -rotation[0]
        rotation[1] += PI
        rotation[2] = 0.0
        camera_transform.set_rotation(rotation)

        if keydown[Keyboard.Z]:
            self.camera_distance -= ZOOM_SPEED * delta_time
        elif keydown[Keyboard.C]:
            self.camera_distance += ZOOM_SPEED * delta_time

        # update player
        player_actor.update_player(self, delta_time, crosshair_x_ratio, crosshair_y_ratio, goal_aim_pitch, goal_aim_yaw)

        if is_mouse_grab and btn_left:
            player_actor.bullet.fire(player_transform.get_pos(), player_transform.front, camera_transform, self.target_actor_distance)

        aim_pos = player_actor.get_pos() + player_transform.front * AIM_DISTANCE - camera_transform.get_pos()
        aim_pos = np.dot(Float4(*aim_pos, 0.0), camera.view_origin_projection)
        aim_pos[0] = (aim_pos[0] / aim_pos[3]) * 0.5 + 0.5
        aim_pos[1] = (aim_pos[1] / aim_pos[3]) * 0.5 + 0.5
        self.player_aim.x = aim_pos[0] * screen_width - self.player_aim.width / 2
        self.player_aim.y = aim_pos[1] * screen_height - self.player_aim.height / 2

        camera_pos = player_actor.get_pos() + camera_transform.front * self.camera_distance
        camera_offset_speed = CAMERA_OFFSET_SPEED * delta_time

        # camera offset horizontal
        goal_offset_horizontal = aim_x_diff_ratio * CAMERA_OFFSET_HORIZONTAL
        diff_offset_horizontal = goal_offset_horizontal - self.camera_offset_horizontal
        sign_offset_horizontal = np.sign(diff_offset_horizontal)
        self.camera_offset_horizontal += camera_offset_speed * abs(diff_offset_horizontal) * sign_offset_horizontal

        if 0.0 != sign_offset_horizontal and sign_offset_horizontal != np.sign(goal_offset_horizontal - self.camera_offset_horizontal):
            self.camera_offset_horizontal = goal_offset_horizontal

        camera_pos += camera_transform.left * self.camera_offset_horizontal

        # camera offset vertical
        goal_offset_vertical = aim_y_diff_ratio * CAMERA_OFFSET_VERTICAL
        diff_offset_vertical = goal_offset_vertical - self.camera_offset_vertical
        sign_offset_vertical = np.sign(diff_offset_vertical)
        self.camera_offset_vertical += camera_offset_speed * abs(diff_offset_vertical) * sign_offset_vertical

        if 0.0 != sign_offset_vertical and sign_offset_vertical != np.sign(goal_offset_vertical - self.camera_offset_vertical):
            self.camera_offset_vertical = goal_offset_vertical

        camera_shake = self.camera_shake.get_camera_shake()
        camera_pos += camera_transform.up * camera_shake[0] + camera_transform.left * camera_shake[1]
        camera_pos += camera_transform.up * self.camera_offset_vertical
        camera_pos[1] += CAMERA_OFFSET_Y
        camera_transform.set_pos(camera_pos)

    def find_target_actor(self):
        camera_transform = self.main_camera.transform
        camera_pos = camera_transform.get_pos()
        aim_dir = -camera_transform.front

        self.target_actor = None
        self.target_actor_distance = 0.0
        target_dist = 10000000.0

        for actor in self.actor_manager.actors:
            to_actor = actor.get_center() - camera_pos
            d = np.dot(aim_dir, to_actor)
            if 0.0 < d:
                c = to_actor - aim_dir * d
                angle = math.atan2(length(c), d)
                if angle < AIM_ANGLE_THRESHOLD:
                    x = np.dot(camera_transform.left, to_actor)
                    y = np.dot(camera_transform.up, to_actor)
                    dist = math.sqrt(x*x + y*y)
                    if dist < target_dist:
                        target_dist = dist
                        self.target_actor = actor
                        self.target_actor_distance = length(to_actor)
        if self.target_actor is not None:
            self.scene_manager.set_selected_object(self.target_actor.actor_object.name)

    def set_camera_shake(self, damage):
        total_camera_shake_time = 0.5
        camera_shake_intensity = 0.5
        if 10.0 < damage:
            total_camera_shake_time = 1.0
            camera_shake_intensity = 1.0

        camera_shake_intensity *= self.main_viewport.width / 1024
        self.camera_shake.set_camera_shake(total_camera_shake_time, camera_shake_intensity)

    def update(self, delta_time):
        self.camera_shake.update(delta_time)
        self.update_player(delta_time)
        self.actor_manager.update_actors(delta_time)
        self.find_target_actor()
        self.bullet_manager.update_bullets(delta_time, self.actor_manager.actors)
        self.game_effect_manager.update()
