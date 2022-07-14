from setuptools import setup

setup(
    name="beautifulcache",
    description="Caching Wrapper for BeautifulSoup",
    author="T.J. Gaffney",
    packages=["beautifulcache"],
    version="1.0.3",
    install_requires=[
        "attrs==21.4.0",
        "beautifulsoup4==4.11.1",
        "lxml==4.8.0",
        "overload==1.1",
        "pandas==1.4.2",
        "PyYAML==6.0",
        "retrying==1.3.3",
        "selenium<4.0.0",
        "tabulate==0.8.9",
    ],
)
