# fg.ps1 - print the foreground window handle, title and rect (which window will gfxcapture see?).
# STATUS: TESTED (27/09 ProfitBase capture; copied unchanged). Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture/fg.ps1
Add-Type 'using System;using System.Runtime.InteropServices;using System.Text;public class W5{[DllImport("user32.dll")]public static extern IntPtr GetForegroundWindow();[DllImport("user32.dll")]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);[DllImport("user32.dll")]public static extern bool GetWindowRect(IntPtr h,out R r);public struct R{public int L,T,Ri,B;}}'
$h=[W5]::GetForegroundWindow(); $sb=New-Object System.Text.StringBuilder 256; [W5]::GetWindowText($h,$sb,256)|Out-Null; $r=New-Object W5+R; [W5]::GetWindowRect($h,[ref]$r)|Out-Null
"fg=$h $($sb) rect=$($r.L),$($r.T),$($r.Ri),$($r.B)"
