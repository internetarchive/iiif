import unittest
import warnings


class IIIFTestCase(unittest.TestCase):
    """Base class for all tests.

    The filter is applied here rather than at the top of a test file because
    `python -m unittest` resets warning filters just before running the tests.
    """

    def run(self, result=None):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Pydantic serializer warnings",
                category=UserWarning,
            )
            return super().run(result)
