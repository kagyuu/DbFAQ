def test_packages_importable():
    import dbfaq_api.config
    import dbfaq_api.log
    import dbfaq_api.oracle  # noqa: F401
