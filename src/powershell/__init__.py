import json
import logging
import subprocess
from dataclasses import dataclass
from typing import List, Sequence, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class PowerShellResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str


class PowerShellError(Exception):
    def __init__(self, message: str, result: PowerShellResult):
        super().__init__(message)
        self.result = result

def _ps_single_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"

def _format_command(ps_command: Sequence[str]) -> str:
    cmd = ps_command[0]
    tokens = list(ps_command[1:])

    # Parse tokens into:
    # - named params hashtable: @{ Param = Value; Switch = $true }
    # - positional args array: @('pos1', 'pos2')
    named: List[tuple[str, Optional[str]]] = []
    positional: List[str] = []

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("-") and len(t) > 1:
            name = t.lstrip("-")
            # Switch param if next token is absent or looks like another param
            if i + 1 >= len(tokens) or (tokens[i + 1].startswith("-") and len(tokens[i + 1]) > 1):
                named.append((name, None))  # switch
                i += 1
            else:
                val = tokens[i + 1]
                named.append((name, val))
                i += 2
        else:
            positional.append(t)
            i += 1

    # Build PowerShell script
    ps_cmd = _ps_single_quote(cmd)

    # Named params hashtable
    if named:
        entries = []
        for k, v in named:
            if ":" in k:
                confirm_cmd, confirm_val = k.split(":")
                combined = f"{confirm_cmd} = {confirm_val}"
                entries.append(combined)
                continue
            if v is None:
                entries.append(f"{k} = $true")
            else:
                # Keep numbers as numbers when possible for better binding
                # (e.g., Get-Disk -Number expects UInt32)
                if v.isdigit():
                    entries.append(f"{k} = {int(v)}")
                else:
                    entries.append(f"{k} = {_ps_single_quote(v)}")
        ps_params = "@{ " + "; ".join(entries) + " }"
    else:
        ps_params = "@{}"

    # Positional args array
    if positional:
        ps_pos = "@(" + ", ".join(_ps_single_quote(p) for p in positional) + ")"
    else:
        ps_pos = "@()"

    invoke = (
        f"$ProgressPreference='SilentlyContinue'; "
        f"$cmd={ps_cmd}; "
        f"$params={ps_params}; "
        f"$pos={ps_pos}; "
        f"& $cmd @params @pos"
    )
    return invoke

def _parse_result_as_json(result: PowerShellResult) -> Union[dict, list, None]:
    if result.stdout == "":
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise PowerShellError(f"Invalid JSON returned", result) from e

def run(
        command: Sequence[str],
        *,
        as_json: bool = False,
        json_depth: int = 5,
        timeout: Optional[float] = 60,
        pwsh_path: str = "powershell.exe",
        raise_on_error: bool = True,
) -> Union[str, dict, list, None]:
    """Executes a PowerShell command

    Parameters:
        command (Sequence[str]): A sequence of strings representing the PowerShell command 
            and its arguments. Must be non-empty.
        as_json (bool, optional): If True, parses the PowerShell output as JSON. Defaults to False.
        json_depth (int, optional): Specifies the depth for JSON parsing when as_json is True. 
            Defaults to 5.
        timeout (Optional[float], optional): Maximum time, in seconds, to wait for the command 
            to complete. Defaults to 60.
        pwsh_path (str, optional): Path to the PowerShell executable. Defaults to "powershell.exe".
        raise_on_error (bool, optional): If True, raises an exception when the PowerShell 
            command fails. Defaults to True.

    Examples:
        >>> run_powershell(
        >>>      ["Write-Host", "hello world"],
        >>>      raise_on_error=False,
        >>> )
        ...
        >>> run_powershell(
        >>>      ["Get-Process", "powershell"],
        >>>      as_json=True,
        >>> )
        {'Name': 'Power', 'CanStop': False, } # more omitted
        >>> x = run_powershell(["Write-Host", "hello world"], as_json=True, raise_on_error=False)
        PowerShellError: JSON parse failed: Expecting value: line 1 column 1 (char 0)
    """
    if not command:
        raise ValueError("command must be non-empty")
    logger.debug("initial args: %s", " ".join(command))

    formatted_command = _format_command(command)
    if as_json:
        formatted_command += f" | ConvertTo-Json -Depth {int(json_depth)}"

    logger.info("Running powershell command %s", " ".join(formatted_command))
    args = [
        pwsh_path,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        formatted_command,
    ]

    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )
    logger.debug("Return code %s", completed.returncode)

    result = PowerShellResult(
        command=args,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr,
    )

    if result.returncode != 0 and raise_on_error:
        raise PowerShellError(f"PowerShell failed ({result.returncode})", result)

    if as_json:
        return _parse_result_as_json(result)
    return result.stdout
    

    
