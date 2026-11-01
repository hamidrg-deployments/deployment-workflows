"""Run with python tests/check_config.py; requires Bash (Git Bash on Windows)."""

import os
from pathlib import Path
import shutil
import subprocess
import textwrap


root = Path(__file__).resolve().parents[1]
bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
expression = "$" + "{{ "
for name in ("deploy-rsync.yml", "deploy-ref-rsync.yml", "snapshot-rsync.yml", "revert-rsync.yml"):
    source = (root / ".github/workflows" / name).read_text()
    assert "DEPLOY_PATH: " + expression + "vars.DEPLOY_PATH || inputs.deploy_path }}" in source
    assert expression + "vars.DEPLOY_PATH || inputs.deploy_path }}" in source.split("concurrency:", 1)[1].split("jobs:", 1)[0]
    assert "      deploy_path:\n        description: Fallback absolute server directory when DEPLOY_PATH is unset\n        required: false" in source
    for legacy, inherited in (("ssh_private_key", "SERVER_SSH_KEY"), ("ssh_known_hosts", "SERVER_KNOWN_HOSTS")):
        assert expression + f"secrets.{legacy} || secrets.{inherited}" + " }}" in source
        for secret in (legacy, inherited):
            assert f"      {secret}:\n        required: false" in source

    section = source.split("      - name: Configure SSH\n", 1)[1]
    validation = textwrap.dedent(section.split("        run: |\n", 1)[1].split('          install -m 700 -d', 1)[0])
    valid = dict(os.environ, DEPLOY_HOST="example.invalid", DEPLOY_USER="deploy", DEPLOY_PATH="/srv/app", SSH_PRIVATE_KEY="fake-key", SSH_KNOWN_HOSTS="fake-hosts")
    cases = [(None, None, 0)]
    cases += [(setting, "", 1) for setting in ("DEPLOY_HOST", "DEPLOY_USER", "DEPLOY_PATH", "SSH_PRIVATE_KEY", "SSH_KNOWN_HOSTS")]
    cases += [("DEPLOY_PATH", path, 1) for path in ("/", "relative")]
    for setting, value, expected in cases:
        environment = valid.copy()
        if setting:
            environment[setting] = value
        result = subprocess.run([bash, "-s"], input=validation, text=True, env=environment, capture_output=True)
        assert result.returncode == expected, (name, setting, result.stderr)

print("Passed: variable paths, legacy/inherited secret contracts, and validation for all four workflows")
