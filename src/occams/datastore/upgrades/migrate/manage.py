import os

from migrate.versioning.shell import main as migrate_main

def main():
    migrate_main(
        repository=os.path.dirname(os.path.abspath(__file__)),
        debug='False')
