#!/usr/bin/env python
import os
from migrate.versioning.shell import main
main(debug='False', repository=os.path.dirname(__file__))
