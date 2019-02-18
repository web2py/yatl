import ast
import re

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('yatl/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))
print(long_description)

setuptools.setup(
    name="yatl",
    version=version,
    url='https://github.com/web2py/yatl',
    license='BSD',
    author='Massimo Di Pierro',
    author_email='massimo.dipierro@gmail.com',
    maintainer='Massimo Di Pierro',
    maintainer_email='massimo.dipierro@gmail.com',
    description='Yet Another Template Language',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['yatl'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: HTML'
    ],
)
