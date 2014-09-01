# -*- coding: utf-8 -*-
'''
This contrib extension, sphinxcontrib.httpdomain provides a Sphinx
domain for describing RESTful HTTP APIs.
'''

from setuptools import setup, find_packages


setup(
    name='sphinxcontrib-autoflask',
    version='0.1.0',
    url='https://github.com/felipeblassioli/sphinx_autoflask',
    license='BSD',
    author='Felipe Blassioli',
    author_email='felipeblassioli@gmail.com',
    description='Sphinx domain for HTTP APIs',
    long_description=__doc__,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Sphinx >= 1.0',
        'six'
    ],
    namespace_packages=['sphinxcontrib'],
)
