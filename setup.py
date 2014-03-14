from setuptools import find_packages, setup
from subprocess import Popen, PIPE
import os.path
import sys


HERE = os.path.abspath(os.path.dirname(__file__))


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
    name='occams.datastore',
    version=get_version(),
    description='Provides storage solution for sparse data.',
    classifiers=[
        'Development Status :: 4 - Beta'
        'Framework :: Zope3',
        'Intended Audience :: Developers'
        'Operating System :: OS Independent'
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        ],
    keywords='AVRC BIT OCCAMS datastore database eav sqlalchemy relational clinical',
    author='BIT Core Development Team',
    author_email='bitcore@ucsd.edu',
    url='https://bitbucket.org/ucsdbitcore/occams.datstore.git',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['occams'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'argparse',

        # Useful tool for result sets
        'ordereddict',

        # Import/Export support via XML
        'lxml',

        # ORM utilities and upgrade tools
        'SQLAlchemy',
        'sqlalchemy-migrate',

        # Component specification/documentation
        # Note that these packages do not install the entire Zope ecosystem,
        # they install necessary building blocks that are useful merely for
        # specification and documentation.
        'zope.component',
        'zope.deprecation',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.schema',

        # Low-level batching support for Zope products
        'z3c.batching',
        ],
    extras_require=dict(
        postgresql=['psycopg2'],
        test=['plone.testing'], # Required for layers, does not install Plone
        ),
    tests_require=['plone.testing'],
    )
