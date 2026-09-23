def test_backend_imports():
    import app.main
    import app.models
    assert app.main.app.title == "CAT Operator Copilot API"
