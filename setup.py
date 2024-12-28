from setuptools import setup, find_packages

setup(
    name="lifted-white-plan-domain-repair",
    version="0.1",
    packages=find_packages(exclude=["tests*", "debug*", "exp_logs*", "documentation*"]),
)