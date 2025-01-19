"""A scene which controls the entity state, and associated classes
"""
from __future__ import annotations # To make type hinting work when using classes within this file
import logging
import random
import pygame as pg
from pygame.sprite import Group, GroupSingle, LayeredDirty
from entity import Enemy, Player

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class EnemyPattern:
    """Class that holds details about an enemy pattern used by a Scene
    """
    def __init__(self, number_of_enemies: int, spawn_type: str,
                    enemy_behaviour: int|str|None=None, 
                    has_leader: bool=False,  distance: int=25):
        """Create a new enemy pattern

        Parameters
        ----------
        number_of_enemies : int
            Number of enemies in the pattern
        spawn_type: int | str
            Where the Enemies spawn, one of ['top', 'left', 'right', 'bottom', 'any']
        enemy_behaviour : int | str | None, optional
            behavioru of enemies in the pattern, by default None
        has_leader : bool, optional
            if the pattern has a leader, by default False
        spawn_type: int
            Distance to leave between enemies when spawning
            only takes affect when paired with has_leader
        """
        self.number_of_enemies = number_of_enemies
        self.enemy_behaviour = enemy_behaviour
        self.has_leader = has_leader
        self.distance = distance
        self.spawn_type = spawn_type if spawn_type in ['top', 'left', 'right', 'bottom'] else 'any'

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
        self.dead_sprites: Group = Group()

        # Create enemies for use later
        for _ in range(2001):
            enemy = Enemy(self.spawn_outside(), sprite)
            enemy.move_towards(pg.Vector2(self.player.sprites()[0].rect.center))
            self.dead_sprites.add(enemy)
        # Make all the enemies red
        for enemy in self.dead_sprites:
            enemy.tint('Red')

        self.all_sprites.add(self.player, layer=2)

        self.spawn_patterns = [
                                EnemyPattern(1, 'any'),
                                EnemyPattern(20, 'left', has_leader=True),
                                EnemyPattern(20, 'bottom', has_leader=True, distance=200),
                                EnemyPattern(20, 'top', has_leader=True, distance=200),
                                EnemyPattern(20, 'right', has_leader=True, distance=50),
                                EnemyPattern(20, 'right', has_leader=True),
                                EnemyPattern(200, 'top'),
                                EnemyPattern(200, 'bottom')
        ]
        self.last_spawn = 0
        self.spaw_timeout = 1000

    def spawn_outside(self, direction: str='any') -> tuple[int, int]:
        """Provide spawn point thats outside the playable bounds.

        spawn_type: int | str
            Where the Enemies spawn, one of ['top', 'left', 'right', 'bottom', 'any']
            by default 'any'

        Returns
        -------
        tuple
            tuple representing a location to spawn thats outside the space of the screen
        """
        if direction == 'any':
            direction = random.choice(['top', 'left', 'right', 'bottom'])
        # logger.debug('Scene:spawn_outside: direction=%s', direction)
        offset = [random.randint(50,100), random.randint(50,100)]

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

    def spawn_near(self, target: tuple[int, int], distance: int=50,
                    direction: str='any') -> tuple[int, int]:
        """Spawn an enemy within a given distance and direction of a of a specific point

        Parameters
        ----------
        target : tuple[int, int]
            Target to spawn near
        distance : int, optional
            Distance to be within, by default 50
        direction : str, optional
            Direction to spawn in, one of ['top', 'left', 'right', 'bottom', 'any']
            by default 'any'

        Returns
        -------
        tuple[int, int]
            tuple representing a location to spawn thats within the desired location
        """
        if direction == 'any':
            direction = random.choice(['top', 'left', 'right', 'bottom'])
        # logger.debug('Scene:spawn_outside: direction=%s', direction)

        offset = [random.randint(0, distance*2), random.randint(0, distance*2)]
        if direction == 'top':
            offset[0] = target[0] + random.choice([offset[0], -offset[0]])
            offset[1] = target[1] - offset[1]
        if direction == 'left':
            offset[0] = target[0] - offset[0]
            offset[1] = target[1] + random.choice([offset[1], -offset[1]])
        if direction == 'right':
            offset[0] += target[0]
            offset[1] = target[1] + random.choice([offset[1], -offset[1]])
        if direction == 'bottom':
            offset[0] = target[0] + random.choice([offset[0], -offset[0]])
            offset[1] += target[1]

        return tuple(offset)

    def update(self, dt:float):
        """Update the current scene

        Parameters
        ----------
        dt : float
            deltatime - time since last update
        """
        ticks = pg.time.get_ticks()
        self.player.update(self.bounds, dt)


        for e in self.enemies:
            e.update(dt)
            if not self.bounds.colliderect(e.rect):
                if e.has_been_onscreen:
                    e.kill()
                    self.dead_sprites.add(e)
            elif not e.has_been_onscreen:
                e.has_been_onscreen = True

        if self.last_spawn + self.spaw_timeout < ticks:
            self.spawn_enemies(random.choice(self.spawn_patterns))
            self.last_spawn = ticks

        collisions = pg.sprite.spritecollide(self.player.sprite, self.enemies, False)
        for collide in collisions:
            self.player.sprite.gain_innertia(pg.Vector2(collide.rect.center))

    def spawn_enemies(self, pattern: EnemyPattern):
        """Spawn enemies based on the provided pattern

        Parameters
        ----------
        pattern : EnemyPattern
            Enemy pattern describing the spawn rate/ positions of enemies
        """
        spawned = []
        for d in self.dead_sprites:
            if isinstance(d, Enemy):
                d.kill()
                d.behaviour = pattern.enemy_behaviour
                if pattern.has_leader:
                    if len(spawned) == 0:
                        if pattern.spawn_type == 'any':
                            pattern.spawn_type = random.choice(['top', 'left', 'right', 'bottom'])
                        spawn = self.spawn_outside(pattern.spawn_type)
                        d.respawn(spawn)
                        d.move_towards(self.player.sprites()[0].rect.center)
                        setattr(pattern, "leader_pos", spawn)
                        setattr(pattern, "leader_vel", d.velocity)
                    else:
                        if pattern.distance:
                            d.respawn(self.spawn_near(pattern.leader_pos,
                                                        direction=pattern.spawn_type,
                                                        distance=pattern.distance))
                        else:
                            d.respawn(self.spawn_near(pattern.leader_pos, 
                                                        direction=pattern.spawn_type))
                        d.velocity = pattern.leader_vel
                else:
                    d.respawn(self.spawn_outside(pattern.spawn_type))
                    d.move_towards(self.player.sprites()[0].rect.center)
                spawned.append(d.rect)
                d.add(self.enemies)
                self.all_sprites.add(d, layer=1)
                if len(spawned) >= pattern.number_of_enemies:
                    break
        logger.debug(spawned)

    def draw(self, screen: pg.Surface):
        """Draw the current scene to the provided screen

        Parameters
        ----------
        screen : pg.Surface
            SCreen or surface to draw the scene too.
        """
        self.all_sprites.draw(screen)
