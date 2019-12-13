from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="caluma-client",
    version="0.0.1",
    description="Client library for Caluma",
    long_description=long_description,
    long_description_content_type="text/markup",
    url="https://projectcaluma.github.io/",
    install_requires=[
        "requests",
    ],
    packages=find_packages(),
)
