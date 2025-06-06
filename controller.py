import logging
from app import App
import pygame as pg

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class Controller:
    def __init__(self):
        pg.joystick.init()
        self.joystick = None
        js = [pg.joystick.Joystick(x) for x in range(pg.joystick.get_count())]
        if js:
            self.joystick = js[0]
        self.click_move:bool = False
        self.click_target = None
        self.attack_triggered = False

    def handle_input(self):
        """Handle input and move
        """
        # Get keys pressed
        keys = pg.key.get_pressed()

        # Check if we have triggered an attack and sett he flag.
        if keys[pg.K_SPACE] or (self.joystick is not None
                                and self.joystick.get_button(App.config('super'))):
            self.attack_triggered =  True
        else:
            self.attack_triggered =  False

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

        # Check if a joystick is connected/ used and change target velocity to match the stick
        # flag if we use stick as it doesnt need normalising
        stick_move = False
        if self.joystick is not None:
            if self.joystick.get_button(11):# pylint: disable=no-member
                target_velocity.y += -1
            if self.joystick.get_button(12):# pylint: disable=no-member
                target_velocity.y += 1
            if self.joystick.get_button(13):# pylint: disable=no-member
                target_velocity.x += -1
            if self.joystick.get_button(14):# pylint: disable=no-member
                target_velocity.x += 1
            if (abs(self.joystick.get_axis(0)) > App.config('deadzone') or
                abs(self.joystick.get_axis(1)) > App.config('deadzone')):
                stick_move = True
                target_velocity.x = self.joystick.get_axis(0)
                target_velocity.y = self.joystick.get_axis(1)
            logger.debug('controller x: %s', target_velocity.x)
            logger.debug('controller y: %s', target_velocity.y)
            logger.debug('')
        # If we are not using a controller, and  the magnatute of the velocity is > 0,
        # we need to normalize
        if target_velocity.length() > 0:
            self.click_move = False # We want to override click move on any other input
            if not stick_move:
                target_velocity = target_velocity.normalize()

        # Keyboard takes priority, but check after if mouse movement has been used
        if self.click_move:
            return {'target': True, 'vector': self.click_target}
        else:
            return {'target': False, 'vector': target_velocity}
