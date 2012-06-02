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

from pylint import lint

import sys

def run_pylint():
    """Runs pylint on the module supplied via command line arguments.
    
    Usage:
    
    >>> bin/python tests/pylint.py path_to_module_or_package
    
    where path_to_module is the relative or absolute path to the module
    or package which you want to test with pylint.
    
    The format of the message output by pylint is:
         MESSAGE_TYPE: LINE_NUM:[OBJECT:] MESSAGE
    where MESSAGE_TYPE can be C(convention), R(refactor), W(warning),
    E(Error), F(Fatal)
    
    Reports generation is disabled by default. 
    Ids are included with message types by default.
    These settings can be changed in the args variable below.
    
    For a full list of command line options pass --help .
    
    For more information please refer to the pyline manual at 
    http://www.logilab.org/card/pylint_manual
    """
    args = [
        '--reports=n',
        '--include-ids=y']
    sys.argv.extend(args)
    lint.Run(sys.argv[1:])

if __name__=='__main__':
    run_pylint()