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
    def __init__(self, bounds: pg.Rect):
        """Create a new scene
        """
        self.bounds = bounds
        sprite =  {
            'file':'assets/sprites/player.png',
            'width': 32,
            'height': 32,
            'frames': 4
        }
        psprite = Player(bounds.center, sprite)
        self.player: GroupSingle[Player] = GroupSingle(psprite)
        self.all_sprites: LayeredDirty[Enemy|Player] = LayeredDirty()
        self.enemies: Group[Enemy] = Group()
        for _ in range(10):
            enemy = Enemy(self.spawn_outside(), sprite)
            enemy.move_towards(pg.Vector2(self.player.sprites()[0].rect.center))
            self.enemies.add(enemy)
        for enemy in self.enemies:
            enemy.tint('Red')
        self.all_sprites.add(self.enemies, layer=1)
        self.all_sprites.add(self.player, layer=2)
        self.dead_sprites: Group = Group()

    def spawn_outside(self) -> tuple:
        """Provide spawn point thats outside the playable bounds.

        Returns
        -------
        tuple
            tuple representing a location to spawn thats outside the space of the screen
        """
        direction = random.choice(['top', 'left', 'right', 'bottom'])
        # logger.debug('Scene:spawn_outside: direction=%s', direction)
        offset = [random.randint(50,100), random.randint(0,100)]

        if direction == 'top':
            offset[0] = random.randint(0,self.bounds.width)
            offset[1] = -offset[1]
        if direction == 'left':
            offset[0] = -offset[0]
            offset[1] = random.randint(0,self.bounds.height)
        if direction == 'right':
            offset[0] += self.bounds.width
            offset[1] = random.randint(0,self.bounds.height)
        if direction == 'bottom':
            offset[0] = random.randint(0,self.bounds.width)
            offset[1] += self.bounds.height
        return tuple(offset)

    def update(self, dt:float):
        """Update the current scene

        Parameters
        ----------
        dt : float
            deltatime - time since last update
        """
        self.player.update(self.bounds, dt)


        for e in self.enemies:
            e.update(dt)
            if not self.bounds.contains(e.rect):
                if e.has_been_onscreen:
                    e.kill()
                    self.dead_sprites.add(e)
            elif not e.has_been_onscreen:
                e.has_been_onscreen = True

        # logger.debug('len dead: %s', len(self.dead_sprites))
        for d in self.dead_sprites:
            if isinstance(d, Enemy):
                d.kill()
                d.respawn(self.spawn_outside())
                d.move_towards(self.player.sprites()[0].rect.center)
                d.add(self.enemies)
                self.all_sprites.add(d, layer=1)

        collisions = pg.sprite.spritecollide(self.player.sprite, self.enemies, False)
        for collide in collisions:
            self.player.sprite.gain_innertia(pg.Vector2(collide.rect.center))

    def draw(self, screen: pg.Surface):
        """Draw the current scene to the provided screen

        Parameters
        ----------
        screen : pg.Surface
            SCreen or surface to draw the scene too.
        """
        self.all_sprites.draw(screen)
