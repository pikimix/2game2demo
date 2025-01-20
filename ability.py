"""A module for classes relating to player abilities
"""

class BaseAttack:
    """Player Basic Attack
    """

    def __init__(self, power: int=10, interval: int=100, uses: int=-1, is_super: bool=False,
                    particle: dict[str,str|int]=None):
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
        particle : dict[str,str|int], optional
            Dict which describes the color/ lifetime, max velocity of the particles this 
            attack generates, by default None
            None results in {'color':'Yellow', 'lifetime':1000, 'max_vel':600} being used
        """
        self.power = power
        self.interval = interval
        self.uses = uses
        self.is_super = is_super
        self.particle = particle if particle else {'color':'Yellow', 'lifetime':1000, 'max_vel':600}
