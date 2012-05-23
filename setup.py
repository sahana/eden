import os
import re
from setuptools import setup, find_packages


setup(
    name = 'e-cidadania',
    description = ("e-cidadania is a project to develop an open source "
                   "application for citizen participation, usable by "
                   "associations, companies and administrations."),
    version = '0.1.5',
    packages = find_packages(exclude=['parts']),
    author = 'Oscar',
    url = 'http://ecidadania.org',
    license = 'GPLv2',
    install_requires = [
        'django', 
        'PIL',
        'django-grappelli',
        'feedparser',
        'python-dateutil==1.5',
        'pyyaml',
        ],
    tests_require=[
        'nose',
        'django-nose',
        'coverage',
        'nose-cov',
        ],
    entry_points = {'console_scripts': ['check-quality = tests.run:main',
                                       ],
                   },
    include_package_data = True,
    zip_safe = False,
    )
