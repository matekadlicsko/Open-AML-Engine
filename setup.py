# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

from setuptools import setup, find_packages

setup(
    name="aml",
    install_requires=["cffi", "numpy"],
    packages=find_packages(),
    package_data={'': ['aml_fast/*.so']},
    include_package_data=True,
)
