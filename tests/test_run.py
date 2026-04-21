import json

import pytest

import powershell


def test_empty_command_should_raise_error():
    with pytest.raises(ValueError):
        powershell.run([])


def test_simple_command(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="hello")

    powershell.run(["Write-Host", "hello"])

    assert mocked_subprocess_run.call_args_list == snapshot


def test_named_string_param(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="")

    powershell.run(["Get-Service", "-Name", "myservice"])

    assert mocked_subprocess_run.call_args_list == snapshot


def test_named_numeric_param(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="")

    powershell.run(["Get-Disk", "-Number", "0"])

    assert mocked_subprocess_run.call_args_list == snapshot


def test_switch_param(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="")

    powershell.run(["Remove-Item", "C:\\Temp\\some\\file.txt", "-SomeForceParam"])

    assert mocked_subprocess_run.call_args_list == snapshot


def test_multiple_named_and_switch_params(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="")

    powershell.run(["New-Partition", "-DiskNumber", "106", "-UseMaximumSize", "-DriveLetter", "XYZ123"])

    assert mocked_subprocess_run.call_args_list == snapshot


def test_colon_syntax_named_param(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="")
    
    powershell.run(["Clear-Disk", "-SuperConfirm:$false"])

    assert mocked_subprocess_run.call_args_list == snapshot


def test_as_json_should_return_parsed_dict(mocked_subprocess_run):
    expected_stdout = {"Name": "foo", "Value": 42}
    mocked_subprocess_run.set_result(stdout=json.dumps(expected_stdout))

    result = powershell.run(["Get-SomeDict"], as_json=True)

    assert result == expected_stdout


def test_as_json_should_return_parsed_list(mocked_subprocess_run):
    expected_stdout = [{"Name": "foo"}, {"Name": "bar"}]
    mocked_subprocess_run.set_result(stdout=json.dumps(expected_stdout))

    result = powershell.run(["Get-SomeList"], as_json=True)

    assert result == expected_stdout


def test_as_json_should_returns_none_on_empty_stdout(mocked_subprocess_run):
    mocked_subprocess_run.set_result(stdout="")

    result = powershell.run(["Get-Something"], as_json=True)

    assert result is None


def test_as_json_should_raise_an_error_on_invalid_json(mocked_subprocess_run):
    mocked_subprocess_run.set_result(stdout="not valid json")

    with pytest.raises(powershell.PowerShellError):
        powershell.run(["Get-Something"], as_json=True)


def test_non_zero_return_code_should_raise_an_error(mocked_subprocess_run):
    mocked_subprocess_run.set_result(stdout="", returncode=1)

    with pytest.raises(powershell.PowerShellError):
        powershell.run(["Some-Command"], raise_on_error=True)


def test_non_zero_return_code_should_ignore_it_if_rais_on_error_is_set_to_false(mocked_subprocess_run):
    mocked_subprocess_run.set_result(stdout="some output", returncode=1)

    result = powershell.run(["Some-Command"], raise_on_error=False)

    assert result == "some output"


def test_powershell_error_should_expose_result(mocked_subprocess_run):
    stdout = "some stdout"
    stderr = "some stderr"
    returncode = 426
    mocked_subprocess_run.set_result(stdout=stdout, stderr=stderr, returncode=returncode)

    with pytest.raises(powershell.PowerShellError) as exc_info:
        powershell.run(["Some-Command"])

    assert exc_info.value.result.stdout == stdout
    assert exc_info.value.result.stderr == stderr
    assert exc_info.value.result.returncode == returncode

def test_custom_timeout(mocked_subprocess_run):
    mocked_subprocess_run.set_result(stdout="")

    powershell.run(["Write-Host", "hello"], timeout=120)

    assert mocked_subprocess_run.call_args.kwargs["timeout"] == 120


def test_custom_pwsh_path(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="")

    powershell.run(["Write-Host", "hello"], pwsh_path="pwsh")

    assert mocked_subprocess_run.call_args_list == snapshot


def test_single_quote_escaping_in_positional_arg(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="")

    powershell.run(["Write-Host", "it's a test"])

    assert mocked_subprocess_run.call_args_list == snapshot


def test_single_quote_escaping_in_named_param(mocked_subprocess_run, snapshot):
    mocked_subprocess_run.set_result(stdout="")

    powershell.run(["Get-Service", "-Name", "service'name"])

    assert mocked_subprocess_run.call_args_list == snapshot


def test_stdout_should_be_stripped(mocked_subprocess_run):
    mocked_subprocess_run.set_result(stdout="  hello world\n")

    result = powershell.run(["Write-Host", "hello world"])

    assert result == "hello world"
