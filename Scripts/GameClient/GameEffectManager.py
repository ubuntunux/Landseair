import numpy as np

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger, log_level, COMMAND

from GameClient.Constants import *

EXPLOSION_00 = "explosion_00"
DAMAGE_00 = "damage_00"


class GameEffectManager:
    def __init__(self):
        self.scene_manager = None
        self.resource_manager = None
        self.effect_instances = []

    def initialize(self, scene_manager, resource_manager):
        self.scene_manager = scene_manager
        self.resource_manager = resource_manager

    def create_explosion_particle(self, pos):
        effect_info = self.scene_manager.add_effect(name=EXPLOSION_00, effect_info=EXPLOSION_00, pos=pos, scale=(10.0, 10.0, 10.0))
        self.effect_instances.append(effect_info)

    def create_damage_particle(self, pos):
        effect_info = self.scene_manager.add_effect(name=DAMAGE_00, effect_info=DAMAGE_00, pos=pos, scale=(1.0, 1.0, 1.0))
        self.effect_instances.append(effect_info)

    def update(self):
        index = 0
        effect_count = len(self.effect_instances)
        for i in range(effect_count):
            effct_instance = self.effect_instances[index]
            if effct_instance.alive:
                index += 1
            else:
                self.scene_manager.delete_object(effct_instance.name)
                self.effect_instances.pop(index)
