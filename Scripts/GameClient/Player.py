from PyEngine3D.Utilities import *
from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND
from GameClient.Constants import *


class Player:
    def __init__(self, scene_manager, resource_manager):
        main_camera = scene_manager.main_camera
        pos = main_camera.transform.pos - main_camera.transform.front * 5.0
        player_model = resource_manager.get_model("Plane00")
        bullet_model = resource_manager.get_model("Cube")

        self.player_object = scene_manager.add_object(model=player_model, pos=pos)
        self.bullet_object = scene_manager.add_object(model=bullet_model, pos=pos)

        self.player_object.transform.set_pos([0.0, 5.0, 0.0])
        self.player_object.transform.set_yaw(3.141592)
        self.player_object.transform.set_scale(1.0)
        self.player_object.transform.euler_to_quaternion()
        self.player_object.transform.set_use_quaternion(False)
        self.bullet_object.transform.set_use_quaternion(False)

        self.fire_bullet = False
        self.on_ground = False
        self.velocity = Float3(0.0, 0.0, 0.0)

    def destroy(self, scene_manager):
        scene_manager.delete_object(self.player_object.name)
        scene_manager.delete_object(self.bullet_object.name)

    def get_pos(self):
        return self.player_object.transform.get_pos()

    def get_transform(self):
        return self.player_object.transform

    def update(self, delta_time, game_client, aim_x_ratio, aim_y_ratio, aim_x_diff_ratio, aim_y_diff_ratio):
        game_backend = game_client.game_backend
        scene_manager = game_client.scene_manager
        screen_width = game_client.main_viewport.width
        screen_height = game_client.main_viewport.height
        crosshair = game_client.crosshair
        player_aim = game_client.player_aim

        keydown = game_backend.get_keyboard_pressed()
        keyup = game_backend.get_keyboard_released()
        mouse_delta = game_backend.mouse_delta
        mouse_pos = game_backend.mouse_pos
        btn_left, btn_middle, btn_right = game_backend.get_mouse_pressed()
        camera = scene_manager.main_camera
        bullet_transform = self.bullet_object.transform
        player_transform = self.player_object.transform
        old_player_pos = player_transform.get_pos().copy()
        is_mouse_grab = game_backend.get_mouse_grab()

        if is_mouse_grab:
            rotation_speed = ROTATION_SPEED * delta_time
            ratio_x = -1.0 if 0.0 <= player_transform.up[1] else 1.0
            player_transform.rotation_pitch(-rotation_speed * aim_y_diff_ratio)
            player_transform.rotation_yaw(rotation_speed * aim_x_diff_ratio * ratio_x)
            player_transform.set_roll(ROLL_AMOUNT * (aim_x_ratio * 2.0 - 1.0))
            player_transform.update_transform()

            # player_transform.set_use_quaternion(True)
            # rotation_speed = ROTATION_SPEED * delta_time
            # aim_x_diff_ratio = (crosshair.center_x / screen_width - 0.5) * 2.0
            # aim_y_diff_ratio = (crosshair.center_y / screen_height - 0.5) * 2.0
            # ql = QUATERNION_IDENTITY.copy()
            # qf = QUATERNION_IDENTITY.copy()
            # qu = QUATERNION_IDENTITY.copy()
            # ql = get_quaternion(player_transform.left, rotation_speed * aim_y_diff_ratio)
            # # qf = get_quaternion(player_transform.front, -rotation_speed * aim_x_diff_ratio)
            # qu = get_quaternion(Float3(0.0, 1.0, 0.0), -rotation_speed * aim_x_diff_ratio)
            # quat = muliply_quaternions(ql, qf, qu)
            # player_transform.rotation_quaternion(quat)
            # player_transform.update_transform()

        # fire bullet
        if btn_left or keyup.get(Keyboard.SPACE):
            self.fire_bullet = True
            bullet_transform.set_pos(old_player_pos)
            bullet_transform.set_rotation(player_transform.get_rotation())

        if self.fire_bullet:
            if length(bullet_transform.get_pos() - player_transform.get_pos()) < 1000.0:
                bullet_transform.move_front((BULLET_SPEED + MOVE_SPEED) * delta_time)
            else:
                self.fire_bullet = False

        # move to forward
        forward_dir = player_transform.front.copy()
        forward_dir[1] = 0.0
        forward_dir = normalize(forward_dir)
        self.velocity[...] = forward_dir * (1.0 + (0.5 - forward_dir[1] * 0.5)) * MOVE_SPEED

        move_delta = self.velocity * delta_time
        player_pos = old_player_pos + move_delta

        self.on_ground = False

        def compute_collide(i, old_position, position, move_delta, bound_box):
            j = (i + 1) % 3
            k = (i + 2) % 3

            def is_in_plane(index, ratio):
                if index == 1:
                    return bound_box.bound_min[index] < (
                                old_position[index] + move_delta[index] * ratio + BOUND_BOX_OFFSET) < bound_box.bound_max[
                               index]
                else:
                    return bound_box.bound_min[index] < (old_position[index] + move_delta[index] * ratio) < \
                           bound_box.bound_max[index]

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

        for collision_actor in scene_manager.collision_actors:
            for geometry_bound_box in collision_actor.get_geometry_bound_boxes():
                for i in range(3):
                    compute_collide(i, old_player_pos, player_pos, move_delta, geometry_bound_box)

        if self.on_ground:
            self.velocity[1] = 0.0

        player_transform.set_pos(player_pos)

