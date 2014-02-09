#!/usr/bin/env python

from distutils.core import setup
import os
import imp

#TODO:
# Add docs
# Add logging.conf
# Add cron
# Add supervisord


def main():
    data_files = (
        non_python_files(os.path.join('www', 'css')) +
        non_python_files(os.path.join('www', 'images')) +
        non_python_files(os.path.join('www', 'scripts')) +
        non_python_files(os.path.join('www', 'templates'))
        )

    conf_files = ([("teleinfo", ["conf_prod/logging_teleinfo.conf"]),
                  ("pysolarmax", ["conf_prod/logging_pysolarmax.conf"]),
                  ("/etc/cron.d", ["conf_prod/pysolarmax.cron"]),
                  ("/etc/supervisor/conf.d", ["conf_prod/charts.conf"]),
                  ("data", ["data/Placeholder.txt"])
         ])
    #conf_files = ("teleinfo", "conf_prod/logging_teleinfo.conf")
    
    setup(name='PySolarmax',
          version='0.2',
          description='Python Solarmax monitoring',
          author='bonzai133',
          author_email='bonzai133@sourceforge.net',
          url='',
          packages=['pysolarmax', 'teleinfo', 'www'],
          data_files=data_files + conf_files,
         )


def non_python_files(path):
    """ Return all non-python-file filenames in path """
    result = []
    all_results = []
    module_suffixes = [info[0] for info in imp.get_suffixes()]
    ignore_dirs = ['.svn', 'cvs']
    for item in os.listdir(path):
        name = os.path.join(path, item)
        if (
            os.path.isfile(name) and
            os.path.splitext(item)[1] not in module_suffixes
            ):
            result.append(name)
        elif os.path.isdir(name) and item.lower() not in ignore_dirs:
            all_results.extend(non_python_files(name))
    if result:
        all_results.append((path, result))
    return all_results


if __name__ == "__main__":
    main()
