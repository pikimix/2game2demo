"""A module for classes relating to player abilities
"""
import pygame as pg
import particle
class BaseAttack:
    """Player Basic Attack
    """

    def __init__(self, power: int=10, interval: int=500, uses: int=-1, is_super: bool=False,
                    base_particle: particle.Particle=None, max_velocity: int=600):
        """Create a new basic attack with the provided details

        Parameters
        ----------
        power : int, optional
            Amount of damage the attack does, by default 10
        interval : int, optional
            The time between the attack triggering, by default 100
        uses : int, optional
            The number of times the attack can be used, -1 is infinite, by default -1
        is_super : bool, optional
            If the attack is a super attack, by default False
        base_particle : particle.Particle
            A default particle used to create the attack via deepcopy before updating its velocity
            and spawn time, by default None
            None results in {'color':'Yellow', 'lifetime':1000, } being used
        """
        self.power = power
        self.interval = interval
        self.uses = uses
        self.is_super = is_super
        self.max_velocity = max_velocity
        self.particle = base_particle if base_particle else particle.Particle(pg.Rect(0,0,1,1),
                                                                    pg.Vector2(0,0),
                                                                    'Yellow', 1000)
