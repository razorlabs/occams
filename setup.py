import os
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
import sys


HERE = os.path.abspath(os.path.dirname(__file__))

REQUIRES = [
    'occams',
]

EXTRAS = {
    'test': [],
}


def get_version():
    version_file = os.path.join(HERE, 'VERSION')

    # read fallback file
    try:
        with open(version_file, 'r+') as fp:
            version_txt = fp.read().strip()
    except:
        version_txt = None

    # read git version (if available)
    try:
        version_git = (
            Popen(['git', 'describe'], stdout=PIPE, stderr=PIPE, cwd=HERE)
            .communicate()[0]
            .strip()
            .decode(sys.getdefaultencoding()))
    except:
        version_git = None

    version = version_git or version_txt or '0.0.0'

    # update fallback file if necessary
    if version != version_txt:
        with open(version_file, 'w') as fp:
            fp.write(version)

    return version


setup(
    name=u'occams_roster',
    version=get_version(),
    description=u'',
    classifiers=[
        u'Development Status :: 4 - Beta'
        u'Intended Audience :: Developers'
        u'Operating System :: OS Independent'
        u'Programming Language :: Python',
        u'Topic :: Database',
        u'Topic :: Scientific/Engineering :: Bio-Informatics',
        u'Topic :: Scientific/Engineering :: Information Analysis',
        u'Topic :: Scientific/Engineering :: Medical Science Apps.',
        u'Topic :: Software Development :: Libraries',
        u'Topic :: Utilities',
        ],
    keywords=u'OCCAMS HIVe BEAST database roster clinical sqlalchemy',
    author=u'Young Labs',
    author_email=u'younglabs@ucsd.edu',
    url=u'https://github.com/younglabs/occams_roster',
    license=u'GPL',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
    entry_points="""
    [console_scripts]
    or_initdb = occams_roster.scripts.initdb:main
    """,
)
