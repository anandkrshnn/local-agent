from setuptools import setup, find_packages

setup(
    name="localagent",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "local-agent=localagent.cli:main",
        ],
    },
)
