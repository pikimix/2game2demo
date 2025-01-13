"""A scene which controls the entity state
"""
import logging
import pygame as pg
import entity

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
        psprite = entity.Player((128,128), sprite)
        self.player = pg.sprite.GroupSingle(psprite)
        self.all_sprites = pg.sprite.LayeredDirty()
        self.all_sprites.add(self.player, layer=2)
        self.enemies = pg.sprite.Group()
        for e in range(4):
            self.enemies.add(entity.Entity((128*e,128), sprite))
        for enemy in self.enemies:
            enemy.tint('Red')
        self.all_sprites.add(self.enemies, layer=1)

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
