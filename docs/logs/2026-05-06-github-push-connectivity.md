# GitHub Push Connectivity Incident

## Summary

On 2026-05-06, pushing `feature/llm-manager` to `origin` became unreliable after previous pushes had succeeded. The local repository was healthy, but Git HTTPS transport to GitHub repeatedly failed.

## Local State

```text
branch: feature/llm-manager
remote: https://github.com/1540530942/MyTest.git
local latest commit: ea96455 Map modules on primary gateway hosts
state: ahead 1
unrelated unstaged file: camera_snapshot/gpio_ssh_bridge.out.log
```

## Errors Observed

```text
fatal: unable to access 'https://github.com/1540530942/MyTest.git/':
Failed to connect to github.com port 443 after 210xx ms: Could not connect to server

fatal: unable to access 'https://github.com/1540530942/MyTest.git/':
Recv failure: Connection was reset

error: RPC failed; curl 52 Recv failure: Connection was reset
fatal: expected flush after ref listing
```

## Diagnostics

```text
Invoke-WebRequest https://github.com -> 200
Test-NetConnection github.com -Port 443 -> intermittent false/true
Test-NetConnection github.com -Port 22 -> true
ssh -T git@github.com -> Permission denied (publickey)
gh --version -> not installed
GitHub MCP connector -> MCP startup handshake timeout
```

## Assessment

The failure is most consistent with intermittent Git HTTPS transport/network failure on this machine. It is not caused by the module route commit itself. The repository remote, branch, and commit history remain valid.

## Recovery Command

When GitHub connectivity recovers, run:

```powershell
git -c http.postBuffer=524288000 push -u origin feature/llm-manager
```

Permanent runbook:

```text
docs/github-push-troubleshooting.md
```
