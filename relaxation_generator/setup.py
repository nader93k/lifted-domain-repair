# coding=utf-8

import os

from setuptools import setup, find_packages


from distutils.core import setup


here = os.path.abspath(os.path.dirname(__file__))


def get_description():
    from codecs import open
    # Get the long description from the README file
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        return f.read()


def main():
    setup(
        name='delete-free-asp-planner',
        version=0.1,
        description='A simple planner for delete-free problems',
        long_description=get_description(),
        url='',
        author='Augusto Blaas Corrêa and Guillem Francès',
        author_email='-',

        keywords='planning logic STRIPS',
        classifiers=[
            'Development Status :: 3 - Alpha',

            'Intended Audience :: Science/Research',
            'Topic :: Scientific/Engineering :: Artificial Intelligence',

            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ],

        packages=find_packages('src'),  # include all packages under src
        package_dir={'': 'src'},  # tell distutils packages are under src

        install_requires=[
            'setuptools',
            'tarski==0.4.0'
        ],

        extras_require={
            'dev': ['pytest', 'tox'],
            'test': ['pytest', 'tox'],
        },
    )


if __name__ == '__main__':
    main()
