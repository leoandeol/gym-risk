import gym
import random
from gym_risk.envs.game import Game
from gym_risk.envs.game.ai.random import RandomAI
from gym.utils.seeding import create_seed, hash_seed


class DraftingRiskEnv(gym.Env):
    """
    3 players Risk - only the drafting phase - with two Random AI to compete against
    """
    # todo compete against itself
    # todo different AIs to compete against
    # todo env space (discrete/box) + info from step
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.game = None
        self.seed_ = None
        self.seed()

    def seed(self, seed=None):
        if seed is None:
            self.seed = create_seed()
            random.seed(self.seed_)
        else:
            self.seed_ = hash_seed(seed)
            random.seed(self.seed_)

    def reset(self):
        self.game = Game()
        self.game.add_player("Random_1", RandomAI)
        self.game.add_player("Random_2", RandomAI)
        return self.game.init()

    def step(self, action):
        return self.game.step_drafting(action)

    # todo render, curses and so on
    def render(self, mode='human', close=False):
        # delay = 0.1 for humans else 0
        pass
