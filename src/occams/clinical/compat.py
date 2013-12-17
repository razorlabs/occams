"""
Various Python 2.7/3X compatibilty wrappers
"""

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
