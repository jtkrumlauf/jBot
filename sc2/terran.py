import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *

# ** See Notes in: README.txt **


class JustinBot(sc2.BotAI):  # see bot_ai.py to see inherited methods
    def __init__(self):
        self.ITERATIONS_PER_MINUTE = 165
        self.MAX_WORKERS = 65

    async def on_step(self, iteration):  # first thing game does on startup
        if iteration == 0:
            await self.chat_send("(JustinBot Wishes the Opponent Good Luck)")
        self.iteration = iteration

        await self.distribute_workers()
        await self.build_workers()
        await self.build_supplydepot()
        await self.build_assimilator()
        await self.expand()
        await self.offensive_force_buildings()
        await self.build_offensive_force()
        await self.attack()

    async def build_workers(self):
        if len(self.units(COMMANDCENTER)) * 16 > len(self.units(SCV)):
            if len(self.units(SCV)) < self.MAX_WORKERS:
                for nexus in self.units(COMMANDCENTER).ready.noqueue:  # COMMANDCENTER must be ready and not producing anything then:
                    if self.can_afford(SCV):  # if can afford a SCV...
                        await self.do(nexus.train(SCV))  # train the PROBE

    async def build_supplydepot(self):
        if self.supply_left < 5 and not self.already_pending(SUPPLYDEPOT):  # if pop. remaining is < x and SD not currently being built
            nexuses = self.units(COMMANDCENTER).ready  # a nexus tha already exists
            if nexuses.exists:
                if self.can_afford(SUPPLYDEPOT):  # if can afford the pylon
                    await self.build(SUPPLYDEPOT, near=nexuses.first)  # builds pylon close to nexus

    async def build_assimilator(self):
        for nexus in self.units(COMMANDCENTER).ready:  # for nexuses that are ready
            vaspenes = self.state.vespene_geyser.closer_than(15.0, nexus)  # looking for geysers that are closer than x units
            for vaspene in vaspenes:
                if not self.can_afford(REFINERY):  # if cant afford
                    break
                worker = self.select_build_worker(vaspene.position)  # finds worker close to the vaspene deposit
                if worker is None:  # if there is no worker near deposit
                    break
                if not self.units(REFINERY).closer_than(1.0, vaspene).exists:  # if not assimilator that exists near vaspene
                    await self.do(worker.build(REFINERY, vaspene))  # builds assimilator on top of found vaspene deposit

    async def expand(self):
        if self.units(COMMANDCENTER).amount < (self.iteration / self.ITERATIONS_PER_MINUTE) and self.can_afford(COMMANDCENTER):  # if number of nexuses is < x and can afford...
            await self.expand_now()  # goes and expands to another resource area

    async def offensive_force_buildings(self):
        # PATH OF PROGRESSION:
        # barracks --> factory --> starport
        #
        # ADD LOGIC TO: see what buildings can be upgrades...based on iteration/min determine whether or not to upgrade
        if self.units(SUPPLYDEPOT).ready.exists:  # as long as some pylon exists
            building_loc = self.units(SUPPLYDEPOT).ready.random  # picks random pylon

            # BUILD FACTORY/FACTORY TECH LAB
            if self.units(BARRACKS).ready.exists and not self.units(FACTORY):  # if have BARRACKS and is ready and exists
                if self.can_afford(FACTORY) and not self.already_pending(FACTORY):  # if can afford FACTORY and not already pending
                    await self.build(FACTORY, near=building_loc)  # builds FACTORY near the random SUPPLYDEPOT
                    # builds only ONE factory...can change in future
            if self.units(FACTORY).ready.exists and self.can_afford(FACTORYTECHLAB):  # checks if factory already exists and if can afford tech lab
                for ready_factories in self.units(FACTORY).ready:  # for each ready factory in factories
                    await self.do(ready_factories.build(FACTORYTECHLAB))  # build a tech lab on a given factory

            # BUILD BARRACKS/BARRACKS TECH LAB
            if len(self.units(BARRACKS)) < ((self.iteration / self.ITERATIONS_PER_MINUTE)/2):  # ~1 every minute
                if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):  # if can afford BARRACKS and not pending
                    await self.build(BARRACKS, near=building_loc)  # builds BARRACKS near random SUPPLYDEPOT from above
            if self.units(BARRACKS).ready.exists and self.can_afford(BARRACKSTECHLAB):  # checks if barracks exists and if can afford tech lab
                for ready_barracks in self.units(BARRACKS).ready:  # for each ready barracks in barracks list
                    await self.do(ready_barracks.build(BARRACKSTECHLAB))  # build a tech lab for the given barracks

            # if self.units(FACTORY).ready.exists:  # if FACTORY is ready and exists...
            #     if len(self.units(STARPORT)) < ((self.iteration / self.ITERATIONS_PER_MINUTE)/2):
            #         if self.can_afford(STARPORT) and not self.already_pending(STARPORT):  # if can afford a STARPORT and not already pending
            #             await self.build(STARPORT, near=building_loc)

    async def build_offensive_force(self):
        # BUILD BARRACKS UNITS
        for barr in self.units(BARRACKS).ready.noqueue:  # for each BARRACK in ready BARRACKS
            if self.units(BARRACKSTECHLAB).exists and self.can_afford(MARAUDER) and self.supply_left > 0:  # HIGHEST priority given to MARAUDERS over rest in scope of for-loop
                await self.do(barr.train(MARAUDER))  # train MARAUDER
            if self.can_afford(MARINE) and self.supply_left > 0:  # if can afford MARINE but not MARAUDER and supply left > 0
                await self.do(barr.train(MARINE))  # trains MARINE

        # BUILD FACTORY UNITS
        for fact in self.units(FACTORY).ready.noqueue:  # for each FACTORY in ready FACTORIES
            if self.units(FACTORYTECHLAB).exists and self.can_afford(SIEGETANK) and self.supply_left > 0:  # HIGHEST priority given to SIEGETANK over rest in scope of for-loop
                await self.do(fact.train(SIEGETANK))  # trains SIEGETANK
            if self.can_afford(HELLION) and self.supply_left > 0:  # if can afford HELLION but not SIEGETANK
                await self.do(fact.train(HELLION))  # trains HELLION

        # for st_pt in self.units(STARPORT).ready.noqueue:
        #     if self.can_afford(VIKING) and self.supply_left > 0:
        #         await self.do(st_pt.train(VIKING))

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:  # if know about some enemy unit
            return random.choice(self.known_enemy_units)  # attack that target
        elif len(self.known_enemy_structures) > 0:  # if cant find any units and only structures
            return random.choice(self.known_enemy_structures)  # attack a random structure
        else:
            return self.enemy_start_locations[0]  # if don't know about anything, go seek them out at start loc.

    async def attack(self):
        # TO ADD - CLUMP IN GROUP BEFORE THEY GO AND ATTACK
        #
        # {UNIT: [n to search for a fight, n to defend]
        aggressive_units = {MARINE: [15, 4],
                            MARAUDER: [7, 3],
                            HELLION: [7, 2],
                            SIEGETANK: [4, 1]}

        for UNIT in aggressive_units:
            if self.units(UNIT).amount > aggressive_units[UNIT][0] and self.units(UNIT).amount > aggressive_units[UNIT][1]:
                for s in self.units(UNIT).idle:
                    await self.do(s.attack(self.find_target(self.state)))

            elif self.units(UNIT).amount > aggressive_units[UNIT][1]:
                if len(self.known_enemy_units) > 0:
                    for s in self.units(UNIT).idle:
                        await self.do(s.attack(random.choice(self.known_enemy_units)))


# Runs the game. can specify the map, who is playing, and game speed
run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Terran, JustinBot()),
    Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=False)
