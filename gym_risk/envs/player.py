from copy import deepcopy


class Player(object):
    def __init__(self, name, game, ai_class):
        self.name = name
        self.color = 0
        self.ord = 32
        self.game = game
        if ai_class is not None:
            self.ai = ai_class(self, game, game.world)
        else:
            self.ai = None
        self.world = game.world

    @property
    def territories(self):
        for t in self.world.territories.values():
            if t.owner == self:
                yield t

    @property
    def territory_count(self):
        count = 0
        for t in self.world.territories.values():
            if t.owner == self:
                count += 1
        return count

    @property
    def areas(self):
        for a in self.world.areas.values():
            if a.owner == self:
                yield a

    @property
    def forces(self):
        return sum(t.forces for t in self.territories)

    @property
    def alive(self):
        return self.territory_count > 0

    @property
    def reinforcements(self):
        return max(self.territory_count // 3, 3) + sum(a.value for a in self.areas)

    def __repr__(self):
        return "P;%s;%s" % (self.name, self.ai.__class__.__name__)

    def __hash__(self):
        return hash(("player", self.name))

    def __eq__(self, other):
        if isinstance(other, Player):
            return self.name == other.name
        return False

    def __deepcopy__(self, memo):
        newobj = Player(self.name, self, None)
        newobj.color = self.color
        newobj.ord = self.ord
        #newobj.__dict__.update(deepcopy(self.__dict__, memo))
        newobj.game = deepcopy(self.game, memo)
        newobj.world = newobj.game.world
        newobj.ai = type(self.ai)(newobj, newobj.game, newobj.world) if self.ai is not None else None
        return newobj
