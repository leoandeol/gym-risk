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
        for t, o in self.world.owners.items():
            if o == self:
                yield t

    @property
    def territory_count(self):
        #todo document
        #return sum(map((self).__eq__, self.world.owners.values())) #actually slower even though faster than sum(value==self for ...
        return list(self.world.owners.values()).count(self)

    @property
    def areas(self):
        for a, t in self.world.areas.items():
            test = True
            for tt in t:
                if self.world.owners[tt] is not self:
                    test = False
                    break
            if test:
                yield a

    @property
    def forces(self):
        return sum(y for x, y in self.world.forces.items() if self.world.owners[x] is self)

    @property
    def alive(self):
        return self.territory_count > 0

    @property
    def reinforcements(self):
        return max(self.territory_count // 3, 3) + sum(self.world.area_values[a] for a in self.areas)

    def __repr__(self):
        return "P;%s;%s" % (self.name, self.ai.__class__.__name__)

    def __hash__(self):
        return hash(("player", self.name))

    def __eq__(self, other):
        #todo safer but still fast way
        #if self.__class__.__name__ == other.__class__.__name__:
        return self.name == other.name
        #return False

    def __deepcopy__(self, memo):
        newobj = Player(self.name, self, None)
        newobj.color = self.color
        newobj.ord = self.ord
        #newobj.__dict__.update(deepcopy(self.__dict__, memo))
        newobj.game = deepcopy(self.game, memo)
        newobj.world = newobj.game.world
        newobj.ai = type(self.ai)(newobj, newobj.game, newobj.world) if self.ai is not None else None
        return newobj
