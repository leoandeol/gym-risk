from gym_risk.envs.game.ai import AI
import random
import collections

class RandomAI(AI):
    """
    RandomAI: Plays a completely random game, randomly choosing and reinforcing
    territories, and attacking wherever it can without any considerations of wisdom.
    """
    def initial_placement(self, empty):
        if empty:
            return random.choice(empty)
        else:
            t = random.choice(list(self.player.territories))
            return t

    def attack(self):
        for t in self.player.territories:
            for a in self.player.world.connections[t]:
                if self.world.owners[a] != self.player:
                    if self.world.forces[t] > self.world.forces[a]:
                        yield (t, a, None, None)

    def reinforce(self, available):
        #todo .... territories if t.border : fix so it can work
        border = [t for t in self.player.territories]
        result = collections.defaultdict(int)
        for i in range(available):
            t = random.choice(border)
            result[t] += 1
        return result
