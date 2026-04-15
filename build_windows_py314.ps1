$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Resolve-PythonLauncher {
    $candidates = @("3.14", "3.13", "3.12")

    foreach ($version in $candidates) {
        & py -$version --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return @{
                Version = $version
                Command = @("py", "-$version")
            }
        }
    }

    throw "Python 3.12+ not found via the Windows py launcher."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$PythonCommand,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $PythonCommand[0] $PythonCommand[1] @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $($PythonCommand -join ' ') $($Arguments -join ' ')"
    }
}

function Test-InstallQtBinding {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackageName
    )

    & .\.venv\Scripts\python.exe -m pip install $PackageName
    return $LASTEXITCODE -eq 0
}

$python = Resolve-PythonLauncher
Write-Host "Using Python $($python.Version)"

Invoke-Python -PythonCommand $python.Command -Arguments @("-m", "venv", ".venv")
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip."
}

& .\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install base requirements."
}

$qtBinding = $null
if (Test-InstallQtBinding -PackageName "PyQt5") {
    $qtBinding = "PyQt5"
} elseif (Test-InstallQtBinding -PackageName "PySide6") {
    $qtBinding = "PySide6"
} else {
    throw "Neither PyQt5 nor PySide6 could be installed in this environment."
}

Write-Host "Using Qt binding $qtBinding"

& .\.venv\Scripts\pyinstaller.exe `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name MoryandCpuTest `
  --collect-all matplotlib `
  --collect-all $qtBinding `
  main.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Write-Host "Build output: $projectRoot\dist\MoryandCpuTest.exe"
