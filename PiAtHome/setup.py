#!/usr/bin/env python

from distutils.core import setup
import os
import imp


#===============================================================================
# main
#===============================================================================
def main():
    data_files = (
        non_python_files(os.path.join('piathome', 'css')) +
        non_python_files(os.path.join('piathome', 'images')) +
        non_python_files(os.path.join('piathome', 'scripts')) +
        non_python_files(os.path.join('piathome', 'templates'))
    )

    conf_files = ([
        ("config", ["conf_prod/logging_teleinfo.conf",
                         "conf_prod/logging_pysolarmax.conf",
                         "conf_prod/apache2/piathome.conf",
                         "conf_prod/apache2/piathome_ssl.conf"]),
        ("config", ["conf_prod/cron_piathome",
                    "conf_prod/cron_backup"]),
        ("/etc/apache2/sites-available", ["conf_prod/apache2/piathome.conf",
                                          "conf_prod/apache2/piathome_ssl.conf"]),
        #("/etc/cron.d", ["conf_prod/cron_piathome"]),
        ("data", ["data/Placeholder.txt"]),
        #TODO: chown www-data or chmod
        #("data/.cache", ["data/Placeholder.txt"]),
        #("log", ["data/Placeholder.txt"]),
        #("piathome/users.txt", ["users.txt"]),
    ])
        
    setup(
        name='PiAtHome',
        version='1.3',
        description='PiAtHome web site',
        author='bonzai133',
        author_email='bonzai133@sourceforge.net',
        url='http://sourceforge.net/projects/pysolarmax/',
        packages=['piathome'],
        scripts=['bin/Charts.wsgi', 'bin/Start_server.py', 'bin/backup.sh'],
        data_files=data_files + conf_files
    )


def non_python_files(path):
    """ Return all non-python-file filenames in path """
    result = []
    all_results = []
    module_suffixes = [info[0] for info in imp.get_suffixes()]
    ignore_dirs = ['.svn', 'cvs']
    for item in os.listdir(path):
        name = os.path.join(path, item)
        if (os.path.isfile(name) and
                os.path.splitext(item)[1] not in module_suffixes):
            result.append(name)
        elif os.path.isdir(name) and item.lower() not in ignore_dirs:
            all_results.extend(non_python_files(name))
    if result:
        all_results.append((path, result))
    return all_results


#===============================================================================
# __main__
#===============================================================================
if __name__ == "__main__":
    main()
