import os
from pip.req import parse_requirements
from setuptools import setup, find_packages



reqs = parse_requirements("requirements.txt")
install_reqs = filter(bool,[str(ir.req) for ir in reqs])


setup(
    name='fab-controller',
    author='Ben Whalley',
    author_email='benwhalley@gmail.com',
    url='http://pypi.python.org/pypi/fab-controller/',
    version="1.0a3",
    license='LICENSE.txt',
    scripts = ['bin/fab', ],
    packages=find_packages(),
    package_data={'fab-controller.static': ['*']},
    include_package_data=True,
    description='Control an FAB finger pressure stimulator device.',
    long_description=open('README.rst').read(),
    install_requires=install_reqs,
)

