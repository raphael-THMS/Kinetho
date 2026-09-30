$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$appSource = Join-Path $projectRoot 'src'
$installerSource = Join-Path $projectRoot 'installer'
$entryPoint = Join-Path $appSource 'kinetho_app.py'
$iconFile = Join-Path $appSource 'Kinetho.ico'
$buildRoot = Join-Path $projectRoot '.build'
$distRoot = Join-Path $buildRoot 'dist'
$workRoot = Join-Path $buildRoot 'work'
$specRoot = Join-Path $buildRoot 'spec'
$appOutput = Join-Path $distRoot 'Kinetho App'
$repoVenv = Join-Path $projectRoot '.venv'
$pythonCandidates = @(
    (Join-Path $repoVenv 'Scripts\python.exe'),
    (Join-Path (Split-Path -Parent $projectRoot) '.venv\Scripts\python.exe')
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $python) {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    $systemPython = Get-Command python.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
    Write-Host "Creating the build environment in $repoVenv ..."
    if ($launcher) {
        & $launcher.Source -3 -m venv $repoVenv
    } elseif ($systemPython) {
        & $systemPython.Source -m venv $repoVenv
    } else {
        throw 'Python 3.10+ was not found. Install it from https://www.python.org/downloads/ and run this script again.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python build environment.' }
    $python = Join-Path $repoVenv 'Scripts\python.exe'
}

$brandingSource = Get-Content -LiteralPath (Join-Path $appSource 'branding.py') -Raw
$versionMatch = [regex]::Match($brandingSource, 'APP_VERSION\s*=\s*"(\d+)\.(\d+)\.(\d+)"')
if (-not $versionMatch.Success) { throw 'APP_VERSION (x.y.z) was not found in branding.py.' }
$appVersion = '{0}.{1}.{2}' -f $versionMatch.Groups[1].Value, $versionMatch.Groups[2].Value, $versionMatch.Groups[3].Value
$versionTuple = '({0}, {1}, {2}, 0)' -f $versionMatch.Groups[1].Value, $versionMatch.Groups[2].Value, $versionMatch.Groups[3].Value
if (-not (Test-Path -LiteralPath $entryPoint)) {
    throw "Application entry point not found: $entryPoint"
}

# Windows PowerShell turns redirected native stderr into a terminating error under 'Stop'.
$ErrorActionPreference = 'Continue'
& $python -c "import PIL, PyInstaller" 2>$null
$requirementsMissing = $LASTEXITCODE -ne 0
$ErrorActionPreference = 'Stop'
if ($requirementsMissing) {
    Write-Host 'Installing build requirements...'
    & $python -m pip install -r (Join-Path $appSource 'build-requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Could not install PyInstaller build requirements.' }
}

if (Test-Path -LiteralPath $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $distRoot, $workRoot, $specRoot -Force | Out-Null

$versionFile = Join-Path $workRoot 'version_info.txt'
@"
VSVersionInfo(
  ffi=FixedFileInfo(filevers=$versionTuple, prodvers=$versionTuple),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Raphael Thomas'),
      StringStruct('FileDescription', 'Kinetho video processing and point annotation'),
      StringStruct('FileVersion', '$appVersion'),
      StringStruct('InternalName', 'Kinetho'),
      StringStruct('LegalCopyright', 'Copyright (c) 2026 Raphael Thomas. MIT License.'),
      StringStruct('OriginalFilename', 'Kinetho.exe'),
      StringStruct('ProductName', 'Kinetho'),
      StringStruct('ProductVersion', '$appVersion')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@ | Set-Content -LiteralPath $versionFile -Encoding UTF8

$pyinstallerArgs = @(
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    '--windowed',
    # One-folder build: a self-extracting one-file EXE is often flagged by antivirus software.
    '--onedir',
    '--noupx',
    '--contents-directory', '_internal',
    '--name', 'Kinetho',
    '--icon', $iconFile,
    '--version-file', $versionFile,
    '--distpath', $distRoot,
    '--workpath', $workRoot,
    '--specpath', $specRoot,
    '--paths', $appSource,
    '--collect-all', 'PIL',
    $entryPoint
)
& $python @pyinstallerArgs
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

Move-Item -LiteralPath (Join-Path $distRoot 'Kinetho') -Destination $appOutput

$runtimeFiles = @(
    @{ Source = $iconFile; Destination = 'Kinetho.ico' },
    @{ Source = (Join-Path $appSource 'kinetho_logo.png'); Destination = 'kinetho_logo.png' },
    @{ Source = (Join-Path $appSource 'kinetho_logo_white.png'); Destination = 'kinetho_logo_white.png' },
    @{ Source = (Join-Path $appSource 'points.txt'); Destination = 'points.txt' },
    @{ Source = (Join-Path $projectRoot 'README.md'); Destination = 'README.md' },
    @{ Source = (Join-Path $projectRoot 'README-fr.md'); Destination = 'README-fr.md' },
    @{ Source = (Join-Path $projectRoot 'LICENSE'); Destination = 'LICENSE' },
    @{ Source = (Join-Path $installerSource 'Uninstall Kinetho.ps1'); Destination = 'Uninstall Kinetho.ps1' }
)
foreach ($item in $runtimeFiles) {
    Copy-Item -LiteralPath $item.Source -Destination (Join-Path $appOutput $item.Destination) -Force
}
$rawVideoFolder = Join-Path $appOutput 'Video edition\Videos_before_modifications'
New-Item -ItemType Directory -Path $rawVideoFolder, (Join-Path $appOutput 'Videos'), (Join-Path $appOutput 'Image folders') -Force | Out-Null
Set-Content -LiteralPath (Join-Path $rawVideoFolder 'README.md') -Encoding UTF8 -Value @(
    'Place source videos in this folder before opening Kinetho.',
    'Placez les vidéos source dans ce dossier avant d''ouvrir Kinetho.'
)

Write-Host "Kinetho $appVersion built successfully: $(Join-Path $appOutput 'Kinetho.exe')"
Write-Host 'Kinetho.exe and its _internal folder include Python, Tkinter, and Pillow. Run Create Portable Package.ps1 to bundle FFmpeg.'
