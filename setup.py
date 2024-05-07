from setuptools import setup, find_packages

setup(
    name='ZeitfreiOauth',
    version='0.0.4',
    packages=find_packages(),
    install_requires=[
        'requests',
        'aiohttp'
    ],
    author='Evanlau',
    author_email='sl30608@gmail.com',
    description='一個用於與ZeitFrei Discord OAuth授權API互動的Python函式庫',
    url='https://github.com/ZeltFrei/EvanlauOauthServer'
)
