""" Collection of entitys that exist within the gamespace
"""
import pygame as pg

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
        self.dirty = 2
        self.visible = 1
        self.last_frame = 0
        self.frame_interval = 100
        radius = 10
        self.image = pg.Surface((20, 20), pg.SRCALPHA)# pylint: disable=no-member
        pg.draw.circle(self.image, (255,255,255,255), (radius,radius), radius=radius, width=0)
        self.rect = pg.Rect(origin[0],origin[1], radius*2, radius*2)
        self.source_rect = pg.Rect(0,0,radius*2, radius*2)
        self.rect = pg.Rect(origin[0], origin[1], radius*2, radius*2)
        if sprite_details:
            self.image = pg.image.load(sprite_details['file']).convert_alpha()
            self.source_rect = pg.Rect(0, 0,
                                        sprite_details['width'], sprite_details['height'])
            self.rect = pg.Rect(origin[0], origin[1],
                                    sprite_details['width'], sprite_details['height'])
        self.src_image = self.image

    def update(self):
        """Update the current entity's animation frame
        """
        if pg.time.get_ticks() > self.last_frame + self.frame_interval:
            self.source_rect.x += self.source_rect.width
            if self.source_rect.x >= self.image.get_width():
                self.source_rect.x = 0
            self.last_frame = pg.time.get_ticks()
            print(pg.time.get_ticks())

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
