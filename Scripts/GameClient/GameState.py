from enum import Enum

from PyEngine3D.Utilities import StateMachine, StateItem


class KEY_FLAG:
    NONE = 0
    MOVE = 1 << 0


class STATES:
    NONE = 0
    IDLE = 1
    MOVE = 2


class StateInfo:
    def __init__(self):
        self.delta = 0.0
        self.elapsed_time = 0.0
        self.player = None
        self.animation_meshes = {}
        self.on_ground = False
        self.key_flag = KEY_FLAG.NONE

    def set_info(self, delta, player, animation_meshes, on_ground, key_flag):
        self.delta = delta
        self.player = player
        self.animation_meshes = animation_meshes
        self.on_ground = on_ground
        self.key_flag = key_flag


class StateBase(StateItem):
    pass


class StateNone(StateBase):
    def on_update(self, state_info=None):
        self.state_manager.set_state(STATES.IDLE, state_info)


class StateIdle(StateBase):
    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['idle'], loop=True, blend_time=0.1)

    def on_update(self, state_info=None):
        if state_info.key_flag & KEY_FLAG.MOVE:
            self.state_manager.set_state(STATES.MOVE, state_info)


class StateMove(StateBase):
    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['idle'], loop=True, blend_time=0.1)

    def on_update(self, state_info=None):
        if not (state_info.key_flag & KEY_FLAG.MOVE):
            self.state_manager.set_state(STATES.IDLE, state_info)



class GameStateManager(StateMachine):
    def __init__(self, *args, **kargs):
        StateMachine.__init__(self, *args, **kargs)
        self.delta = 0.0
        self.elapsed_time = 0.0
        self.state_info = StateInfo()
        self.add_state(StateNone, STATES.NONE)
        self.add_state(StateMove, STATES.MOVE)

        self.set_state(STATES.NONE)

    def update_state(self, delta, player, animation_meshes, on_ground, key_flag):
        self.state_info.set_info(delta, player, animation_meshes, on_ground, key_flag)
        StateMachine.update_state(self, self.state_info)
        self.state_info.elapsed_time += delta
