"""Module to handle displaying information on screen
"""
import logging
import pygame as pg
from pygame.sprite import Sprite
from app import App

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class Bar(Sprite):
    """Basic bar HUD Element
    """

    def __init__(self, rect: pg.Rect, anchor: str|None=None, color: pg.Color='Red'):
        super().__init__()
        self.rect = rect
        self.anchor = anchor
        self.color = color
        self.image = pg.Surface(rect.bottomright, pg.SRCALPHA) # pylint: disable=no-member
        pg.draw.rect(self.image, self.color, pg.Rect(0,0, self.rect.width, self.rect.height), 0)
        pg.draw.rect(self.image, 'Black', pg.Rect(0,0, self.rect.width, self.rect.height), 1)

    def scale_bar(self, new_percent: float):
        """Update the percentage on the bar

        Parameters
        ----------
        new_percent : int
            New percent of the bar that is full, between 0 and 1
        """
        if new_percent < 0 or new_percent > 1:
            logger.error('Hud.Bar.scale_bar: new_percent not within 0 and 1: %s', new_percent)
            new_percent = 1
        self.image.fill((0,0,0,0))
        pg.draw.rect(self.image, self.color,
                     pg.Rect(0,0, self.rect.width * new_percent, self.rect.height), 0)
        pg.draw.rect(self.image, 'Black', pg.Rect(0,0, self.rect.width, self.rect.height), 1)

class Text(Sprite):
    """Basic Text Element
    """

    def __init__(self, rect: pg.Rect, text: str):
        """Create a basic text element

        Parameters
        ----------
        rect : pg.Rect
            Location to draw the text
        text : str
            Text to render to screen
        """
        super().__init__()
        self.rect = rect
        self.image = App.config('font').render(text, True, (0, 0, 0))

    def update_text(self, text: str):
        """Update the text rendered to screen

        Parameters
        ----------
        text : str
            Text to render to screen
        """
        self.image = App.config('font').render(text, True, (0, 0, 0))
