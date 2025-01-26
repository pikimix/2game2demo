"""Module for particles
"""
from __future__ import annotations
import copy
import pygame as pg

class Particle:
    """Simple particle with a Position (rect), direction (velocity), color and lifetime
    """

    def __init__(self, rect: pg.Rect, velocity: pg.Vector2,
                    color: pg.Color=pg.Color('White'), lifetime: int=100):
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
        """
        self.last_pos= rect.center
        self.rect = pg.Rect(0,0,10,10)
        self.rect.center = rect.center
        self.velocity = velocity
        self.color = color
        # self.image = pg.Surface((10, 10), pg.SRCALPHA)# pylint: disable=no-member
        # pg.draw.circle(self.image, color, (10,10), radius=10)
        self.has_expired = False
        self.spawn_time = pg.time.get_ticks()
        self.lifetime = lifetime

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
        self.spawn_time = pg.time.get_ticks()
        return copy.deepcopy(self)

    def update(self, dt:float):
        """Update the particles position, and check if its lifetime has expired

        Parameters
        ----------
        dt : float
            Time that has elapsed since the last frame
        """
        if self.spawn_time + self.lifetime < pg.time.get_ticks():
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
    def __init__(self, rect: pg.Rect, velocity: pg.Vector2,
                    color: pg.Color=pg.Color('White'), lifetime: int=600,
                    windup: int=500, radius: int=50, explosion_speed: int=1200):
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
            how long the particle will be alive, by default 110
        windup : int, optional
            how long it takes in ms before the explosion happens
            , by default 500
        radius : int, optional
            radius of the explosion marker, by default 50
        explosion_speed : int
            Speed the explosion propagates, by default 1200
        """
        super().__init__(rect, velocity, color, lifetime)
        self.rect.width = radius*2
        self.rect.height = radius*2
        self.rect.center = rect.center
        self.windup = windup
        self.inner_scale = 0
        self.radius = radius
        self.sub_particles = []
        self.explosion_speed = explosion_speed

    def reset(self, rect, velocity):
        self.sub_particles = []
        self.inner_scale = 0
        return super().reset(rect, velocity)

    def update(self, dt):
        super().update(dt)
        ticks = pg.time.get_ticks()
        if self.spawn_time + self.windup < ticks:
            if self.sub_particles == []:
                self.inner_scale = 0
                for x in range(0,360):
                    p = Particle(self.rect.copy(),
                                pg.Vector2.from_polar((self.explosion_speed, x)),
                                'Red', self.lifetime - self.windup)
                    self.sub_particles.append(p)

            for p in self.sub_particles:
                p.update(dt)

            self.sub_particles = [p
                                for p in self.sub_particles
                                if not p.has_expired]
        else:
            self.inner_scale = (ticks - self.spawn_time) / self.windup

    def draw(self, screen):
        if self.sub_particles != []:
            for p in self.sub_particles:
                p.draw(screen)
        else:
            pg.draw.circle(screen, self.color, self.rect.center,
                            radius=self.radius*self.inner_scale)
            pg.draw.circle(screen, self.color, self.rect.center, radius=self.radius, width=1)
