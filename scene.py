"""A scene which controls the entity state, and associated classes
"""
from __future__ import annotations # To make type hinting work when using classes within this file
import logging
import random
import time
import pygame as pg
from pygame.sprite import Group, LayeredDirty
import yaml
from app import App
from gamestate import Gamestate
from entity import Enemy, Ghost, Player
from hud import Bar, Scoreboard, Text
from network import Client
from particle import Explosion, Particle

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class EnemyPattern:
    """Class that holds details about an enemy pattern used by a Scene
    """
    def __init__(self, number_of_enemies: int, spawn_type: str,
                    enemy_behaviour: int|str|None=None,
                    has_leader: bool=False,  distance: int=25,
                    target: pg.Vector2|None=None, target_direction: pg.Vector2=None):
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
        distance : int, optional
            Distance to leave between enemies when spawning
            only takes affect when paired with has_leader
        target : pg.Vector2, optional
            Target location for spawned object to move towards, leave as None to target player
            by default None, cannot be used with target_direction
        target_direction : pg.Vector2, optional
            Normalised unit vector indicating the direction spawned enemies should move.
            by default None, cannot be used with target

        Raises
        ------
        ValueError
            When trying to set both target and target_direction as they are mutually exclusive.
        """
        self.number_of_enemies = number_of_enemies
        self.enemy_behaviour = enemy_behaviour
        self.has_leader = has_leader
        self.distance = distance
        self.spawn_type = spawn_type if spawn_type in ['top', 'left', 'right', 'bottom'] else 'any'
        self.target = target
        self.target_direction = target_direction
        if target and target_direction:
            raise ValueError('Cannot set both target and target_direction')

    @staticmethod
    def create_from_dict(ep: dict) -> EnemyPattern:
        """Create a new Enemmy Patter from a dictionary

        Parameters
        ----------
        ep : dict
            Dictionary representing the new enemy pattern

        Returns
        -------
        EnemyPattern
            The Enemy Pattern to be returned
        """
        pattern = EnemyPattern(0, 'any')
        # Set the vaklue if every key to an attribute in the pattern object
        for k, v in ep.items():
            match k:
                case 'target':
                    match v:
                        case 'bounds.center':
                            pattern.target='bounds.center'
                        case _: # If we cant parse the target, the target doesnt exist
                            pattern.target=None
                case 'target_direction':
                    pattern.target_direction=pg.Vector2(v)
                case _:
                    setattr(pattern, k, v)
        return pattern

    @staticmethod
    def load_from_file(filepath: str) -> list[EnemyPattern]:
        """Loads a YAML file representing all the EnemyPatterns required

        Parameters
        ----------
        filepath : str
            File path of the YAML file

        Returns
        -------
        list[EnemyPattern]
            The list of enemy patterns created
        """
        with open(filepath, 'r', encoding="utf-8") as f:
            yml = yaml.safe_load(f)
            eps = []
            # if dict, assume single enemy pattern, assume single Enemy Pattern
            if isinstance(yml, dict):
                eps.append(EnemyPattern.create_from_dict(yml))
            # If list, assume list of EnemyPatterns
            elif isinstance(yml, list):
                for pattern in yml:
                    eps.append(EnemyPattern.create_from_dict(pattern))
            return eps

class Scene:
    """A scene (or "level") of the game
    """
    def __init__(self, bounds: pg.Rect, enemy_pattern_yml: str=None):
        """Create a new scene

        Parameters
        ----------
        bounds : pg.Rect
            Bounds of the playable screen
        enemy_pattern_yml : str, optional
            File path to load enemy patterns from, set to None to use default patterns
            by default None
        """
        self.bounds = bounds
        self.sprite =  {
            'file':'assets/sprites/player.png',
            'width': 32,
            'height': 32,
            'frames': 4
        }
        Gamestate.player = Player(bounds.center, self.sprite)
        self.all_sprites: LayeredDirty[Enemy|Ghost|Player] = LayeredDirty()
        self.dead_sprites: Group[Enemy|Ghost|Player] = Group()
        Gamestate.super_attacks: dict[str,list[Explosion|Particle]] = {}

        # Create enemies for use later
        for _ in range(2001):
            enemy = Enemy((-100,-100), self.sprite)
            self.dead_sprites.add(enemy)
        # Make all the enemies red
        for enemy in self.dead_sprites:
            enemy.tint('Red')

        self.all_sprites.add(Gamestate.player, layer=2)
        self.spawn_patterns = []
        if enemy_pattern_yml is not None:
            self.spawn_patterns = EnemyPattern.load_from_file(enemy_pattern_yml)
        else:
            self.spawn_patterns = [
                                    EnemyPattern(1, 'any'),
                                    EnemyPattern(20, 'left', has_leader=True),
                                    EnemyPattern(20, 'bottom', has_leader=True, distance=200),
                                    EnemyPattern(20, 'top', has_leader=True, distance=200,
                                                    target_direction=pg.Vector2(0,1)),
                                    EnemyPattern(20, 'right', has_leader=True, distance=50),
                                    EnemyPattern(20, 'right', has_leader=True,
                                                    target_direction=pg.Vector2(1,0)),
                                    EnemyPattern(200, 'top', target=self.bounds.center),
                                    EnemyPattern(200, 'bottom',target=self.bounds.center)
            ]
        self.last_spawn = 0
        self.spaw_timeout = 1000

        #####
        # Hud
        self.hp = Bar(pg.Rect(self.bounds.centerx-100,self.bounds.bottom-20, 100,20))
        self.hp_label = Text(pg.Rect(self.bounds.centerx-100,self.bounds.bottom-40, 40,20), "HP")
        self.super = Bar(pg.Rect(self.bounds.centerx,self.bounds.bottom-20, 100,20), color='Blue')
        self.super_label = Text(pg.Rect(self.bounds.centerx,self.bounds.bottom-40, 40,20), "SUPER")
        self.scoreboard = Scoreboard((10,10,0,0), {App.config('name'):0})
        Gamestate.score[App.config('name')] = 0
        self.hud = Group(self.hp, self.hp_label, self.super, self.super_label, self.scoreboard)
        #
        #####

        #####
        # Net
        self.client = None
        if App.config('url'):
            url = App.config('url')
            if 'ws://' not in url:
                url = f'ws://{url}'
            port = 8080 if not App.config('port') else App.config('port')
            self.client = Client(url, port)
            self.client.start()
            self.client.send({'uuid':str(Gamestate.player.uuid), 'time': time.time()})
            logger.debug(self.client)

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
            offset[0] = random.randint(-100,self.bounds.width + 100)
            offset[1] = -offset[1]
        if direction == 'left':
            offset[0] = -offset[0]
            offset[1] = random.randint(-100,self.bounds.height + 100)
        if direction == 'right':
            offset[0] += self.bounds.width
            offset[1] = random.randint(-100,self.bounds.height + 100)
        if direction == 'bottom':
            offset[0] = random.randint(-100,self.bounds.width + 100)
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

        if Gamestate.player.alive():
            # Check if the player needs to attack, then fire one off if there are enemies
            if Gamestate.player.last_attack + Gamestate.player.attacks.interval < ticks:
                enemy = None
                if len(Gamestate.enemies) > 1:
                    enemy = min([e for e in Gamestate.enemies.sprites()],
                                key=lambda e: pow(e.rect.x-Gamestate.player.rect.x, 2)
                                            + pow(e.rect.y-Gamestate.player.rect.y, 2))
                elif len(Gamestate.enemies) == 1:
                    enemy = Gamestate.enemies.sprites()[0]
                if enemy is not None:
                    Gamestate.player.attack(pg.Vector2(enemy.rect.center), ticks)

            Gamestate.player.update(self.bounds, dt)
            # Check if the player can/ has triggered super
            super_charge = (ticks - Gamestate.player.last_super)/  Gamestate.player.super_ability.interval
            if super_charge > 1:
                super_charge = 1
                keys = pg.key.get_pressed()
                if keys[pg.K_SPACE]: # pylint: disable=no-member
                    new_super = Gamestate.player.super_attack(ticks)
                    Gamestate.new_supers.append(new_super)
                    if Gamestate.player.uuid in Gamestate.super_attacks:
                        Gamestate.super_attacks[Gamestate.player.uuid].append(new_super)
                    else:
                        Gamestate.super_attacks[Gamestate.player.uuid] = [new_super]
                    super_charge = 0
            self.super.scale_bar(super_charge)

        else:
            # if the player is not alive, we need to make sure their particles are updated/ culled
            for p in Gamestate.player.particles:
                p.update(dt)
            Gamestate.player.particles = [p
                                    for p in Gamestate.player.particles
                                    if not p.has_expired]
            keys = pg.key.get_pressed()
            if keys[pg.K_SPACE]: # pylint: disable=no-member
                Gamestate.player.respawn(self.bounds.center)
                Gamestate.player.last_super = ticks
                Gamestate.player.add(self.all_sprites)
                self.hp.scale_bar(1)
                self.super.scale_bar(0)
                Gamestate.score[App.config('name')] = 0
                self.last_spawn = ticks

        # Update all our super attacks # pylint: disable=consider-using-dict-items
        for key in Gamestate.super_attacks:
            for p in Gamestate.super_attacks[key]:
                p.update(dt)
                if p.triggered: # Check if the super has triggered and is damaging
                    for sub in p.sub_particles: # Check if the sub particles hit us/ enemies
                        self.check_attacks(sub, 25, Gamestate.enemies)
                        self.check_attacks(sub, 25, [Gamestate.player])
                    p.sub_particles = [sub for sub in p.sub_particles if not sub.has_expired]
            Gamestate.super_attacks[key] = [p for p in Gamestate.super_attacks[key]if not p.has_expired]
        # pylint: enable=consider-using-dict-items

        # Check if any of our attacks hit, kill enmies that are hit,
        # and remove the particle that killed them
        for particle in Gamestate.player.particles:
            try:
                sub_particles = getattr(particle, 'sub_particles')
                for p in sub_particles:
                    self.check_attacks(p, Gamestate.player.attacks.power, Gamestate.enemies)
            except AttributeError:
                self.check_attacks(particle, Gamestate.player.attacks.power, Gamestate.enemies)

        self.scoreboard.update_scores(Gamestate.score)
        for e in Gamestate.enemies:
            e.update(dt)
            if not self.bounds.colliderect(e.rect):
                if e.has_been_onscreen:
                    e.kill()
                    self.dead_sprites.add(e)
            elif not e.has_been_onscreen:
                e.has_been_onscreen = True

        if self.last_spawn + self.spaw_timeout < ticks and Gamestate.player.alive():
            self.spawn_enemies(random.choice(self.spawn_patterns))
            self.last_spawn = ticks

        collisions: list[Enemy] = pg.sprite.spritecollide(Gamestate.player, Gamestate.enemies, False)
        for collide in collisions:
            self.damage_player(collide.power, collide.rect.center)

        if self.client is not None:
            self.net_update(dt)

    def damage_player(self, power: int, collision_center: tuple[int,int]):
        """Damage the player after collision

        Parameters
        ----------
        power : int
            Power of the attack that hit the player
        collision_center : tuple[int,int]
            location of the center of the collision
        """
        Gamestate.player.current_hp -= power
        if Gamestate.player.current_hp <= 0:
            Gamestate.player.kill()
            self.hp.scale_bar(0)
            # logger.debug(Gamestate.player)
        else:
            self.hp.scale_bar(Gamestate.player.current_hp / Gamestate.player.max_hp)
            Gamestate.player.gain_innertia(pg.Vector2(collision_center))

    def net_update(self, dt: float):
        """Process updates from a network server

        Parameters
        ----------
        dt : float
            delta time for velocity updates on network elements between messages
        """
        # This can probably be cleaned up
        # Update local ghosts
        Gamestate.ghosts.update(dt=dt)
        for update in self.client.get_messages():
            Gamestate.update_net(update)
            self.all_sprites.add(Gamestate.ghosts)
            # for g in Gamestate.update_net(update):
                # self.all_sprites.add(g)


        # end by sending out update
        msg = Gamestate.serialize()
        msg['time'] = time.time()
        self.client.send(msg)

    def check_attacks(self, attack: pg.sprite.Sprite, attack_pwr: int,
                            targets: Group|list[Player]):
        """Check if an attack (normally a particle or sub particle) hiss an target (normally a 
        sprite group of enemies)

        Parameters
        ----------
        attack : pg.sprite.Sprite
            Sprite or sprite like object that is doing the attack
        attack_pwr : int
            Damage the attack does if it hits
        targets : Group
            SpriteGroup of targets
        """
        hit: Group[Enemy|Player] = pg.sprite.spritecollide(attack, targets, False)
        for h in hit:
            if isinstance(h, Enemy):
                h.current_hp -= attack_pwr
                if h.current_hp <= 0:
                    h.kill()
                    Gamestate.score[App.config('name')] += h.max_hp
                    self.dead_sprites.add(h)
            elif isinstance(h, Player):
                self.damage_player(attack_pwr,attack.rect.center)
            else:
                logger.error('Scene:check_attacks: Collision between %s and %s, but %s is not'
                                ' a player or enemy', attack, h, h)
        if len(hit):
            attack.has_expired = True

    def spawn_enemies(self, pattern: EnemyPattern):
        """Spawn enemies based on the provided pattern

        Parameters
        ----------
        pattern : EnemyPattern
            Enemy pattern describing the spawn rate/ positions of enemies
        """
        spawned = []
        spawn_type = pattern.spawn_type
        for d in self.dead_sprites:
            if isinstance(d, Enemy):
                d.kill()
                d.behaviour = pattern.enemy_behaviour
                if pattern.has_leader:
                    if len(spawned) == 0:
                        if spawn_type == 'any':
                            spawn_type = random.choice(['top', 'left', 'right', 'bottom'])
                        spawn = self.spawn_outside(spawn_type)
                        d.respawn(spawn)
                        self.spawn_target(d, pattern)
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
                    self.spawn_target(d, pattern)
                spawned.append(d.rect)
                d.add(Gamestate.enemies)
                self.all_sprites.add(d, layer=1)
                if len(spawned) >= pattern.number_of_enemies:
                    break
        # logger.debug(spawned)

    def spawn_target(self, enemy: Enemy, pattern: EnemyPattern):
        """Set the movement target of a newly spawned enemy

        Parameters
        ----------
        enemy : Enemy
            Enemy to set the movement for
        pattern : EnemyPattern
            Spawn pattern dictating the movement of the enemy
        """
        match pattern.target:
            case 'bounds.center':
                enemy.move_towards(self.bounds.center)
            case pg.Vector2():
                enemy.move_towards(pattern.target)
            case _:
                if pattern.target_direction:
                    enemy.set_direction(pattern.target_direction)
                else:
                    enemy.move_towards(Gamestate.player.rect.center)

    def draw(self, screen: pg.Surface):
        """Draw the current scene to the provided screen

        Parameters
        ----------
        screen : pg.Surface
            SCreen or surface to draw the scene too.
        """
        self.all_sprites.draw(screen)
        for p in Gamestate.player.particles:
            p.draw(screen)
        self.hud.draw(screen)
        for s in Gamestate.super_attacks.values():
            for p in s:
                p.draw(screen)
