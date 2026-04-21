import pytest

import powershell


def test_empty_command_should_raise_error():
    with pytest.raises(ValueError):
        powershell.run([])

def test_simple_command(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="hello")
    
    powershell.run(["Write-Host", "hello"])
    
    assert mocked_subprocess_run.call_args_list == snapshot
