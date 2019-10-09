from enum import Enum
from PyEngine3D.Utilities import StateMachine, StateItem


class STATES:
    NONE = 0


class StateBase(StateItem):
    pass


class StateNone(StateBase):
    def on_update(self, state_info=None):
        pass


class GameStateManager(StateMachine):
    def __init__(self, *args, **kargs):
        StateMachine.__init__(self, *args, **kargs)
        self.delta = 0.0
        self.elapsed_time = 0.0
        self.add_state(StateNone, STATES.NONE)

        self.set_state(STATES.NONE)

    def update_state(self, delta_time):
        self.delta = delta_time
        StateMachine.update_state(self, delta_time)

        self.elapsed_time += delta_time
