import gym
from gym import error, spaces, utils
import random
import importlib
from gym_risk.envs.game import Game
from gym_risk.envs.ai.random import RandomAI

class RiskEnv(gym.Env):
    """
    3 players Risk with two Random AI to compete against
    """
    #todo different AIs to compete against

    metadata = {'render.modes' : ['human']}

    def __init__(self):
        self.game = Game()
        self.game.add_player("Random_1", RandomAI)
        self.game.add_player("Random_2", RandomAI)


    def seed(self, seed=None):
        #todo improve with gym.utils.seeding
        random.seed(seed)

    def step(self, action):
        pass

    def reset(self):
        pass

    #todo render, curses and so on
    def render(self, mode='human', close=False):
        #delay = 0.1 for humans else 0
        pass
