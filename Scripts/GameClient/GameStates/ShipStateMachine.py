import math
from enum import Enum

from PyEngine3D.Utilities import *
from GameClient.Constants import *
from GameClient.GameStates import *


class StateNone(StateItem):
    def on_update(self, state_machine, delta_time):
        actor = state_machine.actor
        t = abs((((id(self) * 0.314515 + state_machine.elapsed_time) * 0.1) % 1.0) * 2.0 - 1.0)
        pos0 = actor.spline_path.get_resampling_position(t)
        delta = pos0 - actor.actor_object.transform.get_pos()
        delta_direction = normalize(delta)
        d = np.dot(delta_direction, actor.actor_object.transform.front)
        if abs(d) < 0.999:
            if actor.apply_axis_y:
                actor.actor_object.transform.front[...] = delta_direction
                actor.actor_object.transform.left[...] = normalize(np.cross(actor.actor_object.transform.up, delta_direction))
                actor.actor_object.transform.up[...] = normalize(np.cross(delta_direction, actor.actor_object.transform.left))
            else:
                actor.actor_object.transform.up[...] = WORLD_UP
                actor.actor_object.transform.left[...] = normalize(np.cross(actor.actor_object.transform.up, delta_direction))
                actor.actor_object.transform.front[...] = normalize(np.cross(actor.actor_object.transform.left, actor.actor_object.transform.up))
            actor.actor_object.transform.rotationMatrix[0][0:3] = actor.actor_object.transform.left
            actor.actor_object.transform.rotationMatrix[1][0:3] = actor.actor_object.transform.up
            actor.actor_object.transform.rotationMatrix[2][0:3] = actor.actor_object.transform.front

        actor.actor_object.transform.set_pos(pos0)


class ShipStateMachine(BaseStateMachine):
    def __init__(self, game_client):
        BaseStateMachine.__init__(self, game_client)
        self.add_state(StateNone, STATES.NONE)

    def initialize(self, actor):
        BaseStateMachine.initialize(self, actor)

        self.set_state(STATES.NONE)

    def update_state(self, delta_time):
        self.delta = delta_time
        StateMachine.update_state(self, self, delta_time)

        self.elapsed_time += delta_time
