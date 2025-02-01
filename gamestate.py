"""Class that holds the current gamestate
"""
from __future__ import annotations # To make type hinting work when using certain classes
import logging
from pygame.sprite import Group
from entity import Enemy, Entity, Ghost, Player

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

    @staticmethod
    def serialize() -> dict:
        """Serialize the current gamestate, or at least what we want to transfer to another game

        Currently serializes:
            Gamestate.player
        """
        return Gamestate.player.serialize()

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
            if ruuid == 'offset' or ruuid == str(Gamestate.player.uuid):
                continue
            uuid_found = False
            for sprite in Gamestate.ghosts:
                if str(sprite.uuid) == ruuid:
                    uuid_found = True
                    sprite.net_update(values)
            if not uuid_found:
                g = Ghost((0,0), Gamestate.sprite, euuid=ruuid)
                g.net_update(values)
                Gamestate.ghosts.add(g)
                # yield g
