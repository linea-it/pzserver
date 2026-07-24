import pzserver


def test_version():
    """Check to see that we can get the package version"""
    assert pzserver.__version__ is not None
