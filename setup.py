from setuptools import setup

setup(
    name="beautiful-cache",
    description="Caching Wrapper for BeautifulSoup",
    author="T.J. Gaffney",
    package_dir={"": "src"},
    install_requires=[
        "attrs==21.4.0",
        "beautifulsoup4==4.11.1",
        "lxml==4.8.0",
        "mysql-connector-python==8.0.28",
        "overload==1.1",
        "pandas==1.4.2",
        "PyYAML==6.0",
        "retrying==1.3.3",
        "selenium==4.1.3",
        "tabulate==0.8.9",
    ]
)
