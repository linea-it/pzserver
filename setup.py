from setuptools import find_packages, setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="pz-server-lib",
    packages=find_packages(include=["pz_server"]),
    version="0.1.5.dev2",
    description=(
        "Python library to access the Photo-z Server database"
        " hosted by the Brazilian LSST IDAC at LIneA. "
    ),
    license="MIT",
    python_requires=">=3.9, <4",
    setup_requires=["pytest-runner", "numpy", "astropy"],
    install_requires=[
        "numpy>=1.19.4",
        "pandas>=1.2.0",
        "requests>=2.23.0",
        "astropy>=5.0.0",
        "matplotlib>=3.6.0",
        "tables_io >=0.7.9",
        "Jinja2>=3.1.2",
        "ipython>=8.5.0"
    ],
    # tests_require=["pytest==4.4.1", "astropy"],  #TODO
    # test_suite="tests",  #TODO
    # Long description of your library
    long_description=long_description,
    long_description_content_type="text/markdown",
    # Either the link to your github or to your website
    url="https://github.com/linea-it/pz-server-lib",
    # Link from which the project can be downloaded
    # download_url='https://github.com/linea-it/pz-server-lib/archive/refs/tags/v0.1.0-alpha.tar.gz',
)
