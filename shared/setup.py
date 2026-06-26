from setuptools import find_packages, setup

setup(
    name="sevlens-shared",
    version="0.1.0",
    description="Shared SevLens contracts, data helpers, and seed content",
    packages=find_packages(include=["shared", "shared.*"]),
    include_package_data=True,
)
