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


class PowerShellError(RuntimeError):
    def __init__(self, message: str, result: PowerShellResult):
        super().__init__(message)
        self.result = result


def run(
        ps_command: Sequence[str],
        *,
        as_json: bool = False,
        json_depth: int = 5,
        timeout: Optional[float] = 60,
        pwsh_path: str = "powershell.exe",
        raise_on_error: bool = True,
) -> Union[str, dict, list]:
    """
    TODO 
    examples:
    run_powershell(  # Required to clear the disk, otherwise it will be offline
            ["Initialize-Disk", "-Number", str(output_disk_number), "-PartitionStyle", str(partition_type.value)],
            raise_on_error=False,
        )

    x = run_powershell(["Get-Service", "-Name", f"{CYBEE_WINDOWS_SERVICE_NAME}*"], as_json=True)
    """

    if not ps_command:
        raise ValueError("ps_command must be non-empty")
    logger.debug("Running powershell command : %s", " ".join(ps_command))  # TODO log full edited command 

    def ps_single_quote(s: str) -> str:
        return "'" + s.replace("'", "''") + "'"

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
    ps_cmd = ps_single_quote(cmd)

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
                # (e.g. Get-Disk -Number expects UInt32)
                if v.isdigit():
                    entries.append(f"{k} = {int(v)}")
                else:
                    entries.append(f"{k} = {ps_single_quote(v)}")
        ps_params = "@{ " + "; ".join(entries) + " }"
    else:
        ps_params = "@{}"

    # Positional args array
    if positional:
        ps_pos = "@(" + ", ".join(ps_single_quote(p) for p in positional) + ")"
    else:
        ps_pos = "@()"

    invoke = (
        f"$ProgressPreference='SilentlyContinue'; "
        f"$cmd={ps_cmd}; "
        f"$params={ps_params}; "
        f"$pos={ps_pos}; "
        f"& $cmd @params @pos"
    )

    if as_json:
        script = f"{invoke} | ConvertTo-Json -Depth {int(json_depth)}"
    else:
        script = invoke

    args = [
        pwsh_path,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]

    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )

    result = PowerShellResult(
        command=args,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )

    if raise_on_error and result.returncode != 0:
        raise PowerShellError(f"PowerShell failed ({result.returncode})", result)

    out = result.stdout.strip()

    if not as_json:
        return out

    if out == "":
        return None

    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise PowerShellError(f"JSON parse failed: {e}", result)
