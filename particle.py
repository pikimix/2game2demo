"""Module for particles
"""
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
        self.rect = rect
        self.last_pos= rect.center
        self.velocity = velocity
        self.color = color
        # self.image = pg.Surface((10, 10), pg.SRCALPHA)# pylint: disable=no-member
        # pg.draw.circle(self.image, color, (10,10), radius=10)
        self.has_expired = False
        self.spawn_time = pg.time.get_ticks()
        self.lifetime = lifetime

    def update(self, dt:int):
        """Update the particles position, and check if its lifetime has expired

        Parameters
        ----------
        dt : int
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
