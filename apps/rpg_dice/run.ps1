# One-click launcher: opens RPG Dice TUI in an isolated Windows Terminal window
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir

$py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } elseif (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { $null }
if (-not $py) {
    Write-Error 'Python 3 was not found on PATH. Please install Python 3.'
    pause
    exit 1
}

# -w new ensures it opens in a completely separate window, leaving background TUIs untouched
if (Get-Command wt.exe -ErrorAction SilentlyContinue) {
    Start-Process wt.exe -ArgumentList @('-w', 'new', '--size', '120,36', '-d', "`"$dir`"", $py, 'main.py')
} else {
    Start-Process cmd.exe -ArgumentList @('/c', "$py main.py")
}
