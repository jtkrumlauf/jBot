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
        self.iteration = iteration

        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilator()
        await self.expand()
        await self.offensive_force_buildings()
        await self.build_offensive_force()
        await self.attack()

    async def build_workers(self):
        if len(self.units(NEXUS)) * 16 > len(self.units(PROBE)):
            if len(self.units(PROBE)) < self.MAX_WORKERS:
                for nexus in self.units(NEXUS).ready.noqueue:  # nexus must be ready and not producing anything then:
                    if self.can_afford(PROBE):  # if can afford a PROBE...
                        await self.do(nexus.train(PROBE))  # train the PROBE

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):  # if pop. remaining is < x and plyon not currently being built
            nexuses = self.units(NEXUS).ready  # a nexus tha already exists
            if nexuses.exists:
                if self.can_afford(PYLON):  # if can afford the pylon
                    await self.build(PYLON, near=nexuses.first)  # builds pylon close to nexus

    async def build_assimilator(self):
        for nexus in self.units(NEXUS).ready:  # for nexuses that are ready
            vaspenes = self.state.vespene_geyser.closer_than(15.0, nexus)  # looking for geysers that are closer than x units
            for vaspene in vaspenes:
                if not self.can_afford(ASSIMILATOR):  # if cant afford
                    break
                worker = self.select_build_worker(vaspene.position)  # finds worker close to the vaspene deposit
                if worker is None:  # if there is no worker near deposit
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:  # if not assimilator that exists near vaspene
                    await self.do(worker.build(ASSIMILATOR, vaspene))  # builds assimilator on top of found vaspene deposit

    async def expand(self):
        if self.units(NEXUS).amount < (self.iteration / self.ITERATIONS_PER_MINUTE) and self.can_afford(NEXUS):  # if number of nexuses is < x and can afford...
            await self.expand_now()  # goes and expands to another resource area

    async def offensive_force_buildings(self):
        if self.units(PYLON).ready.exists:  # as long as some pylon exists
            pylon = self.units(PYLON).ready.random  # picks random pylon

            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):  # if have gateway and is ready and exists
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):  # if can afford CC and not already pending
                    await self.build(CYBERNETICSCORE, near=pylon)  # builds cybernetics core near the random pylon

            elif len(self.units(GATEWAY)) < ((self.iteration / self.ITERATIONS_PER_MINUTE)/2):
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):  # if can afford gateway and not pending
                    await self.build(GATEWAY, near=pylon)  # builds gateway near random pylon from above

            if self.units(CYBERNETICSCORE).ready.exists:  # if CC is ready and exists...
                if len(self.units(STARGATE)) < ((self.iteration / self.ITERATIONS_PER_MINUTE)/2):
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):  # if can afford a Stargate and not already pending
                        await self.build(STARGATE, near=pylon)

    async def build_offensive_force(self):
        for gw in self.units(GATEWAY).ready.noqueue:  # for each gateway in ready gateways
            if self.can_afford(STALKER) and self.supply_left > 0:  # if can afford stalker and supply left > 0

                if self.can_afford(STALKER) and self.supply_left > 0:
                    await self.do(gw.train(STALKER))  # trains stalker

        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                await self.do(sg.train(VOIDRAY))

    def find_target(self, state):
        if len(self.known_enemy_units) > 0: # if know about some enemy unit
            return random.choice(self.known_enemy_units)  # attack that target
        elif len(self.known_enemy_structures) > 0:  # if cant find any units and only structures
            return random.choice(self.known_enemy_structures)  # attack a random structure
        else:
            return self.enemy_start_locations[0]  # if don't know about anything, go seek them out at start loc.

    async def attack(self):
        # TO ADD - CLUMP OF 3 BEFORE THEY GO AND ATTACK

        # {UNIT: [n to search for a fight, n to defend]
        aggressive_units = {STALKER: [15, 3],
                           VOIDRAY: [8, 3]}

        for UNIT in aggressive_units:
            if self.units(UNIT).amount > aggressive_units[UNIT][0] and self.units(UNIT).amount > aggressive_units:
                for s in self.units(UNIT).idle:
                    await self.do(s.attack(self.find_target(self.state)))

            if self.units(UNIT).amount > aggressive_units[UNIT][1]:
                if len(self.known_enemy_units) > 0:
                    for s in self.units(UNIT.idle):
                        await self.do(s.attack(random.choice(self.known_enemy_units)))


# Runs the game. can specify the map, who is playing, and game speed
run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, JustinBot()),
    Computer(Race.Terran, Difficulty.Medium)
    ], realtime=False)