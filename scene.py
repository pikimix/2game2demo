"""A scene which controls the entity state
"""
import logging
import random
import pygame as pg
from pygame.sprite import Group, GroupSingle, LayeredDirty
from entity import Enemy, Player

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)
class Scene:
    """A scene (or "level") of the game
    """
    def __init__(self):
        """Create a new scene
        """
        sprite =  {
            'file':'assets/sprites/player.png',
            'width': 32,
            'height': 32,
            'frames': 4
        }
        psprite = Player((128,128), sprite)
        self.player: GroupSingle[Player] = GroupSingle(psprite)
        self.all_sprites: LayeredDirty[Enemy|Player] = LayeredDirty()
        self.enemies: Group[Enemy] = Group()
        for _ in range(4):
            loc = (random.randint(0,1200), random.randint(0,700))
            enemy = Enemy(loc, sprite)
            enemy.move_towards(pg.Vector2(self.player.sprites()[0].rect.center))
            self.enemies.add(enemy)
        for enemy in self.enemies:
            enemy.tint('Red')
        self.all_sprites.add(self.enemies, layer=1)
        self.all_sprites.add(self.player, layer=2)

    def update(self, bounds: pg.Rect):
        """Update the current scene

        Parameters
        ----------
        bounds : pg.Rect
            The bounds to keep the player within - This may move in future.
        """
        for p in self.player:
            p.update(bounds)

    def draw(self, screen: pg.Surface):
        """Draw the current scene to the provided screen

        Parameters
        ----------
        screen : pg.Surface
            SCreen or surface to draw the scene too.
        """
        self.all_sprites.draw(screen)
