# GraviTUI baslatici. Kullanim: .\run.ps1 [-Example 1..4|test]
param([string]$Example = "")

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$py = (Get-Command py -ErrorAction SilentlyContinue)
$pyArgs = @()
if ($py) { $pyExe = $py.Source; $pyArgs = @("-3") }
else { $pyExe = (Get-Command python -ErrorAction Stop).Source }

$scripts = @{
    "1" = "examples\01_hello_ratatui.py"
    "2" = "examples\02_3d_polyhedron.py"
    "3" = "examples\03_dashboard.py"
    "4" = "examples\04_office_mini.py"
}

if (-not $Example) {
    Write-Host ""
    Write-Host "  GraviTUI - ornek sec:"
    Write-Host "    1  Hello Ratatui"
    Write-Host "    2  3D Polyhedron"
    Write-Host "    3  Dashboard"
    Write-Host "    4  Office Mini"
    Write-Host "    t  Testler"
    $Example = Read-Host "  Secim [1-4/t]"
}

Push-Location -LiteralPath $root
try {
    if ($Example -in @("t", "test")) {
        & $pyExe @pyArgs -m unittest discover -s tests -t .
        exit $LASTEXITCODE
    }
    if (-not $scripts.ContainsKey($Example)) { throw "Gecersiz secim: $Example" }
    $script = $scripts[$Example]

    # Windows Terminal varsa ve zaten icinde degilsek orada ac; yol bosluklari dizi argumanla korunur
    $wt = Get-Command wt -ErrorAction SilentlyContinue
    if ($wt -and -not $env:WT_SESSION) {
        $inner = "& '$pyExe' $($pyArgs -join ' ') '$script'"
        Start-Process -FilePath $wt.Source -ArgumentList @(
            "-d", $root, "pwsh", "-NoLogo", "-Command", $inner)
    }
    else {
        & $pyExe @pyArgs $script
    }
}
finally {
    Pop-Location
}
