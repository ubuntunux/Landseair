from PyEngine3D.Utilities import *
from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND

from GameClient.Bullet import BulletActor
from GameClient.Constants import *


class PlayerActor:
    def __init__(self, scene_manager, resource_manager):
        main_camera = scene_manager.main_camera
        pos = main_camera.transform.pos - main_camera.transform.front * 5.0
        player_model = resource_manager.get_model("Plane00")

        self.player_object = scene_manager.add_object(model=player_model, pos=pos)
        self.bullet_actor = BulletActor(scene_manager, resource_manager)

        self.player_object.transform.set_pos([0.0, 5.0, 0.0])
        self.player_object.transform.set_yaw(3.141592)
        self.player_object.transform.set_scale(1.0)
        self.acceleration = 1.0
        self.side_acceleration = 0.0
        self.velocity = Float3(0.0, 0.0, 0.0)

    def destroy(self, scene_manager):
        scene_manager.delete_object(self.player_object.name)

    def get_pos(self):
        return self.player_object.transform.get_pos()

    def get_transform(self):
        return self.player_object.transform

    def update(self, delta_time, game_client, crosshair_x_ratio, crosshair_y_ratio, aim_x_ratio, aim_y_ratio, goal_aim_pitch, goal_aim_yaw):
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
        player_transform = self.player_object.transform
        old_player_pos = player_transform.get_pos().copy()
        is_mouse_grab = game_backend.get_mouse_grab()

        player_pitch = player_transform.get_pitch()
        player_yaw = player_transform.get_yaw()
        player_roll = player_transform.get_roll()

        diff_pitch = (goal_aim_pitch - player_pitch)
        if PI < diff_pitch or diff_pitch < -PI:
            diff_pitch -= np.sign(diff_pitch) * TWO_PI

        diff_yaw = (goal_aim_yaw - player_yaw)
        if PI < diff_yaw or diff_yaw < -PI:
            diff_yaw -= np.sign(diff_yaw) * TWO_PI

        goal_player_roll = clamp_radian(ROTATION_ROLL_LIMIT * ((crosshair_x_ratio * 2.0 - 1.0) - self.side_acceleration * 0.3))
        diff_roll = (goal_player_roll - player_roll)
        if PI < diff_roll or diff_roll < -PI:
            diff_roll -= np.sign(diff_roll) * TWO_PI

        if is_mouse_grab:
            pitch_speed_ratio = abs(crosshair_y_ratio * 2.0 - 1.0)
            yaw_speed_ratio = abs(crosshair_x_ratio * 2.0 - 1.0)
            pitch_speed = pitch_speed_ratio * ROTATION_SPEED * delta_time
            yaw_speed = yaw_speed_ratio * ROTATION_SPEED * delta_time
            roll_speed = ROTATION_ROLL_SPEED * delta_time

            # set pitch
            if abs(diff_pitch) <= pitch_speed:
                player_transform.set_pitch(goal_aim_pitch)
            else:
                player_transform.rotation_pitch(pitch_speed * np.sign(diff_pitch))

            result_pitch = player_transform.get_pitch()

            # pitch threashold
            if PI * 1.5 < result_pitch < (TWO_PI - ROTATION_PITCH_LIMIT):
                player_transform.set_pitch(TWO_PI - ROTATION_PITCH_LIMIT)
            elif ROTATION_PITCH_LIMIT < result_pitch < PI * 0.5:
                player_transform.set_pitch(ROTATION_PITCH_LIMIT)

            # set yaw
            if abs(diff_yaw) <= yaw_speed:
                player_transform.set_yaw(goal_aim_yaw)
            else:
                player_transform.rotation_yaw(yaw_speed * np.sign(diff_yaw))

            # set roll
            if abs(diff_roll) <= roll_speed:
                player_transform.set_roll(goal_player_roll)
            else:
                player_transform.rotation_roll(roll_speed * np.sign(diff_roll))

            result_roll = player_transform.get_roll()

            # roll threashold
            if PI * 1.5 < result_roll < (TWO_PI - ROTATION_ROLL_LIMIT):
                player_transform.set_roll(TWO_PI - ROTATION_ROLL_LIMIT)
            elif ROTATION_PITCH_LIMIT < result_roll < PI * 0.5:
                player_transform.set_roll(ROTATION_ROLL_LIMIT)

            player_transform.update_transform()

        # move
        if keydown[Keyboard.W]:
            self.acceleration += ACCELERATION * delta_time
        elif keydown[Keyboard.S]:
            self.acceleration -= ACCELERATION * delta_time
        self.acceleration = min(1.0, max(-0.5, self.acceleration))

        if keydown[Keyboard.A]:
            self.side_acceleration += SIDE_ACCELERATION * delta_time
        elif keydown[Keyboard.D]:
            self.side_acceleration -= SIDE_ACCELERATION * delta_time
        else:
            sign = np.sign(self.side_acceleration)
            self.side_acceleration -= sign * SIDE_ACCELERATION * delta_time
            if sign == self.side_acceleration:
                self.side_acceleration = 0.0
        self.side_acceleration = min(1.0, max(-1.0, self.side_acceleration))

        forward_dir = player_transform.front.copy()
        side_dir = player_transform.left.copy()
        forward_dir[1] = 0.0
        side_dir[1] = 0.0
        forward_dir = normalize(forward_dir)
        side_dir = normalize(side_dir)
        self.velocity[...] = forward_dir * self.acceleration * FORWARD_MOVE_SPEED + side_dir * self.side_acceleration * SIDE_MOVE_SPEED

        move_delta = self.velocity * delta_time
        player_pos = old_player_pos + move_delta

        player_transform.set_pos(player_pos)

        if btn_left or keydown[Keyboard.SPACE]:
            self.bullet_actor.fire(player_transform)

        self.bullet_actor.update(delta_time, player_transform)
