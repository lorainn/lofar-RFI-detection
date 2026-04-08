try:
    from importlib import metadata
except ImportError:  # for Python<3.8
    import importlib_metadata as metadata

# Manually set the version to avoid PackageNotFoundError
__version__ = "0.1.0"
