import math
from enum import Enum

import numpy as np

from PyEngine3D.Utilities import *
from GameClient.GameStates import *


class StateIdle(StateItem):
    def on_enter(self):
        self.state_manager.idle_time = self.state_manager.IDLE_TIME.get_uniform()

    def on_update(self, delta_time):
        if self.state_manager.idle_time < 0.0:
            self.state_manager.set_state(STATES.PATROL)
        self.state_manager.idle_time -= delta_time


class StatePatrol(StateItem):
    def on_enter(self):
        self.state_manager.patrol_time = self.state_manager.PATROL_TIME.get_uniform()
        self.state_manager.patrol_rotation_angle = self.state_manager.PATROL_ROTATION_ANGLE.get_uniform()

    def on_update(self, delta_time):
        player_actor = self.state_manager.actor_manager.player_actor
        actor = self.state_manager.actor
        actor_transform = actor.actor_object.transform
        actor_transform.rotation_yaw(self.state_manager.patrol_rotation_angle * delta_time)

        dist = get_distance(player_actor, actor)

        if dist < self.state_manager.DECTECTION_DISTANCE:
            self.state_manager.set_state(STATES.DETECTION)
        elif self.state_manager.patrol_time < 0.0:
            self.state_manager.set_state(STATES.IDLE)
        self.state_manager.patrol_time -= delta_time


class StateDetection(StateItem):
    def on_enter(self):
        self.state_manager.detection_time = self.state_manager.DETECTION_TIME

    def on_update(self, delta_time):
        player_actor = self.state_manager.actor_manager.player_actor
        actor = self.state_manager.actor

        look_at_actor(player_actor, actor, self.state_manager.DECTECTION_ROTATION_SPEED, delta_time)
        dist = get_distance(player_actor, actor)

        if self.state_manager.DECTECTION_DISTANCE < dist:
            self.state_manager.set_state(STATES.IDLE)
        elif self.state_manager.detection_time <= 0.0:
            self.state_manager.set_state(STATES.FIRE)

        self.state_manager.detection_time -= delta_time


class StateFire(StateItem):
    def on_enter(self):
        self.state_manager.detection_time = 0.0

    def on_update(self, delta_time):
        player_actor = self.state_manager.actor_manager.player_actor
        actor = self.state_manager.actor
        look_at_actor(player_actor, actor, self.state_manager.DECTECTION_ROTATION_SPEED, delta_time)

        if self.state_manager.detection_time <= 0.0:
            camera_transform = self.state_manager.game_client.main_camera.transform
            pos = actor.actor_object.get_center()
            player_pos = player_actor.actor_object.get_center()

            fire_direction = normalize(player_pos - pos)
            fire_dist_xz = length(Float2(fire_direction[0], fire_direction[2]))

            front_direction = actor.actor_object.transform.front.copy()
            front_dist_xz = length(Float2(front_direction[0], front_direction[2]))

            fire_direction[0] = (front_direction[0] / front_dist_xz) * fire_dist_xz
            fire_direction[2] = (front_direction[2] / front_dist_xz) * fire_dist_xz

            self.state_manager.actor.bullet.fire(pos, fire_direction, camera_transform, 0.0)
            self.state_manager.detection_time += self.state_manager.FIRE_DELAY
        else:
            self.state_manager.detection_time -= delta_time


class TankStateMachine(StateMachine):
    IDLE_TIME = RangeVariable(2.0, 3.0)
    PATROL_TIME = RangeVariable(2.0, 3.0)
    PATROL_ROTATION_ANGLE = RangeVariable(-1.5, 1.5)
    DECTECTION_DISTANCE = 20.0
    DECTECTION_ROTATION_SPEED = 1.0
    DETECTION_TIME = 1.0
    FIRE_DELAY = 1.0

    def __init__(self, game_client):
        StateMachine.__init__(self)
        self.game_client = game_client
        self.actor_manager = game_client.actor_manager
        self.bullet_manager = game_client.bullet_manager
        self.player_actor = game_client.actor_manager.player_actor
        self.delta = 0.0
        self.elapsed_time = 0.0
        self.idle_time = 0.0
        self.patrol_time = 0.0
        self.patrol_rotation_angle = 0.0
        self.detection_time = 0.0
        self.fire_delay = 0.0

        self.add_state(StateIdle, STATES.IDLE)
        self.add_state(StatePatrol, STATES.PATROL)
        self.add_state(StateDetection, STATES.DETECTION)
        self.add_state(StateFire, STATES.FIRE)

    def initialize(self, actor):
        self.actor = actor
        self.set_state(STATES.IDLE)

    def update_state(self, delta_time):
        self.delta = delta_time
        super(TankStateMachine, self).update_state(delta_time)

        self.elapsed_time += delta_time
