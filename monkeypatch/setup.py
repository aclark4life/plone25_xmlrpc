from setuptools import setup, find_packages

setup(
    name='monkeypatch',
    packages=find_packages(),
    install_requires=[
        'collective.monkeypatcher',
    ]
)
