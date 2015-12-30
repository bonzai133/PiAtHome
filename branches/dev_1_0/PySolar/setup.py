#!/usr/bin/env python

from distutils.core import setup


#===============================================================================
# main
#===============================================================================
def main():
    setup(
        name='PySolarmax',
        version='1.0',
        description='Python Solarmax monitoring',
        author='bonzai133',
        author_email='bonzai133@sourceforge.net',
        url='http://sourceforge.net/projects/pysolarmax/',
        packages=['pysolarmax'],
    )


#===============================================================================
# __main__
#===============================================================================
if __name__ == "__main__":
    main()