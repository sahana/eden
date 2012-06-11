#/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012 Cidadania S. Coop. Galega
#
# This file is part of e-cidadania.
#
# e-cidadania is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# e-cidadania is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with e-cidadania. If not, see <http://www.gnu.org/licenses/>.

import pep8

import sys


def run_pep():
    """Runs pep on the module or package supplied via command line.
    
    Usage: bin/python tests/pep.py [options] path_to_module_or_package
    
    If you want to see full set of command line options offered by
    pep, pass --help.
    
    """
    
    args = [
        '--show-source',
        '--show-pep8',
        '--ignore=W291'
    ]
    
    sys.argv.extend(args)
    pep8._main()


if __name__=='__main__':
    run_pep()