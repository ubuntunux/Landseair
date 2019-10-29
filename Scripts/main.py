import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton
from GameClient import GameClient


class ScriptManager(Singleton):
    def __init__(self):
        self.game_client = None

    def initialize(self, core_manager):
        logger.info("ScriptManager::initialize")

        self.game_client = GameClient()
        self.game_client.initialize(core_manager)

    def exit(self):
        if self.game_client is not None:
            self.game_client.exit()
        self.game_client = None

    def update(self, delta):
        self.game_client.update(delta)
