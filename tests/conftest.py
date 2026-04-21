from functools import partial
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def mocked_subprocess_run():
    with patch("subprocess.run") as mocked:
        mocked.set_result.side_effect = partial(fake_subprocess_result, mocked)
        yield mocked


def fake_subprocess_result(mocked_subprocess_run, stdout, stderr="", returncode=0):
    """Helper to set the result of the mocked subprocess.run"""
    mocked_subprocess_run.return_value = MagicMock(
        stdout=stdout, stderr=stderr, returncode=returncode
    )
