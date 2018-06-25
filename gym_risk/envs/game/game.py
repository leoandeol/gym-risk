from gym_risk.envs.game.player import Player
from gym_risk.envs.game.world import World
from gym import logger
import random
from copy import deepcopy


class Game(object):
    """
    This class represents an individual game, and contains the main game logic.
    """
    defaults = {
        "color": True,  # whether to use color with ncurses
        "delay": 0.1,  # seconds to sleep after each (ncurses) display update
        "round": None,  # the round number
        "wait": False,  # whether to pause and wait for a keypress after each event
        "history": {},  # the win/loss history for each player, for multiple rounds
        "deal": False  # deal out territories rather than let players choose
    }

    # todo recoder, les IAs devraient renvoyer action par action, et non pas renvoyer un generateur

    def __init__(self, **options):
        self.options = self.defaults.copy()
        # self.options.update(options)

        self.world = World()

        self.players = {}
        self.live_players = 0

        self.turn = 0
        self.turn_order = []

        self.remaining = {}
        self.drafting = False
        self.finished = False
        # todo if log ....
        # just for newer  version
        from gym import __version__ as gym_v
        if gym_v == "0.7.4" or gym_v == "0.7.3":
            logger.setLevel(40)
        else:
            logger.set_level(40)
            
    def add_player(self, name, ai_class):
        assert name not in self.players
        assert len(self.players) <= 5
        player = Player(name, self, ai_class)
        self.players[name] = player

    @property
    def player(self):
        """Property that returns the correct player object for this turn."""
        return self.players[self.turn_order[self.turn % len(self.players)]]

    def event(self, msg):
        """
        Record any game action.
        """
        logger.info(str(msg))

    def warn(self, msg):
        """
        Record any game action.
        """
        logger.warn(str(msg))

    def init(self):
        assert 2 <= len(self.players) <= 6
        self.add_player("Player", None)
        self.live_players = len(self.players)
        self.turn_order = list(self.players)
        random.shuffle(self.turn_order)
        for i, name in enumerate(self.turn_order):
            if self.players[name].ai is not None:
                self.players[name].ai.start()
        self.event(("start",))
        empty = list(self.world.owners.keys())
        available = 35 - 2 * len(self.players)
        self.remaining = {p: available for p in self.players}
        if self.options['deal']:
            random.shuffle(empty)
            while empty:
                t = empty.pop()
                t.forces += 1
                self.remaining[self.player.name] -= 1
                t.owner = self.player
                self.event(("deal", self.player, t))
                self.turn += 1
            while sum(self.remaining.values()) > 0:
                if self.remaining[self.player.name] > 0:
                    choice = self.player.ai.initial_placement(None, self.remaining[self.player.name])
                    if choice not in self.world.owners.keys():
                        self.event("invalid territory choice %s", choice)
                        self.turn += 1
                        continue
                    if choice not in empty:
                        self.event("initial invalid empty territory %s", choice)
                        self.turn += 1
                        continue
                    self.world.forces[choice] += 1
                    self.remaining[self.player.name] -= 1
                    self.event(("reinforce", self.player, choice, 1))
                    self.turn += 1
                    self.play()
                    self.drafting = True
            return "combat", self.world.copy()
        else:
            return "drafting", self.initial_placement(empty)

    # reward = 100*(((win/total)-(1/nb_players))/(1/nb_players))
    def step_drafting(self, action):
        if not self.drafting:
            t = action
            if t not in self.world.owners.keys():
                self.event("invalid territory choice")
                self.turn += 1
                empty = [x for x, y in self.world.owners.items() if y is None]
                result = self.initial_placement(empty)
                return ("drafting", result), -100, False, {"error":"invalid territory"}
            if (self.world.owners[t] is not None) and (self.world.owners[t] is not self.player):
                self.event("someone else owns this land")
                self.turn += 1
                empty = [x for x, y in self.world.owners.items() if y is None]
                result = self.initial_placement(empty)
                return ("drafting", result), -100, False, {"error":"territory already owned"}
            self.world.forces[t] +=1
            self.remaining[self.player.name] -= 1
            if self.world.owners[t] is None:
                self.world.owners[t] = self.player
                self.event(("claim", self.player, t))
            else:
                self.event(("reinforce", self.player, t, 1))
            self.turn += 1
            empty = [x for x, y in self.world.owners.items() if y is None]
            result = self.initial_placement(empty)
            if result is not None:
                # observation, reward, done, info
                # todo reward
                return ("drafting", result), 0, False, {}
            else:
                NB_PLAYOUTS = 100
                victories = 0
                from gym_risk.envs.game.ai.random import RandomAI
                self.players["Player"].ai = RandomAI(self.players["Player"], self, self.world)
                self.players["Player"].ai.start()
                world_backup = self.world.copy()
                for i in range(NB_PLAYOUTS):
                    self.world = world_backup.copy()
                    for player in self.players.values():
                        player.world = self.world
                        player.ai.world = self.world
                    self.live_players = len(self.players)
                    while self.live_players > 1:
                        if self.player.alive:
                            choices = self.player.ai.reinforce(self.player.reinforcements)
                            assert sum(choices.values()) == self.player.reinforcements
                            for t, ff in choices.items():
                                f = int(ff)
                                if t not in self.world.owners.keys():
                                    self.event("reinforce invalid territory")
                                    continue
                                if self.world.owners[t] is not self.player:
                                    self.event("reinforce unowned territory")
                                    continue
                                if f < 0:
                                    self.event("reinforce invalid count")
                                    continue
                                self.world.forces[t] += f
                                self.event(("reinforce", self.player, t, f))

                            for src, target, attack, move in self.player.ai.attack():
                                if src not in self.world.owners.keys():
                                    self.event("attack invalid src %s", src)
                                    continue
                                if target not in self.world.owners.keys():
                                    self.event("attack invalid target")
                                    continue
                                if self.world.owners[src] is not self.player:
                                    self.warn("attack unowned src")
                                    continue
                                if self.world.owners[target] is self.player:
                                    self.warn("attack owned target")
                                    continue
                                if target not in self.world.connections[src]:
                                    self.event("attack unconnected")
                                    continue
                                initial_forces = (self.world.forces[src], self.world.forces[target])
                                opponent = self.world.owners[target]
                                victory = self.combat(src, target, attack, move)
                                final_forces = (self.world.forces[src], self.world.forces[target])
                                self.event(("conquer" if victory else "defeat", self.player, opponent, src, target,
                                            initial_forces, final_forces))
                            freemove = self.player.ai.freemove()
                            if freemove:
                                src, target, count = freemove
                                f = int(count)
                                valid = True
                                if src not in self.world.owners.keys():
                                    self.event("freemove invalid src %s", src)
                                    valid = False
                                if target not in self.world.owners.keys():
                                    self.event("freemove invalid target %s", target)
                                    valid = False
                                if self.world.owners[src] is not self.player:
                                    self.event("freemove unowned src %s", src)
                                    valid = False
                                if self.world.owners[target] is not self.player:
                                    self.event("freemove unowned target %s", target)
                                    valid = False
                                if not 0 <= f < self.world.forces[src]:
                                    self.event("freemove invalid count %s", f)
                                    valid = False
                                if valid:
                                    self.world.forces[src] -= count
                                    self.world.forces[target] += count
                                    self.event(("move", self.player, src, target, count))
                        self.live_players = len([p for p in self.players.values() if p.alive])
                        self.turn += 1
                    winner = [p for p in self.players.values() if p.alive][0]
                    self.event(("victory", winner))
                    if winner is self.players["Player"]:
                        victories += 1
                for p in self.players.values():
                    p.ai.end()
                reward = 100 * (((victories / NB_PLAYOUTS) - (1 / len(self.players))) / (1 / len(self.players)))
                return ("done", self.world.copy()), reward, True, {}

    def step(self, action):
        # todo check self.player.ai == none at any time
        if not self.drafting:
            t = self.world.territory(action)
            if t is None:
                self.event("invalid territory choice %s", action)
                self.turn += 1
            if (t.owner is not None) or (t.owner is not self.player):
                self.event("initial invalid empty territory %s", t.name)
                self.turn += 1
            t.forces += 1
            self.remaining[self.player.name] -= 1
            if t.owner is None:
                t.owner = self.player
                self.event(("claim", self.player, t))
            else:
                self.event(("reinforce", self.player, t, 1))
            self.turn += 1
            empty = [x for x in self.world.territories if x.owner is None]
            result = self.initial_placement(empty)
            if result is not None:
                # observation, reward, done, info
                # todo reward
                return ("drafting", result), 0, False, {}
            else:
                # todo not sure
                self.play()
        # play
        elif not self.finished:
            assert sum(action.values()) == self.player.reinforcements
            for tt, ff in action.items():
                t = self.world.territory(tt)
                f = int(ff)
                if t is None:
                    self.event("reinforce invalid territory %s", tt)
                    continue
                if t.owner != self.player:
                    self.event("reinforce unowned territory %s", t.name)
                    continue
                if f < 0:
                    self.event("reinforce invalid count %s", f)
                    continue
                t.forces += f
                self.event(("reinforce", self.player, t, f))

            for src, target, attack, move in self.player.ai.attack():
                st = self.world.territory(src)
                tt = self.world.territory(target)
                if st is None:
                    self.event("attack invalid src %s", src)
                    continue
                if tt is None:
                    self.event("attack invalid target %s", target)
                    continue
                if st.owner != self.player:
                    self.event("attack unowned src %s", st.name)
                    continue
                if tt.owner == self.player:
                    self.event("attack owned target %s", tt.name)
                    continue
                if tt not in st.connect:
                    self.event("attack unconnected %s %s", st.name, tt.name)
                    continue
                initial_forces = (st.forces, tt.forces)
                opponent = tt.owner
                victory = self.combat(st, tt, attack, move)
                final_forces = (st.forces, tt.forces)
                self.event(("conquer" if victory else "defeat", self.player, opponent, st, tt, initial_forces,
                            final_forces))
            # todo freemove for player
            # freemove = self.player.ai.freemove()
            # if freemove:
            #     src, target, count = freemove
            #     st = self.world.territory(src)
            #     tt = self.world.territory(target)
            #     f = int(count)
            #     valid = True
            #     if st is None:
            #         self.event("freemove invalid src %s", src)
            #         valid = False
            #     if tt is None:
            #         self.event("freemove invalid target %s", target)
            #         valid = False
            #     if st.owner != self.player:
            #         self.event("freemove unowned src %s", st.name)
            #         valid = False
            #     if tt.owner != self.player:
            #         self.event("freemove unowned target %s", tt.name)
            #         valid = False
            #     if not 0 <= f < st.forces:
            #         self.event("freemove invalid count %s", f)
            #         valid = False
            #     if valid:
            #         st.forces -= count
            #         tt.forces += count
            #         self.event(("move", self.player, st, tt, count), territory=[st, tt], player=[self.player.name])
            self.live_players = len([p for p in self.players.values() if p.alive])
            self.turn += 1
            # other AIs play
            self.play()
            if not self.player.alive:
                return ("loss", self.world.copy()), -100, True, {}
            elif self.live_players == 1:
                self.finished = True
                winner = [p for p in self.players.values() if p.alive][0]
                self.event(("victory", winner))
                for p in self.players.values():
                    if p.ai is not None:
                        p.ai.end()
                reward = 100 if winner.ai is None else -100
                return ("win" if reward == 00 else "loss", self.world.copy()), reward, True, {}
            else:
                return ("combat", self.world.copy()), 0, False, {}

    def play(self):
        while self.live_players > 1 and self.player.ai is not None:
            if self.player.alive:
                choices = self.player.ai.reinforce(self.player.reinforcements)
                assert sum(choices.values()) == self.player.reinforcements
                for tt, ff in choices.items():
                    t = self.world.territory(tt)
                    f = int(ff)
                    if t is None:
                        self.event("reinforce invalid territory %s", tt)
                        continue
                    if t.owner != self.player:
                        self.event("reinforce unowned territory %s", t.name)
                        continue
                    if f < 0:
                        self.event("reinforce invalid count %s", f)
                        continue
                    t.forces += f
                    self.event(("reinforce", self.player, t, f))

                for src, target, attack, move in self.player.ai.attack():
                    st = self.world.territory(src)
                    tt = self.world.territory(target)
                    if st is None:
                        self.event("attack invalid src %s", src)
                        continue
                    if tt is None:
                        self.event("attack invalid target %s", target)
                        continue
                    if st.owner != self.player:
                        self.event("attack unowned src %s", st.name)
                        continue
                    if tt.owner == self.player:
                        self.event("attack owned target %s", tt.name)
                        continue
                    if tt not in st.connect:
                        self.event("attack unconnected %s %s", st.name, tt.name)
                        continue
                    initial_forces = (st.forces, tt.forces)
                    opponent = tt.owner
                    victory = self.combat(st, tt, attack, move)
                    final_forces = (st.forces, tt.forces)
                    self.event(("conquer" if victory else "defeat", self.player, opponent, st, tt, initial_forces,
                                final_forces))
                freemove = self.player.ai.freemove()
                if freemove:
                    src, target, count = freemove
                    st = self.world.territory(src)
                    tt = self.world.territory(target)
                    f = int(count)
                    valid = True
                    if st is None:
                        self.event("freemove invalid src %s", src)
                        valid = False
                    if tt is None:
                        self.event("freemove invalid target %s", target)
                        valid = False
                    if st.owner != self.player:
                        self.event("freemove unowned src %s", st.name)
                        valid = False
                    if tt.owner != self.player:
                        self.event("freemove unowned target %s", tt.name)
                        valid = False
                    if not 0 <= f < st.forces:
                        self.event("freemove invalid count %s", f)
                        valid = False
                    if valid:
                        st.forces -= count
                        tt.forces += count
                        self.event(("move", self.player, st, tt, count))
                self.live_players = len([p for p in self.players.values() if p.alive])
            self.turn += 1

    def combat(self, src, target, f_atk, f_move):
        n_atk = self.world.forces[src]
        n_def = self.world.forces[target]

        if f_atk is None:
            def f_atk(*_): return True
        if f_move is None:
            def f_move(x): return x - 1

        while n_atk > 1 and n_def > 0 and f_atk(n_atk, n_def):
            atk_dice = min(n_atk - 1, 3)
            atk_roll = sorted([random.randint(1, 6) for _ in range(atk_dice)], reverse=True)
            def_dice = min(n_def, 2)
            def_roll = sorted([random.randint(1, 6) for _ in range(def_dice)], reverse=True)

            for a, d in zip(atk_roll, def_roll):
                if a > d:
                    n_def -= 1
                else:
                    n_atk -= 1

        if n_def == 0:
            move = f_move(n_atk)
            min_move = min(n_atk - 1, 3)
            max_move = n_atk - 1
            if move < min_move:
                self.event("combat invalid move request %s (%s-%s)", move, min_move, max_move)
                move = min_move
            if move > max_move:
                self.event("combat invalid move request %s (%s-%s)", move, min_move, max_move)
                move = max_move
            self.world.forces[src] = n_atk - move
            self.world.forces[target] = move
            self.world.owners[target] = self.world.owners[src]
            return True
        else:
            self.world.forces[src] = n_atk
            self.world.forces[target] = n_def
            return False

    def initial_placement(self, empty):
        while empty:
            if self.player.ai is not None:
                choice = self.player.ai.initial_placement(empty)
                if choice not in self.world.owners.keys():
                    self.event("invalid territory choice %s", choice)
                    self.turn += 1
                    continue
                if choice not in empty:
                    self.event("initial invalid empty territory %s", choice)
                    self.turn += 1
                    continue
                self.world.forces[choice] += 1
                self.world.owners[choice] = self.player
                self.remaining[self.player.name] -= 1
                empty.remove(choice)
                self.event(("claim", self.player, choice))
                self.turn += 1
            else:
                return self.world.copy()
        while sum(self.remaining.values()) > 0:
            if self.remaining[self.player.name] > 0:
                if self.player.ai is not None:
                    choice = self.player.ai.initial_placement(None)
                    if choice not in self.world.owners.keys():
                        self.event("invalid territory choice")
                        self.turn += 1
                        continue
                    if self.world.owners[choice] is not self.player:
                        self.event("initial invalid empty territory")
                        self.turn += 1
                        continue
                    self.world.forces[choice] += 1
                    self.remaining[self.player.name] -= 1
                    self.event(("reinforce", self.player, choice, 1))
                    self.turn += 1
                else:
                    return self.world.copy()
            else:
                self.turn += 1
        self.drafting = True
        return None
