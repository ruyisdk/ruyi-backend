from contextlib import AbstractContextManager
from importlib import resources
import pathlib

import pytest


class RuyiFileFixtureFactory:
    def path(self, *frags: str) -> AbstractContextManager[pathlib.Path]:
        return resources.as_file(resources.files(None).joinpath(*frags))


@pytest.fixture
def ruyi_file() -> RuyiFileFixtureFactory:
    return RuyiFileFixtureFactory()
