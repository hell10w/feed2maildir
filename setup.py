from setuptools import find_packages
from setuptools import setup

import feed2any

setup(
    name='feed2any',
    version=feed2any.__version__,
    author='',
    author_email='',
    url='',
    description='',
    packages=find_packages(exclude=('tests', )),
    install_requires=[
        'six',
        'docopt',
        'cachetools',
        'requests',
        'feedparser',
        'jinja2',
        'python-dateutil',
        'html2text',
        'inscriptis'
    ],
    extras_require={
        'twitter': ['python-twitter'],
    },
    test_suite='tests',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'f2a--prefix=feed2any.prefix:main',
            'f2a--fetch=feed2any.fetch:main',
            'f2a--parse=feed2any.parse:main',
            'f2a--to-twitter=feed2any.to_twitter:main',
            'f2a--to-maildir=feed2any.to_maildir:main',
            'f2a--transform=feed2any.transform:main',
        ],
    },
)
