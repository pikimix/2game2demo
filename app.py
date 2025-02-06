"""Module to contain app level config
"""
import logging
import typing
import pygame as pg
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class App:
    """App level config

    Raises
    ------
    NameError
        Raised when something tries to set a value to a read only attribute
    """
    __conf = {
        'name': 'Player',
        'font30': None, # Font needs to be initialised before this is set
        # default font is set in main as pg.font.SysFont('Futura', 30)
        'font18': None, # Font needs to be initialised before this is set
        # default font is set in main as pg.font.SysFont('Futura', 30)
        'url' : None,
        'port' : 8080
    }

    @staticmethod
    def config(name: str) -> typing.Any:
        """Get config item

        Parameters
        ----------
        name : str
            Name of the config object to get

        Returns
        -------
        Any
            The config value requested.
        """
        return App.__conf.get(name, None)

    @staticmethod
    def set(name: str, value: typing.Any):
        """Set the requested config element to a specific value

        Parameters
        ----------
        name : str
            The name of the config item
        value : typing.Any
            The value to set to

        Raises
        ------
        NameError
            Raised when the requested item is not settable
        """
        App.__conf[name] = value

    @staticmethod
    def load(filepath: str='config.yml'):
        """Load config from YAML file

        Parameters
        ----------
        filepath : str
            Location of Yaml file for config, by default 'config.yml'
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                yml: dict = yaml.safe_load(f)
                for k, v in yml.items():
                    match k:
                        case f if k in ['font18', 'font30']:
                            App.set(k, pg.font.SysFont(v, int(k[-2:])))
                        case _:
                            App.set(k, v)
                logger.critical(App.__conf)
        except FileNotFoundError:
            logger.error('App.load: %s not found.', filepath)
