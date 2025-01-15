""" Collection of entitys that exist within the gamespace
"""
import logging
import pygame as pg

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class Entity(pg.sprite.DirtySprite):
    """Basic entity that gets drawn to screen
    """

    def __init__(self, origin: tuple[int, int], sprite_details: dict[str,str|int]|None):
        """Create new basic entity that gets drawn to screen

        Parameters
        ----------
        origin : tuple[int, int]
            location where the entity gets spwaned
        sprite_details : dict[str,str | int]
            details of the sprite to be drawn
        """
        super().__init__()
        #####
        # Set up the sprite
        self.dirty = 2
        self.visible = 1
        self.last_frame = 0
        self.frame_interval = 100
        radius = 10
        # Default to no sprite, render a cirle
        self.image = pg.Surface((20, 20), pg.SRCALPHA)# pylint: disable=no-member
        pg.draw.circle(self.image, (255,255,255,255), (radius,radius), radius=radius, width=0)
        self.rect = pg.Rect(origin[0],origin[1], radius*2, radius*2)
        self.source_rect = pg.Rect(0,0,radius*2, radius*2)
        self.rect = pg.Rect(origin[0], origin[1], radius*2, radius*2)
        # If there was sprite details passed, load the sprite
        if sprite_details:
            self.load_sprite(sprite_details)

        self.src_image = self.image
        # End setting up sprite
        #####

        #####
        # Movement
        self.velocity = pg.Vector2(0,0)
        self.max_velocity = 10
        #
        #####

    def load_sprite(self, sprite_details: dict[str,str|int]):
        """Load a sprite from a file

        Parameters
        ----------
        sprite_details : dict[str,str | int]
            details of the sprite to be loaded
        """
        self.image = pg.image.load(sprite_details['file']).convert_alpha()
        self.source_rect = pg.Rect(0, 0,
                                    sprite_details['width'], sprite_details['height'])
        self.rect = pg.Rect(self.rect.x, self.rect.y,
                                sprite_details['width'], sprite_details['height'])

    def respawn(self, origin: tuple[int, int]):
        """Respawn the entity at a new location.

        This will also reset the state of the entity to its default.

        Parameters
        ----------
        origin : tuple[int, int]
            Location to spawn in at.
        """
        self.source_rect.topleft = (0,0)
        self.rect.topleft = origin

    def update(self):
        """Update the current entity's animation frame
        """
        if (pg.time.get_ticks() > self.last_frame + self.frame_interval
            and self.source_rect.width < self.image.get_width()):
            self.source_rect.x += self.source_rect.width
            if self.source_rect.x >= self.image.get_width():
                self.source_rect.x = 0
            self.last_frame = pg.time.get_ticks()

    def move_towards(self, target: pg.Vector2):
        """
        Sets velocity to move the object towards a target position.

        This method calculates the vector from the object's current rect (center) 
        to the target position, normalizes this vector, and then sets the object's velocity 
        to move towards the target at a constant maximum velocity.

        Parameters
        ----------
        target : pg.Vector2
            The target position towards which the object will move.
        """
        target_velocity = target - pg.Vector2(self.rect.center)
        if target_velocity.length() != 0:
            self.velocity = target_velocity.normalize() * self.max_velocity

    def tint(self, color: pg.color.Color):# pylint: disable=c-extension-no-member
        """Tints a copy of the original image, and stores this as image for drawing

        Parameters
        ----------
        color : pg.color.Color
            Color to tint the original image with.
        """
        tinted = self.src_image.copy()
        if color:
            tinted.fill(color,None,pg.BLEND_RGBA_MIN)# pylint: disable=no-member
        self.image = tinted.copy()

class Player(Entity):
    """A locally controllable player extension to the entity class
    """
    def __init__(self, origin, sprite_details):
        super().__init__(origin, sprite_details)
        self.click_move: bool = False
        self.click_target: pg.Vector2 = None

    def update(self, bounds: pg.Rect=None):
        """Update the player movement, before passing to the parent class to update animation

        Parameters
        ----------
        bounds : pg.Rect
            Bounds that the player must remain within
        """
        # Get keys pressed
        keys = pg.key.get_pressed()

        # First check if the player has clicked a location
        mouse = pg.mouse.get_pressed(num_buttons=3)
        if mouse[0]:
            # If a location has been clicked, set click move to true and the click location
            # from the mouse potision so that this persists to the next frame
            mouse_pos = pg.mouse.get_pos()
            self.click_target = pg.Vector2(mouse_pos)
            self.click_move = True

        # After that, create a new target veloicty and check for keyboard input
        # We have a separate target velocity so that we can do some normalisation if
        # keyboard movement is used
        target_velocity = pg.Vector2(0, 0)
        # Depending on the keys pressed, change the target velocity
        if keys[pg.K_w]:# pylint: disable=no-member
            target_velocity.y += -1
        if keys[pg.K_s]:# pylint: disable=no-member
            target_velocity.y += 1
        if keys[pg.K_a]:# pylint: disable=no-member
            target_velocity.x += -1
        if keys[pg.K_d]:# pylint: disable=no-member
            target_velocity.x += 1

        # If the magnatute of the velocity is > 0, we need to move
        if target_velocity.length() > 0:
            self.click_move = False
            self.velocity = target_velocity.normalize() * self.max_velocity
            self.rect.move_ip(self.velocity)
        # Keyboard takes priority, but check after if mouse movement has been used
        elif self.click_move:
            # Set velocity to move to click location
            self.move_towards(self.click_target)
            if not self.velocity:
                self.click_move = False
            # Stop if we are "close enough" to the click location, but it is non 0
            # Possibly move this into the move_towards method
            elif self.click_target.distance_to(self.rect.center) < 10:
                self.click_move = False
            # if we haven't stopped, move
            else:
                self.rect.move_ip(self.velocity)
        # Make sure we stay in bouds, if we have bounds set.
        if bounds and not bounds.contains(self.rect):
            if self.rect.left < bounds.left:
                self.rect.left = bounds.left
            elif self.rect.right > bounds.right:
                self.rect.right = bounds.right
            if self.rect.top < bounds.top:
                self.rect.top = bounds.top
            elif self.rect.bottom > bounds.bottom:
                self.rect.bottom = bounds.bottom

        # Update the parent sprite class to update animation
        super().update()
