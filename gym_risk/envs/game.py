from gym_risk.envs.display import Display
from gym_risk.envs.player import Player
from gym_risk.envs.territory import World
from gym_risk.envs.world import CONNECT, AREAS, MAP, KEY
import logging
import random
from copy import deepcopy

LOG = logging.getLogger("pyrisk")
LOG.setLevel(logging.DEBUG)
logging.basicConfig(filename="pyrisk.log", filemode="w")


class Game(object):
    """
    This class represents an individual game, and contains the main game logic.
    """
    defaults = {
        "curses": True,  # whether to use ncurses for map display
        "color": True,  # whether to use color with ncurses
        "delay": 0.1,  # seconds to sleep after each (ncurses) display update
        "connect": CONNECT,  # the territory connection graph (see world.py)
        "areas": AREAS,  # the territory->continent mapping, and values
        "cmap": MAP,  # the ASCII art map to use
        "ckey": KEY,  # the territory->char mapping key for the map
        "screen": None,  # a curses.window (for use with the curses.wrapper function)
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
        self.world.load(self.options['areas'], self.options['connect'])

        self.players = {}
        self.live_players = 0

        self.turn = 0
        self.turn_order = []

        self.remaining = {}
        self.drafting = False
        self.finished = False

        self.display = Display()

    def add_player(self, name, ai_class):
        assert name not in self.players
        assert len(self.players) <= 5
        player = Player(name, self, ai_class)
        self.players[name] = player

    @property
    def player(self):
        """Property that returns the correct player object for this turn."""
        return self.players[self.turn_order[self.turn % len(self.players)]]

    def aiwarn(self, *args):
        """Generate a warning message when an AI player tries to break the rules."""
        logging.getLogger("pyrisk.player.%s" % self.player.ai.__class__.__name__).warning(*args)

    def event(self, msg, territory=None, player=None):
        """
        Record any game action.
        `msg` is a tuple describing what happened.
        `territory` is a list of territory objects to be highlighted, if any
        `player` is a list of player names to be highlighted, if any
        
        Calling this method triggers the display to be updated, and any AI
        players that have implemented event() to be notified.
        """

        self.display.update(msg, territory=territory, player=player)

        LOG.info([str(m) for m in msg])
        for p in self.players.values():
            if p.ai is not None:
                p.ai.event(msg)

    def init(self):
        assert 2 <= len(self.players) <= 6
        self.add_player("Player", None)
        self.live_players = len(self.players)
        self.turn_order = list(self.players)
        random.shuffle(self.turn_order)
        for i, name in enumerate(self.turn_order):
            self.players[name].color = i + 1
            self.players[name].ord = ord('\/-|+*'[i])
            if self.players[name].ai is not None:
                self.players[name].ai.start()
        self.event(("start",))
        empty = list(self.world.territories.values())
        available = 35 - 2 * len(self.players)
        self.remaining = {p: available for p in self.players}
        if self.options['deal']:
            random.shuffle(empty)
            while empty:
                t = empty.pop()
                t.forces += 1
                self.remaining[self.player.name] -= 1
                t.owner = self.player
                self.event(("deal", self.player, t), territory=[t], player=[self.player.name])
                self.turn += 1
            while sum(self.remaining.values()) > 0:
                if self.remaining[self.player.name] > 0:
                    choice = self.player.ai.initial_placement(None, self.remaining[self.player.name])
                    t = self.world.territory(choice)
                    if t is None:
                        self.aiwarn("initial invalid territory %s", choice)
                        self.turn += 1
                        continue
                    if t.owner != self.player:
                        self.aiwarn("initial unowned territory %s", t.name)
                        self.turn += 1
                        continue
                    t.forces += 1
                    self.remaining[self.player.name] -= 1
                    self.event(("reinforce", self.player, t, 1), territory=[t], player=[self.player.name])
                    self.turn += 1
                    self.play()
                    self.drafting = True
                    # todo which data structure
                    return "combat", list(self.world.territories.values())
        else:
            return self.initial_placement(empty)

    # reward = 100*(((win/total)-(1/nb_players))/(1/nb_players))
    def step_drafting(self, action):
        if not self.drafting:
            t = self.world.territory(action)
            if t is None:
                self.aiwarn("invalid territory choice %s", action)
                self.turn += 1
            if (t.owner is not None) or (t.owner is not self.player):
                self.aiwarn("initial invalid empty territory %s", t.name)
                self.turn += 1
            t.forces += 1
            self.remaining[self.player.name] -= 1
            if t.owner is None:
                t.owner = self.player
                self.event(("claim", self.player, t), territory=[t], player=[self.player.name])
            else:
                self.event(("reinforce", self.player, t, 1), territory=[t], player=[self.player.name])
            self.turn += 1
            empty = [x for x in self.world.territories if x.owner is None]
            result = self.initial_placement(empty)
            if result is not None:
                # observation, reward, done, info
                # todo reward
                return ("drafting", result), 0, False, {}
            else:
                NB_PLAYOUTS = 100
                victories = 0
                world_backup = deepcopy(self.world)
                from gym_risk.envs.ai.random import RandomAI
                self.players["Player"].ai = RandomAI(self.players["Player"], self, self.world)
                self.players["Player"].ai.start()
                for i in range(NB_PLAYOUTS):
                    self.world = deepcopy(world_backup)
                    while live_players > 1:
                        if self.player.alive:
                            choices = self.player.ai.reinforce(self.player.reinforcements)
                            assert sum(choices.values()) == self.player.reinforcements
                            for tt, ff in choices.items():
                                t = self.world.territory(tt)
                                f = int(ff)
                                if t is None:
                                    self.aiwarn("reinforce invalid territory %s", tt)
                                    continue
                                if t.owner != self.player:
                                    self.aiwarn("reinforce unowned territory %s", t.name)
                                    continue
                                if f < 0:
                                    self.aiwarn("reinforce invalid count %s", f)
                                    continue
                                t.forces += f
                                self.event(("reinforce", self.player, t, f), territory=[t], player=[self.player.name])

                            for src, target, attack, move in self.player.ai.attack():
                                st = self.world.territory(src)
                                tt = self.world.territory(target)
                                if st is None:
                                    self.aiwarn("attack invalid src %s", src)
                                    continue
                                if tt is None:
                                    self.aiwarn("attack invalid target %s", target)
                                    continue
                                if st.owner != self.player:
                                    self.aiwarn("attack unowned src %s", st.name)
                                    continue
                                if tt.owner == self.player:
                                    self.aiwarn("attack owned target %s", tt.name)
                                    continue
                                if tt not in st.connect:
                                    self.aiwarn("attack unconnected %s %s", st.name, tt.name)
                                    continue
                                initial_forces = (st.forces, tt.forces)
                                opponent = tt.owner
                                victory = self.combat(st, tt, attack, move)
                                final_forces = (st.forces, tt.forces)
                                self.event(("conquer" if victory else "defeat", self.player, opponent, st, tt,
                                            initial_forces, final_forces), territory=[st, tt],
                                           player=[self.player.name, tt.owner.name])
                            freemove = self.player.ai.freemove()
                            if freemove:
                                src, target, count = freemove
                                st = self.world.territory(src)
                                tt = self.world.territory(target)
                                f = int(count)
                                valid = True
                                if st is None:
                                    self.aiwarn("freemove invalid src %s", src)
                                    valid = False
                                if tt is None:
                                    self.aiwarn("freemove invalid target %s", target)
                                    valid = False
                                if st.owner != self.player:
                                    self.aiwarn("freemove unowned src %s", st.name)
                                    valid = False
                                if tt.owner != self.player:
                                    self.aiwarn("freemove unowned target %s", tt.name)
                                    valid = False
                                if not 0 <= f < st.forces:
                                    self.aiwarn("freemove invalid count %s", f)
                                    valid = False
                                if valid:
                                    st.forces -= count
                                    tt.forces += count
                                    self.event(("move", self.player, st, tt, count), territory=[st, tt],
                                               player=[self.player.name])
                            live_players = len([p for p in self.players.values() if p.alive])
                        self.turn += 1
                    winner = [p for p in self.players.values() if p.alive][0]
                    self.event(("victory", winner), player=[self.player.name])
                    if winner is self.players["Player"]:
                        victories += 1
                for p in self.players.values():
                    p.ai.end()
                reward = 100 * (((victories / NB_PLAYOUTS) - (1 / len(self.players))) / (1 / len(self.players)))
                return ("win", list(self.world.territories.values)), reward, True, {}

    def step(self, action):
        # todo check self.player.ai == none at any time
        if not self.drafting:
            t = self.world.territory(action)
            if t is None:
                self.aiwarn("invalid territory choice %s", action)
                self.turn += 1
            if (t.owner is not None) or (t.owner is not self.player):
                self.aiwarn("initial invalid empty territory %s", t.name)
                self.turn += 1
            t.forces += 1
            self.remaining[self.player.name] -= 1
            if t.owner is None:
                t.owner = self.player
                self.event(("claim", self.player, t), territory=[t], player=[self.player.name])
            else:
                self.event(("reinforce", self.player, t, 1), territory=[t], player=[self.player.name])
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
            # todo myactions
            assert sum(action.values()) == self.player.reinforcements
            for tt, ff in action.items():
                t = self.world.territory(tt)
                f = int(ff)
                if t is None:
                    self.aiwarn("reinforce invalid territory %s", tt)
                    continue
                if t.owner != self.player:
                    self.aiwarn("reinforce unowned territory %s", t.name)
                    continue
                if f < 0:
                    self.aiwarn("reinforce invalid count %s", f)
                    continue
                t.forces += f
                self.event(("reinforce", self.player, t, f), territory=[t], player=[self.player.name])

            for src, target, attack, move in self.player.ai.attack():
                st = self.world.territory(src)
                tt = self.world.territory(target)
                if st is None:
                    self.aiwarn("attack invalid src %s", src)
                    continue
                if tt is None:
                    self.aiwarn("attack invalid target %s", target)
                    continue
                if st.owner != self.player:
                    self.aiwarn("attack unowned src %s", st.name)
                    continue
                if tt.owner == self.player:
                    self.aiwarn("attack owned target %s", tt.name)
                    continue
                if tt not in st.connect:
                    self.aiwarn("attack unconnected %s %s", st.name, tt.name)
                    continue
                initial_forces = (st.forces, tt.forces)
                opponent = tt.owner
                victory = self.combat(st, tt, attack, move)
                final_forces = (st.forces, tt.forces)
                self.event(("conquer" if victory else "defeat", self.player, opponent, st, tt, initial_forces,
                            final_forces), territory=[st, tt], player=[self.player.name, tt.owner.name])
            # todo freemove for player
            # freemove = self.player.ai.freemove()
            # if freemove:
            #     src, target, count = freemove
            #     st = self.world.territory(src)
            #     tt = self.world.territory(target)
            #     f = int(count)
            #     valid = True
            #     if st is None:
            #         self.aiwarn("freemove invalid src %s", src)
            #         valid = False
            #     if tt is None:
            #         self.aiwarn("freemove invalid target %s", target)
            #         valid = False
            #     if st.owner != self.player:
            #         self.aiwarn("freemove unowned src %s", st.name)
            #         valid = False
            #     if tt.owner != self.player:
            #         self.aiwarn("freemove unowned target %s", tt.name)
            #         valid = False
            #     if not 0 <= f < st.forces:
            #         self.aiwarn("freemove invalid count %s", f)
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
                return ("loss", list(self.world.territories.values())), -100, True, {}
            elif self.live_players == 1:
                self.finished = True
                winner = [p for p in self.players.values() if p.alive][0]
                self.event(("victory", winner), player=[self.player.name])
                for p in self.players.values():
                    if p.ai is not None:
                        p.ai.end()
                reward = 100 if winner.ai is None else -100
                return ("win" if reward == 00 else "loss", list(self.world.territories.values())), reward, True, {}
            else:
                return ("combat", list(self.world.territories.values())), 0, False, {}

    def play(self):
        while self.live_players > 1 and self.player.ai is not None:
            if self.player.alive:
                choices = self.player.ai.reinforce(self.player.reinforcements)
                assert sum(choices.values()) == self.player.reinforcements
                for tt, ff in choices.items():
                    t = self.world.territory(tt)
                    f = int(ff)
                    if t is None:
                        self.aiwarn("reinforce invalid territory %s", tt)
                        continue
                    if t.owner != self.player:
                        self.aiwarn("reinforce unowned territory %s", t.name)
                        continue
                    if f < 0:
                        self.aiwarn("reinforce invalid count %s", f)
                        continue
                    t.forces += f
                    self.event(("reinforce", self.player, t, f), territory=[t], player=[self.player.name])

                for src, target, attack, move in self.player.ai.attack():
                    st = self.world.territory(src)
                    tt = self.world.territory(target)
                    if st is None:
                        self.aiwarn("attack invalid src %s", src)
                        continue
                    if tt is None:
                        self.aiwarn("attack invalid target %s", target)
                        continue
                    if st.owner != self.player:
                        self.aiwarn("attack unowned src %s", st.name)
                        continue
                    if tt.owner == self.player:
                        self.aiwarn("attack owned target %s", tt.name)
                        continue
                    if tt not in st.connect:
                        self.aiwarn("attack unconnected %s %s", st.name, tt.name)
                        continue
                    initial_forces = (st.forces, tt.forces)
                    opponent = tt.owner
                    victory = self.combat(st, tt, attack, move)
                    final_forces = (st.forces, tt.forces)
                    self.event(("conquer" if victory else "defeat", self.player, opponent, st, tt, initial_forces,
                                final_forces), territory=[st, tt], player=[self.player.name, tt.owner.name])
                freemove = self.player.ai.freemove()
                if freemove:
                    src, target, count = freemove
                    st = self.world.territory(src)
                    tt = self.world.territory(target)
                    f = int(count)
                    valid = True
                    if st is None:
                        self.aiwarn("freemove invalid src %s", src)
                        valid = False
                    if tt is None:
                        self.aiwarn("freemove invalid target %s", target)
                        valid = False
                    if st.owner != self.player:
                        self.aiwarn("freemove unowned src %s", st.name)
                        valid = False
                    if tt.owner != self.player:
                        self.aiwarn("freemove unowned target %s", tt.name)
                        valid = False
                    if not 0 <= f < st.forces:
                        self.aiwarn("freemove invalid count %s", f)
                        valid = False
                    if valid:
                        st.forces -= count
                        tt.forces += count
                        self.event(("move", self.player, st, tt, count), territory=[st, tt], player=[self.player.name])
                self.live_players = len([p for p in self.players.values() if p.alive])
            self.turn += 1

    def combat(self, src, target, f_atk, f_move):
        n_atk = src.forces
        n_def = target.forces

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
                self.aiwarn("combat invalid move request %s (%s-%s)", move, min_move, max_move)
                move = min_move
            if move > max_move:
                self.aiwarn("combat invalid move request %s (%s-%s)", move, min_move, max_move)
                move = max_move
            src.forces = n_atk - move
            target.forces = move
            target.owner = src.owner
            return True
        else:
            src.forces = n_atk
            target.forces = n_def
            return False

    def initial_placement(self, empty):
        while empty:
            if self.player.ai is not None:
                choice = self.player.ai.initial_placement(empty)
                t = self.world.territory(choice)
                if t is None:
                    self.aiwarn("invalid territory choice %s", choice)
                    self.turn += 1
                    continue
                if t not in empty:
                    self.aiwarn("initial invalid empty territory %s", t.name)
                    self.turn += 1
                    continue
                t.forces += 1
                t.owner = self.player
                self.remaining[self.player.name] -= 1
                empty.remove(t)
                self.event(("claim", self.player, t), territory=[t], player=[self.player.name])
                self.turn += 1
            else:
                return list(self.world.territories.values())
        while sum(self.remaining.values()) > 0:
            if self.remaining[self.player.name] > 0:
                if self.player.ai is not None:
                    choice = self.player.ai.initial_placement(None)
                    t = self.world.territory(choice)
                    if t is None:
                        self.aiwarn("initial invalid territory %s", choice)
                        self.turn += 1
                        continue
                    if t.owner != self.player:
                        self.aiwarn("initial unowned territory %s", t.name)
                        self.turn += 1
                        continue
                    t.forces += 1
                    self.remaining[self.player.name] -= 1
                    self.event(("reinforce", self.player, t, 1), territory=[t], player=[self.player.name])
                    self.turn += 1
                else:
                    return list(self.world.territories.values())

        self.drafting = True
        return None
