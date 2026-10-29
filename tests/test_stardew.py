"""Stardew Valley TUI testlerini `unittest discover -s tests` altında da çalıştırır."""
from apps.stardew_valley import test_stardew, test_stardew_game


def load_tests(loader, tests, pattern):
    suite = loader.loadTestsFromModule(test_stardew)
    suite.addTests(loader.loadTestsFromModule(test_stardew_game))
    return suite
