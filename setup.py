import os
import versioneer

versioneer.VCS = 'git'
versioneer.versionfile_source = 'BigStash/version.py'
versioneer.versionfile_build = 'BigStash/version.py'
versioneer.tag_prefix = ''
versioneer.parentdir_prefix = 'bigstash-'
from setuptools import setup, find_packages


def pep386adapt(version):
    if version is not None and '-' in version:
        # adapt git-describe version to be in line with PEP 386
        parts = version.split('-')
        parts[-2] = 'post'+parts[-2]
        version = '.'.join(parts[:-1])
    return version

install_requires = [
    'six>=1.9, <2.0',
    'requests>=2.5.1, <2.6',
    'retrying',
    'wrapt',
    'boto3',
    'cached_property',
    'docopt'
]


dev_requires = [
    'flake8',
]


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''


setup(version=pep386adapt(versioneer.get_version()),
      name="bigstash",
      description=read('DESCRIPTION'),
      long_description=read('README.rst'),
      url='http://github.com/longaccess/bigstash-python/',
      license='Apache',
      packages=find_packages(exclude=['features*', '*.t']),
      tests_require=['testtools'],
      test_suite="BigStash.t",
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Information Technology',
          'Natural Language :: English',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Archiving',
          'Topic :: Utilities',
          ],
      cmdclass=versioneer.get_cmdclass(),
      install_requires=install_requires,
      extras_require={
          'dev': dev_requires,
          },
      entry_points={
          'console_scripts': ['bgst=BigStash.upload:main']
          }
      )
