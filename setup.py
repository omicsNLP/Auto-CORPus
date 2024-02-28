from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="autoCORPus",
    version='1.0.0',
    description="autoCORPus",
    py_modules=["autoCORPus"],
    package_dir={'': 'src'},
    install_requires=required
)
