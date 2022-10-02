#!/usr/bin/env python

from distutils.core import setup


#===============================================================================
# main
# Will be installed in /usr/local/bin
# Service must be in /etc/systemd/system/multi-user.target.wants/pyteleinfo.service
#===============================================================================
def main():
    setup(
        name='PyTeleinfo',
        version='2.0',
        description='Python Teleinfo monitoring',
        author='bonzai133',
        author_email='bonzai133@sourceforge.net',
        url='https://github.com/bonzai133/PiAtHome',
        scripts=['teleinfo/teleinfo.py',
                 'teleinfo/teleinfo_store.py'],
    )


#===============================================================================
# __main__
#===============================================================================
if __name__ == "__main__":
    main()
