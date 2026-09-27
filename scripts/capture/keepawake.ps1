# keepawake.ps1 - keep the display on during a capture session (SetThreadExecutionState, an app-level request like a video
# player; no power settings are changed). Ends after -Minutes, when the stop file appears, or when the process is killed.
# STATUS: SMOKE-TESTED (27/09 version had 150 min and $PSScriptRoot\STOP_KEEPAWAKE hard-coded; now params; re-run with -Minutes 0)
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture/keepawake.ps1 [-Minutes 150] [-StopFile footage\STOP_KEEPAWAKE]
param([int]$Minutes = 150, [string]$StopFile = (Join-Path (Get-Location) 'STOP_KEEPAWAKE'))
Add-Type 'using System;using System.Runtime.InteropServices;public class KA{[DllImport("kernel32.dll")]public static extern uint SetThreadExecutionState(uint f);}'
$ES = [uint32]'0x80000003'  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
$end = (Get-Date).AddMinutes($Minutes)
while ((Get-Date) -lt $end -and -not (Test-Path $StopFile)) { [KA]::SetThreadExecutionState($ES) | Out-Null; Start-Sleep -Seconds 20 }
[KA]::SetThreadExecutionState([uint32]'0x80000000') | Out-Null
"keepawake done (minutes=$Minutes stopfile=$StopFile)"
