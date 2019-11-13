import numpy as np

from PyEngine3D.Utilities import *
from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger, log_level, COMMAND

from GameClient.Constants import *
from GameClient.GameState import TankStateMachine


class ActorManager:
    def __init__(self):
        self.scene_manager = None
        self.resource_manager = None
        self.game_effect_manager = None
        self.player_actor = None
        self.actors = []
        self.animation_meshes = {}

    def initialize(self, scene_manager, resource_manager, game_effect_manager):
        self.scene_manager = scene_manager
        self.resource_manager = resource_manager
        self.game_effect_manager = game_effect_manager

        animation_list = ['idle']

        for key in animation_list:
            # self.animation_meshes[key] = self.resource_manager.get_mesh("Plane00_" + key)
            self.animation_meshes[key] = resource_manager.get_mesh("Plane00")

        self.player_actor = PlayerActor(self.scene_manager, self.resource_manager, actor_model="Plane00", pos=Float3(0.0, 5.0, 0.0), rotation=PI, scale=1.0)

        count = 10
        for i in range(count):
            pos = np.random.rand(3) * Float3(100.0, 10.0, 100.0)
            pos[1] += 5.0
            rotation = np.random.rand() * TWO_PI
            actor = BaseActor(scene_manager, resource_manager, actor_model="Plane00", pos=pos, rotation=rotation)
            self.actors.append(actor)

        count = 10
        for i in range(count):
            pos = np.random.rand(3) * Float3(100.0, 10.0, 100.0)
            pos[1] += 5.0
            rotation = np.random.rand() * TWO_PI
            state_machine = TankStateMachine()
            actor = BaseActor(scene_manager, resource_manager, actor_model="Tank", pos=pos, rotation=rotation, state_machine=state_machine)
            self.actors.append(actor)

    def destroy(self):
        self.destroy_actor(self.player_actor)
        self.player_actor = None

        for actor in self.actors:
            self.destroy_actor(actor)
        self.actors = []

    def destroy_actor(self, actor):
        actor.destroy(self.scene_manager)

    def update_actors(self, delta_time):
        index = 0
        actor_count = len(self.actors)

        for i in range(actor_count):
            actor = self.actors[index]
            if actor.is_alive:
                actor.update_actor(self, delta_time)
                index += 1
            else:
                # dead
                self.game_effect_manager.create_explosion_particle(actor.get_pos())
                self.destroy_actor(actor)
                self.actors.pop(index)


class BaseActor:
    isPlayer = False

    def __init__(self, scene_manager, resource_manager, actor_model, pos=Float3(0.0), rotation=0.0, scale=1.0, state_machine=None):
        actor_model = resource_manager.get_model(actor_model)

        self.actor_object = scene_manager.add_object(model=actor_model)
        self.actor_object.transform.set_pos(pos)
        self.actor_object.transform.set_yaw(rotation)
        self.actor_object.transform.set_scale(scale)

        self.is_alive = True
        self.hp = 3
        self.acceleration = 1.0
        self.side_acceleration = 0.0
        self.velocity = Float3(0.0, 0.0, 0.0)

        self.state_machine = state_machine
        if self.state_machine is not None:
            self.state_machine.initialize(self)

    def set_dead(self):
        self.is_alive = False

    def set_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.set_dead()

    def destroy(self, scene_manager):
        scene_manager.delete_object(self.actor_object.name)

    def get_center(self):
        return self.actor_object.bound_box.bound_center

    def get_pos(self):
        return self.actor_object.transform.get_pos()

    def get_transform(self):
        return self.actor_object.transform

    def update_actor(self, game_client, delta_time):
        if self.state_machine is not None:
            self.state_machine.update_state(delta_time)


class PlayerActor(BaseActor):
    isPlayer = True

    def update_player(self, game_client, delta_time, crosshair_x_ratio, crosshair_y_ratio, goal_aim_pitch, goal_aim_yaw):
        game_backend = game_client.game_backend
        keydown = game_backend.get_keyboard_pressed()
        keyup = game_backend.get_keyboard_released()
        mouse_delta = game_backend.mouse_delta
        mouse_pos = game_backend.mouse_pos
        btn_left, btn_middle, btn_right = game_backend.get_mouse_pressed()
        actor_transform = self.actor_object.transform
        old_actor_pos = actor_transform.get_pos().copy()
        is_mouse_grab = game_backend.get_mouse_grab()

        actor_pitch = actor_transform.get_pitch()
        actor_yaw = actor_transform.get_yaw()
        actor_roll = actor_transform.get_roll()

        diff_pitch = (goal_aim_pitch - actor_pitch)
        if PI < diff_pitch or diff_pitch < -PI:
            diff_pitch -= np.sign(diff_pitch) * TWO_PI

        diff_yaw = (goal_aim_yaw - actor_yaw)
        if PI < diff_yaw or diff_yaw < -PI:
            diff_yaw -= np.sign(diff_yaw) * TWO_PI

        goal_actor_roll = clamp_radian(
            ROTATION_ROLL_LIMIT * ((crosshair_x_ratio * 2.0 - 1.0) - self.side_acceleration * 0.3))
        diff_roll = (goal_actor_roll - actor_roll)
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
                actor_transform.set_pitch(goal_aim_pitch)
            else:
                actor_transform.rotation_pitch(pitch_speed * np.sign(diff_pitch))

            result_pitch = actor_transform.get_pitch()

            # pitch threashold
            if PI * 1.5 < result_pitch < (TWO_PI - ROTATION_PITCH_LIMIT):
                actor_transform.set_pitch(TWO_PI - ROTATION_PITCH_LIMIT)
            elif ROTATION_PITCH_LIMIT < result_pitch < PI * 0.5:
                actor_transform.set_pitch(ROTATION_PITCH_LIMIT)

            # set yaw
            if abs(diff_yaw) <= yaw_speed:
                actor_transform.set_yaw(goal_aim_yaw)
            else:
                actor_transform.rotation_yaw(yaw_speed * np.sign(diff_yaw))

            # set roll
            if abs(diff_roll) <= roll_speed:
                actor_transform.set_roll(goal_actor_roll)
            else:
                actor_transform.rotation_roll(roll_speed * np.sign(diff_roll))

            result_roll = actor_transform.get_roll()

            # roll threashold
            if PI * 1.5 < result_roll < (TWO_PI - ROTATION_ROLL_LIMIT):
                actor_transform.set_roll(TWO_PI - ROTATION_ROLL_LIMIT)
            elif ROTATION_PITCH_LIMIT < result_roll < PI * 0.5:
                actor_transform.set_roll(ROTATION_ROLL_LIMIT)

            actor_transform.update_transform()

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

        forward_dir = actor_transform.front.copy()
        side_dir = actor_transform.left.copy()
        forward_dir[1] = 0.0
        side_dir[1] = 0.0
        forward_dir = normalize(forward_dir)
        side_dir = normalize(side_dir)
        self.velocity[...] = forward_dir * self.acceleration * FORWARD_MOVE_SPEED + side_dir * self.side_acceleration * SIDE_MOVE_SPEED

        move_delta = self.velocity * delta_time
        actor_pos = old_actor_pos + move_delta

        actor_transform.set_pos(actor_pos)
