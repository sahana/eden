import os
import re
from setuptools import setup, find_packages


setup(
    name = 'e-cidadania',
    description=("e-cidadania is a project to develop an open source "
                 "application for citizen participation, usable by "
                 "associations, companies and administrations."),
    version = '0.1.5',
    packages = find_packages(exclude=['parts']),
    author='Oscar',
    url='http://ecidadania.org',
    license='GPLv2',
    install_requires = [
        ],
    tests_require=[
        ],
    include_package_data = True,
    zip_safe = False,
    )
