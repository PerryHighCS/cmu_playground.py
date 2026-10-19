# Soft-reboot the board and print its serial output for a few seconds.
#   powershell -ExecutionPolicy Bypass -File tools\serial.ps1 -Seconds 10 -Port COM68
param([int]$Seconds = 8, [string]$Port = "COM68")
$p = New-Object System.IO.Ports.SerialPort $Port, 115200
$p.ReadTimeout = 200; $p.DtrEnable = $true
$p.Open()
$p.Write([string][char]3); Start-Sleep -Milliseconds 300
$p.Write([string][char]4)
$end = (Get-Date).AddSeconds($Seconds)
while ((Get-Date) -lt $end) {
  try { $s = $p.ReadExisting(); if ($s) { [Console]::Write($s) } } catch {}
  Start-Sleep -Milliseconds 100
}
$p.Write([string][char]3); Start-Sleep -Milliseconds 200
try { [Console]::Write($p.ReadExisting()) } catch {}
$p.Close()
