import os
from setuptools import setup, find_packages
from setuptools.command.develop import develop as _develop

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()


REQUIRES = [
    'occams',
    'occams_datastore',                 # EAV
    'occams_roster',
    'occams_forms',                     # EAV form renderer
]

EXTRAS = {
    'test': []
}


def get_version():
    """
    Generates python version from projects git tag
    """
    import os
    from subprocess import Popen, PIPE
    import sys
    here = os.path.abspath(os.path.dirname(__file__))
    version_file = os.path.join(here, 'VERSION')

    # read fallback file
    try:
        with open(version_file, 'r+') as fp:
            version_txt = fp.read().strip()
    except:
        version_txt = None

    # read git version (if available)
    try:
        version_git = (
            Popen(['git', 'describe'], stdout=PIPE, stderr=PIPE, cwd=here)
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


class _custom_develop(_develop):
    def run(self):
        _develop.run(self)
        self.execute(_post_develop, [], msg="Running post-develop task")


def _post_develop():
    from subprocess import call
    call(['bower', 'install'], cwd=HERE)


setup(
    name='occams_studies',
    version=get_version(),
    description='occams_studies',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='The YoungLabs',
    author_email='younglabs@ucsd.edu',
    url='https://github.com/younglabs/occams_studies',
    keywords='web wsgi bfg pylons pyramid',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
    cmdclass={'develop': _custom_develop},
    entry_points="""\
    [console_scripts]
    os_export = occams_studies.scripts.export:main
    """,
)
