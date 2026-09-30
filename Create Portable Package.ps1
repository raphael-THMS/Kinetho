$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$packageRoot = Split-Path -Parent $projectRoot
$appBuild = Join-Path $projectRoot '.build\dist\Kinetho App'
$ffmpegRoot = Join-Path $projectRoot 'Third-party\FFmpeg'
$ffmpegBinary = Join-Path $ffmpegRoot 'bin\ffmpeg.exe'
$ffmpegNotice = Join-Path $ffmpegRoot 'FFmpeg-GPLv3-Notice.txt'
$ffmpegLicense = Join-Path $ffmpegRoot 'COPYING.GPLv3.txt'
$ffmpegBuildInfo = Join-Path $ffmpegRoot 'README.txt'
$ffmpegSource = Join-Path $ffmpegRoot 'source\ffmpeg-9.0.2.tar.xz'
$ffmpegSourceSignature = $ffmpegSource + '.asc'
$packagePath = Join-Path $packageRoot 'Kinetho-Windows.zip'
$stagePath = Join-Path $env:TEMP ('Kinetho-package-' + [guid]::NewGuid().ToString('N'))

$installerFiles = @(
    'Install Kinetho.bat',
    'Install Kinetho.ps1',
    'Install README.md'
)

if (-not (Test-Path -LiteralPath (Join-Path $appBuild 'Kinetho.exe'))) {
    throw 'Kinetho.exe was not built. Run Build Kinetho EXE.ps1 first.'
}
foreach ($requiredFile in @($ffmpegBinary, $ffmpegNotice, $ffmpegLicense, $ffmpegBuildInfo, $ffmpegSource, $ffmpegSourceSignature)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required bundled FFmpeg file is missing: $requiredFile. Run Setup FFmpeg.ps1 first."
    }
}
$ffmpegEncoders = (& $ffmpegBinary -hide_banner -encoders 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0 -or $ffmpegEncoders -notmatch 'libx264') {
    throw 'The bundled FFmpeg executable must run successfully and include the libx264 encoder.'
}

try {
    New-Item -ItemType Directory -Path $stagePath -Force | Out-Null
    foreach ($relativePath in $installerFiles) {
        $sourcePath = Join-Path $projectRoot $relativePath
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Required installer file is missing: $relativePath"
        }
        Copy-Item -LiteralPath $sourcePath -Destination (Join-Path $stagePath $relativePath)
    }

    Copy-Item -LiteralPath $appBuild -Destination (Join-Path $stagePath 'Kinetho App') -Recurse
    $packageFfmpeg = Join-Path $stagePath 'Kinetho App\ffmpeg'
    New-Item -ItemType Directory -Path (Join-Path $packageFfmpeg 'bin') -Force | Out-Null
    Copy-Item -LiteralPath $ffmpegBinary -Destination (Join-Path $packageFfmpeg 'bin\ffmpeg.exe') -Force
    Copy-Item -LiteralPath @($ffmpegNotice, $ffmpegLicense, $ffmpegBuildInfo) -Destination $packageFfmpeg -Force

    if (Test-Path -LiteralPath $packagePath) {
        Remove-Item -LiteralPath $packagePath -Force
    }
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::Open($packagePath, [System.IO.Compression.ZipArchiveMode]::Create)
    try {
        Get-ChildItem -LiteralPath $stagePath -File -Recurse | ForEach-Object {
            $relative = $_.FullName.Substring($stagePath.Length).TrimStart('\').Replace('\', '/')
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive,
                $_.FullName,
                $relative,
                [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }
    } finally {
        $archive.Dispose()
    }

    Write-Host "Installer package created: $packagePath"
    Copy-Item -LiteralPath @($ffmpegSource, $ffmpegSourceSignature) -Destination $packageRoot -Force
    Write-Host "FFmpeg source for the release: $(Join-Path $packageRoot 'ffmpeg-9.0.2.tar.xz')"
    Write-Host 'Attach Kinetho-Windows.zip, ffmpeg-9.0.2.tar.xz and ffmpeg-9.0.2.tar.xz.asc to the same GitHub release.'
    Write-Host 'The ZIP contains Kinetho.exe, FFmpeg, and their notices, but excludes user media, annotations, and local build environments.'
} finally {
    if (Test-Path -LiteralPath $stagePath) {
        Remove-Item -LiteralPath $stagePath -Recurse -Force
    }
}
