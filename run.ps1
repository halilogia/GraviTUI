# GraviTUI baslatici (Interactive Hub & CLI Launcher)
param([string]$App = "")

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$py = (Get-Command py -ErrorAction SilentlyContinue)
$pyArgs = @()
if ($py) { $pyExe = $py.Source; $pyArgs = @("-3") }
else { $pyExe = (Get-Command python -ErrorAction Stop).Source }

Push-Location -LiteralPath $root
try {
    if ($App -in @("t", "test")) {
        & $pyExe @pyArgs -m unittest discover -s tests -t .
        exit $LASTEXITCODE
    }

    $targetArgs = if ($App) { @("run_hub.py", $App) } else { @("run_hub.py") }

    # Windows Terminal varsa ve zaten icinde degilsek yeni sekmede/pencerede ac
    $wt = Get-Command wt -ErrorAction SilentlyContinue
    if ($wt -and -not $env:WT_SESSION) {
        $inner = "& '$pyExe' $($pyArgs -join ' ') " + ($targetArgs -join ' ')
        Start-Process -FilePath $wt.Source -ArgumentList @(
            "-d", $root, "--title", "GraviTUI Hub", "pwsh", "-NoLogo", "-Command", $inner)
    }
    else {
        & $pyExe @pyArgs @targetArgs
    }
}
finally {
    Pop-Location
}
