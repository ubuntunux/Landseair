from PyEngine3D.Utilities import *


class BaseStateMachine(StateMachine):
    def __init__(self, game_client):
        StateMachine.__init__(self)
        self.game_client = game_client
        self.game_ui_manager = game_client.game_ui_manager
        self.sound_manager = game_client.sound_manager
        self.actor_manager = game_client.actor_manager
        self.bullet_manager = game_client.bullet_manager
        self.player_actor = game_client.actor_manager.player_actor
        self.actor = None
        self.delta = 0.0
        self.elapsed_time = 0.0

    def initialize(self, actor):
        self.actor = actor

    def get_actor_pos(self):
        return self.actor.actor_object.get_center()

    def set_fire_state(self):
        pass
