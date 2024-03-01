from setuptools import setup, find_packages

setup(
    name='enhanced_md',
    version='0.1',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='A package to enhance the markdown language',
    author='Pau Tarragó Navarro & Xavier-Andoni Tibau Alberdi',
    author_email="p.tarragonavarra@gmail.com"
)
