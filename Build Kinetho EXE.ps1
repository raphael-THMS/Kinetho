$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appSource = Join-Path $projectRoot 'Point Annotator'
$entryPoint = Join-Path $appSource 'kinetho_app.py'
$iconFile = Join-Path $projectRoot 'Kinetho.ico'
$buildRoot = Join-Path $projectRoot '.build'
$distRoot = Join-Path $buildRoot 'dist'
$workRoot = Join-Path $buildRoot 'work'
$specRoot = Join-Path $buildRoot 'spec'
$appOutput = Join-Path $distRoot 'Kinetho App'
$developerPython = Join-Path (Split-Path -Parent $projectRoot) '.venv\Scripts\python.exe'
$appPython = Join-Path $appSource '.venv\Scripts\python.exe'
$python = if (Test-Path $developerPython) { $developerPython } else { $appPython }

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Python was not found. Run Point Annotator\Setup.bat first or install Python 3.10+.'
}
if (-not (Test-Path -LiteralPath $entryPoint)) {
    throw "Application entry point not found: $entryPoint"
}

& $python -c "import PIL, PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Installing build requirements...'
    & $python -m pip install -r (Join-Path $appSource 'build-requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Could not install PyInstaller build requirements.' }
}

if (Test-Path -LiteralPath $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $distRoot, $workRoot, $specRoot -Force | Out-Null

$pyinstallerArgs = @(
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    '--windowed',
    '--onefile',
    '--name', 'Kinetho',
    '--icon', $iconFile,
    '--distpath', $distRoot,
    '--workpath', $workRoot,
    '--specpath', $specRoot,
    '--paths', $appSource,
    '--collect-all', 'PIL',
    $entryPoint
)
& $python @pyinstallerArgs
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

New-Item -ItemType Directory -Path $appOutput -Force | Out-Null
Move-Item -LiteralPath (Join-Path $distRoot 'Kinetho.exe') -Destination (Join-Path $appOutput 'Kinetho.exe') -Force

$runtimeFiles = @(
    @{ Source = $iconFile; Destination = 'Kinetho.ico' },
    @{ Source = (Join-Path $appSource 'kinetho_logo.png'); Destination = 'kinetho_logo.png' },
    @{ Source = (Join-Path $appSource 'kinetho_logo_white.png'); Destination = 'kinetho_logo_white.png' },
    @{ Source = (Join-Path $appSource 'points.txt'); Destination = 'points.txt' },
    @{ Source = (Join-Path $projectRoot 'README.md'); Destination = 'README.md' },
    @{ Source = (Join-Path $projectRoot 'README-fr.md'); Destination = 'README-fr.md' },
    @{ Source = (Join-Path $projectRoot 'LICENSE'); Destination = 'LICENSE' },
    @{ Source = (Join-Path $projectRoot 'Uninstall Kinetho.ps1'); Destination = 'Uninstall Kinetho.ps1' }
)
foreach ($item in $runtimeFiles) {
    Copy-Item -LiteralPath $item.Source -Destination (Join-Path $appOutput $item.Destination) -Force
}
New-Item -ItemType Directory -Path (Join-Path $appOutput 'Video edition\Videos_before_modifications'), (Join-Path $appOutput 'Videos'), (Join-Path $appOutput 'Image folders') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'Video edition\Videos_before_modifications\README.md') -Destination (Join-Path $appOutput 'Video edition\Videos_before_modifications\README.md') -Force

Write-Host "Single-file Kinetho.exe built successfully: $(Join-Path $appOutput 'Kinetho.exe')"
Write-Host 'The EXE includes Python, Tkinter, and Pillow. Run Create Portable Package.ps1 to bundle FFmpeg.'
