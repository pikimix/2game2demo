"""
Entrypoint for the Pygame 2game2demo
"""
import signal
import types
import argparse
import logging
import pygame

def signal_handler(sig: int, frame: types.FrameType) -> None:
    """
    Handle SIGINT signal and exit gracefully.

    This function handles the SIGINT signal (typically triggered by a 
    Ctrl+C action), logs debug and info messages, quits the pygame 
    library, and raises a SystemExit exception to terminate the program.

    Args:
        sig : int
            The signal number that was received.
        frame : types.FrameType 
            The current stack frame when the signal  was received.

    Logs:
        - Debug level log containing the signal and frame details.
        - Info level log indicating the reception of SIGINT and the graceful exit process.

    Actions:
        - If SIGINT is received, logs the details and exits the program:
            - Calls logger.debug() to log signal and stack frame details.
            - Calls logger.info() to log the graceful exit message.
            - Calls pygame.quit() to cleanly quit the pygame library.
            - Raises a SystemExit exception to terminate the program.

    Example:
        signal_handler(signal.SIGINT, frame)
    """
    if sig == signal.SIGINT:
        logger.debug('signal_handler: %s | %s', sig, frame)
        logger.info('signal_handler: Caught sigint, gracefully exiting.')
        pygame.quit()
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

# pygame setup
pygame.init()
pygame.display.set_mode((1280, 720))

# set the clock
clock: pygame.time.Clock = pygame.time.Clock()
running: bool = True
dt: int = 0

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000
