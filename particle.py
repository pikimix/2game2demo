"""Module for particles
"""
from __future__ import annotations
import copy
import time
from random import randint
import pygame as pg
class Particle:
    """Simple particle with a Position (rect), direction (velocity), color and lifetime
    """

    def __init__(self, rect: pg.Rect, velocity: pg.Vector2, color: pg.Color=pg.Color('White'), 
                    lifetime: int=100, spawn_time: int|None=None):
        """Create new particle with given details

        Parameters
        ----------
        rect : pg.Rect
            Location to spawn the particle
        velocity : pg.Vector2
            velocity to give the particle
        color : pg.Color, optional
            color to draw the particle, by default pg.Color('White')
        lifetime : int, optional
            how long the particle will be alive, by default 100
        spawn_time: int|None
            time this particle was spawned, None handled by getting current time.time, default None
        """
        self.last_pos= rect.center
        self.rect = pg.Rect(0,0,10,10)
        self.rect.center = rect.center
        self.velocity = velocity
        self.color = color
        # self.image = pg.Surface((10, 10), pg.SRCALPHA)# pylint: disable=no-member
        # pg.draw.circle(self.image, color, (10,10), radius=10)
        self.has_expired = False
        self.spawn_time = time.time() * 1000
        if spawn_time is not None:
            self.spawn_time = spawn_time
        self.lifetime = lifetime

    def serialize(self) -> dict:
        """Serialize the particle to be re-created

        Returns
        -------
        dict
            dictionary representing this particle
        """
        print(self.color)
        serialized = {'type': 'particle'}
        for key, value in vars(self).items():
            match key:
                case 'rect':
                    serialized['position'] = value.center
                case 'velocity':
                    serialized['velocity'] = [value.x, value.y]
                case 'color':
                    serialized['color'] =(self.color.r,
                                            self.color.g,
                                            self.color.b,
                                            self.color.a)
                case x if x in ['spawn_time','lifetime', 'windup', 'radius', 'explosion_speed',
                                'decay',]:
                    serialized[key] = value
                case _:
                    pass
        return serialized

    def reset(self, rect: pg.Rect, velocity: pg.Vector2) -> Particle:
        """Returns a reset copy of this particle

        Parameters
        ----------
        rect : pg.Rect
            Location of the new copy
        velocity : pg.Vector2
            Velocity of the new copy

        Returns
        -------
        Particle
            Copy of this particle reset with the new location/ velocity
        """
        self.rect = rect
        self.last_pos= rect.center
        self.velocity = velocity
        self.has_expired = False
        self.spawn_time = time.time() * 1000
        return copy.deepcopy(self)

    def update(self, dt:float):
        """Update the particles position, and check if its lifetime has expired

        Parameters
        ----------
        dt : float
            Time that has elapsed since the last frame
        """
        if self.spawn_time + self.lifetime < time.time() * 1000:
            self.has_expired = True
        else:
            self.last_pos = self.rect.center
            self.rect.move_ip(self.velocity * dt)

    def draw(self, screen: pg.Surface):
        """Draw the particle to a surface

        Parameters
        ----------
        screen : pg.Surface
            Surface to draw too
        """
        pg.draw.circle(screen, self.color, self.rect.center, radius=5)

class Explosion(Particle):
    """Basic particle for explosion
    """
    def __init__(self, rect: pg.Rect, velocity: pg.Vector2, color: pg.Color=pg.Color('White'),
                    lifetime: int=1250, spawn_time: int|None=None,
                    windup: int=750, radius: int=100, explosion_speed: int=400, decay: float=0.95):
        """Create new explosion particle with given details

        Parameters
        ----------
        rect : pg.Rect
            Location to spawn the particle
        velocity : pg.Vector2
            velocity to give the particle
        color : pg.Color, optional
            color to draw the particle, by default pg.Color('White')
        lifetime : int, optional
            how long the particle will be alive, by default 1250
        spawn_time: int|None
            time this particle was spawned, None handled by getting current time.time, default None
        windup : int, optional
            how long it takes in ms before the explosion happens
            , by default 750
        radius : int, optional
            radius of the explosion marker, by default 100
        explosion_speed : int
            Average speed the explosion propagates, each particle is between 1/4 and 3x this
            value, by default 400
        decay : float
            The percentage multiplier for how much sub particles slow down by each frame,
            by default 0.95
        """
        super().__init__(rect, velocity, color, lifetime, spawn_time)
        self.rect.width = radius*2
        self.rect.height = radius*2
        self.rect.center = rect.center
        self.windup = windup
        self.inner_scale = 0
        self.radius = radius
        self.sub_particles: list[Particle] = []
        self.explosion_speed = explosion_speed
        self.triggered = False
        self.decay = decay

    def serialize(self):
        serialized = super().serialize()
        serialized['type'] = 'explosion'
        return serialized

    def reset(self, rect, velocity):
        self.sub_particles = []
        self.inner_scale = 0
        return super().reset(rect, velocity)

    def update(self, dt):
        super().update(dt)
        ticks = time.time() * 1000
        if self.spawn_time + self.windup < ticks:
            self.triggered = True
            if self.sub_particles == []:
                self.inner_scale = 0
                for x in range(0,360):
                    speed = randint(self.explosion_speed/4, self.explosion_speed*3)
                    p = Particle(self.rect.copy(),
                                pg.Vector2.from_polar((speed, x)),
                                'Red', self.lifetime - self.windup)
                    self.sub_particles.append(p)
            for p in self.sub_particles:
                if p.velocity.magnitude() > self.explosion_speed/4:
                    p.velocity *= self.decay
                p.update(dt)
            self.sub_particles = [p
                                for p in self.sub_particles
                                if not p.has_expired]
        else:
            self.triggered = False
            self.inner_scale = (ticks - self.spawn_time) / self.windup

    def draw(self, screen):
        if self.sub_particles != []:
            for p in self.sub_particles:
                p.draw(screen)
        else:
            pg.draw.circle(screen, self.color, self.rect.center,
                            radius=self.radius*self.inner_scale)
            pg.draw.circle(screen, self.color, self.rect.center, radius=self.radius, width=1)
