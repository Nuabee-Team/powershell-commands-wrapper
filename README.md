# powershell-commands-wrapper

A Python wrapper around `subprocess` to run PowerShell commands and retrieve
their outputs.

> **Tested on Windows only.** The package may work on Linux with PowerShell
> (`pwsh`) installed, but this is not tested.

## Installation

```bash
pip install powershell-commands-wrapper
```

## Usage

Commands are expressed as a list of strings — the first element is the cmdlet
name, followed by its arguments.

```python
import powershell

stdout = powershell.run(["Write-Host", "hello world"])
# stdout = "hello world"
```

### JSON output

Pass `as_json=True` to retrieve the output as a JSON object:

```python
import powershell

disks = powershell.run(["Get-Disk"], as_json=True)
# disks = [{"Size": 10737418240, "DiskNumber": 1, "PartitionStyle": "MBR", ...}]
```

### Error handling

By default a `powershell.PowerShellError` is raised when the exit code is
non-zero. Set `raise_on_error=False` to suppress this:

```python
try:
    powershell.run(["Some-Command"])
except powershell.PowerShellError as e:
    print(e.result.returncode)
    print(e.result.stderr)

# Or ignore errors entirely
powershell.run(["Some-Command"], raise_on_error=False)
```

## About Nuabee

This package is maintained by [Nuabee](https://nuabee.fr), a company that helps
businesses improve their IT resiliency.
