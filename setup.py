#!/usr/bin/env python
from setuptools import setup, find_packages
from os.path import dirname, join

setup(
    name='django-debugtools',
    version='0.9.1',
    license='Apache License, Version 2.0',

    description='A toolbox of small utilities to assist Django development',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),

    author='Diederik van der Boor',
    author_email='opensource@edoburu.nl',

    url='https://github.com/edoburu/django-debugtools',
    download_url='https://github.com/edoburu/django-debugtools/zipball/master',

    packages=find_packages(exclude=('example*',)),
    include_package_data=True,

    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ]
)
