# win.ps1 - list top-level windows whose title contains -match (default SDVMARK = a tab title you set), optionally bring
# the first one to the front (-front). Prints: hwnd vis= min= rect= title. The hwnd feeds rec.py --hwnd / SDV_HWND.
# STATUS: TESTED (27/09 ProfitBase capture; copied unchanged).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture/win.ps1 -match 'Google Chrome' [-front]
param([string]$match='SDVMARK',[switch]$front)
Add-Type @'
using System;using System.Runtime.InteropServices;using System.Text;
public class WE{public delegate bool CB(IntPtr h,IntPtr l);
[DllImport("user32.dll")]public static extern bool EnumWindows(CB cb,IntPtr l);
[DllImport("user32.dll")]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);
[DllImport("user32.dll")]public static extern bool IsWindowVisible(IntPtr h);
[DllImport("user32.dll")]public static extern bool IsIconic(IntPtr h);
[DllImport("user32.dll")]public static extern bool ShowWindow(IntPtr h,int c);
[DllImport("user32.dll")]public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")]public static extern bool GetWindowRect(IntPtr h,out R r);public struct R{public int L,T,Ri,B;}}
'@
$out=@(); [WE]::EnumWindows({param($h,$l) $sb=New-Object System.Text.StringBuilder 256; [WE]::GetWindowText($h,$sb,256)|Out-Null; if($sb.ToString() -like "*$match*"){ $r=New-Object WE+R; [WE]::GetWindowRect($h,[ref]$r)|Out-Null; $script:out += "$h vis=$([WE]::IsWindowVisible($h)) min=$([WE]::IsIconic($h)) rect=$($r.L),$($r.T),$($r.Ri),$($r.B) $sb" }; $true},[IntPtr]::Zero)|Out-Null
$out
if($front -and $out.Count -gt 0){ $h=[IntPtr]([long]($out[0].Split(' ')[0])); [WE]::ShowWindow($h,9)|Out-Null; [WE]::SetForegroundWindow($h)|Out-Null; "fronted $h" }
