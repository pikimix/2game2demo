"""Class that holds the current gamestate
"""
from __future__ import annotations # To make type hinting work when using certain classes
import logging
import time
from pygame.sprite import Group
import pygame as pg
from app import App
from entity import Enemy, Entity, Ghost, Player
from particle import Explosion, Particle

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class Gamestate:
    sprite =  {
        'file':'assets/sprites/player.png',
        'width': 32,
        'height': 32,
        'frames': 4
    }
    player: Player = None
    enemies: Group[Enemy] = Group()
    ghosts: Group[Ghost] = Group()
    score: dict[str,int] = {}
    my_top_score = 0
    super_attacks: dict[str,list[Explosion|Particle]] = {}
    new_supers: list[Explosion|Particle] = []

    @staticmethod
    def serialize() -> dict:
        """Serialize the current gamestate, or at least what we want to transfer to another game

        Currently serializes:
            Gamestate.player
            Gamestate.score[PlayerName]
        """
        gamestate = Gamestate.player.serialize()
        gamestate['name'] = App.config('name')
        gamestate['score'] = Gamestate.my_top_score
        supers = [s.serialize() for s in Gamestate.new_supers]
        gamestate['supers'] = supers
        Gamestate.new_supers = []
        return gamestate

    @staticmethod
    def update_net(update: dict):
        """Update current gamestate based on update provided from the network

        Parameters
        ----------
        update : dict
            Dictionary of the gamestate

        Yields
        ------
        Ghost
            Any new ghosts that need to be added ot the scenes sprite list to be drawn
        """
        logger.debug('Scene.update: processing %s network updates', len(update))
        for ruuid, values in update.items():
            logger.debug(values)
            if ruuid == str(Gamestate.player.uuid):
                continue
            elif ruuid == 'offset':
                Gamestate.offset = values
                continue
            uuid_found = False
            if 'score' in values:
                Gamestate.score[values['name']] = values['score']
                logger.debug(Gamestate.score)
            for sprite in Gamestate.ghosts:
                if str(sprite.uuid) == ruuid:
                    uuid_found = True
                    sprite.net_update(values)
            if 'supers' in values:
                for s in values['supers']:
                    r = pg.Rect(0,0,10,10)
                    r.center = s['position']
                    v = pg.Vector2(s['velocity'])
                    c = pg.Color(s['color'])
                    p = None
                    if s['type'] == 'particle':
                        p = Particle(r, v, c, s['lifetime'], s['spawn_time'])
                    elif s['type'] == 'explosion':
                        p = Explosion(r, v, c, s['lifetime'], s['spawn_time'], s['windup'],
                                        s['radius'], s['explosion_speed'], s['decay'])
                    else: #IF we dont have a type, just create a particle
                        p = Particle(r, v, c, s['lifetime'], s['spawn_time'])
                    p.update(time.time() - s['spawn_time'])
                    Gamestate.super_attacks[ruuid].append(p)
            if not uuid_found:
                g = Ghost((0,0), Gamestate.sprite, euuid=ruuid)
                g.net_update(values)
                Gamestate.ghosts.add(g)
                Gamestate.super_attacks[ruuid] = []
                # yield g
