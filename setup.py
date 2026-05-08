from setuptools import setup, find_packages

setup(
    name="pos",
    version="1.0.0",
    packages=find_packages(),
    py_modules=["cli", "main"],
    install_requires=[
        "mysql-connector-python>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "pos=cli:main",
        ],
    },
)
