from setuptools import setup, find_packages

with open("README.md","r") as f:
    long_description = f.read()

setup(
    name="gym_risk",
    version="0.0.6",
    install_requires=["gym"],
    author="Léo Andéol",
    author_email="leo.andeol@gmail.com",
    description="An OpenAI Gym wrapper for the Risk game",
    long_description=long_description,
    url="https://github.com/leoandeol/gym-risk/",
    packages=find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
