import math
from enum import Enum

from PyEngine3D.Utilities import StateMachine, StateItem


class STATES:
    NONE = 0


class StateNone(StateItem):
    def on_update(self, delta_time, actor):
        actor.actor_object.transform.rotation_yaw(delta_time * math.pi)
        actor.actor_object.transform.move_front(10.0 * delta_time)


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
        StateMachine.update_state(self, delta_time, self.actor)

        self.elapsed_time += delta_time
