#!/usr/bin/env python

from distutils.core import setup


#===============================================================================
# main
#===============================================================================
def main():
    setup(
        name='PyTeleinfo',
        version='1.1',
        description='Python Teleinfo monitoring',
        author='bonzai133',
        author_email='bonzai133@sourceforge.net',
        url='http://sourceforge.net/projects/pysolarmax/',
        scripts=['teleinfo/teleinfo.py',
                 'teleinfo/teleinfo_store.py'],
    )


#===============================================================================
# __main__
#===============================================================================
if __name__ == "__main__":
    main()
