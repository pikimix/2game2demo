"""
Entrypoint for the Pygame 2game2demo
"""
import signal
import types
import argparse
import logging
import pygame as pg
from scene import Scene

def signal_handler(sig: int, frame: types.FrameType) -> None:
    """
    Handle SIGINT signal and exit gracefully.

    This function handles the signal processing, logs debug and info messages,
    quits the pygame, and raises a SystemExit exception to terminate the
    program.

    Parameters
    ----------
    sig : int
        The signal number that was received.
    frame : types.FrameType
        The current stack frame when the signal was received.
    """
    if sig == signal.SIGINT:
        logger.debug('signal_handler: %s | %s', sig, frame)
        logger.info('signal_handler: Caught sigint, gracefully exiting.')
        pg.quit()# pylint: disable=no-member
        raise SystemExit

# parse arguments passed when started
parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", help="Player name", required=False)
parser.add_argument("-v", "--verbosity", help="Logging verbosity - default vvv", action='count')
args = parser.parse_args()

#create our logger and default to only show warnings
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)
if args.verbosity:
    if args.verbosity <= 5:
        # Calculate log level from number of v's passed in
        logger.setLevel((6 - args.verbosity) * 10)
logger.info(' Log Level=%s', logging.getLevelName(logger.getEffectiveLevel()))

signal.signal(signal.SIGINT, signal_handler)

# pg setup
pg.init()# pylint: disable=no-member
_screen = pg.display.set_mode((1280, 720))

# set the clock
clock: pg.time.Clock = pg.time.Clock()
running: bool = True
dt: int = 0

scene = Scene(_screen.get_rect())

while running:
    # poll for events
    # pg.QUIT event means the user clicked X to close your window
    for event in pg.event.get():
        if event.type == pg.QUIT:# pylint: disable=no-member
            running = False
    _screen.fill("forestgreen")

    scene.update(dt)
    scene.draw(_screen)
    # flip() the display to put your work on screen
    pg.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000
