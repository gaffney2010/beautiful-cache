from setuptools import setup

setup(
    name="beautifulcache",
    description="Caching Wrapper for BeautifulSoup",
    author="T.J. Gaffney",
    packages=["beautifulcache"],
    version="2.0.0",
    install_requires=[
        "beautifulsoup4==4.11.1",
    ],
)
