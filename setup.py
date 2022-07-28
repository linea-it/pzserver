from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pz-server-lib",
    packages=find_packages(include=["pz-server-lib"]),
    version="0.1.0",
    description="Python library to access the Photo-z Server database"
    " hosted by the Brazilian LSST IDAC at LIneA. "
    license="MIT",
    python_requires=">=3.8",
    setup_requires=["pytest-runner", "numpy", "astropy"],
    install_requires=[
        "sqlalchemy>=1.4.25",
        "psycopg2-binary>=2.9.1",
        "numpy>=1.19.4",
        "pandas>=1.2.0",
        "requests>=2.23.0",
        "astropy>=5.0.0",
    ],
    tests_require=["pytest==4.4.1", "astropy"],
    test_suite="tests",
    # Long description of your library
    long_description=long_description,
    long_description_content_type="text/markdown",
    # Either the link to your github or to your website
    url="https://github.com/linea-it/pz-server-lib",
    # Link from which the project can be downloaded
    # download_url='https://github.com/linea-it/pz-server-lib/archive/refs/tags/v0.1.0-alpha.tar.gz',
)