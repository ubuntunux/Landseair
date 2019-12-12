import math
from enum import Enum

from PyEngine3D.Utilities import *
from GameClient.GameStates import STATES


class StateNone(StateItem):
    def on_update(self, state_machine, delta_time):
        actor = state_machine.actor
        actor_transform = actor.actor_object.transform
        actor_transform.set_yaw(state_machine.elapsed_time * 0.1)


class TankStateMachine(StateMachine):
    def __init__(self):
        StateMachine.__init__(self)
        self.actor = None
        self.delta = 0.0
        self.elapsed_time = 0.0
        self.add_state(StateNone, STATES.NONE)
        self.set_state(STATES.NONE)

    def initialize(self, actor):
        self.actor = actor

    def update_state(self, delta_time):
        self.delta = delta_time
        StateMachine.update_state(self, self, delta_time)

        self.elapsed_time += delta_time
