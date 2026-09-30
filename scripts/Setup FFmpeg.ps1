param([string]$ArchivePath)
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$distributionRoot = Join-Path $projectRoot 'Third-party\FFmpeg'
$downloadUrl = 'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip'
$expectedSha256 = '60F467265B1E312373DBCD92200C2618A74850F98D3D078E94296BB3FA2047BA'
$entryPrefix = 'ffmpeg-9.0.2-essentials_build/'
$sourceUrl = 'https://ffmpeg.org/releases/ffmpeg-9.0.2.tar.xz'
$sourceSha256 = '8C3850283EB25FA026482078A04051E0BE17347B09EF81A0849BEC15A96E002E'
$sourceRoot = Join-Path $distributionRoot 'source'
$sourceTarball = Join-Path $sourceRoot 'ffmpeg-9.0.2.tar.xz'
$temporaryRoot = $null
$archive = $null

if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
    $temporaryRoot = Join-Path $env:TEMP ('Kinetho-FFmpeg-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
    $ArchivePath = Join-Path $temporaryRoot 'ffmpeg-release-essentials.zip'
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($null -eq $curl) {
        throw 'curl.exe is required to download FFmpeg. On Windows 10/11 it is normally included.'
    }
    & $curl.Source -fL --retry 3 --connect-timeout 30 -o $ArchivePath $downloadUrl
    if ($LASTEXITCODE -ne 0) {
        throw "FFmpeg download failed with curl exit code $LASTEXITCODE."
    }
}

try {
    if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
        throw "FFmpeg archive not found: $ArchivePath"
    }
    $actualSha256 = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash
    if ($actualSha256 -ne $expectedSha256) {
        throw "FFmpeg archive SHA-256 mismatch. Expected $expectedSha256; got $actualSha256."
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $ArchivePath).Path)
    $filesToExtract = @(
        @{ Entry = ($entryPrefix + 'bin/ffmpeg.exe'); Destination = (Join-Path $distributionRoot 'bin\ffmpeg.exe') },
        @{ Entry = ($entryPrefix + 'LICENSE'); Destination = (Join-Path $distributionRoot 'COPYING.GPLv3.txt') },
        @{ Entry = ($entryPrefix + 'README.txt'); Destination = (Join-Path $distributionRoot 'README.txt') }
    )
    foreach ($item in $filesToExtract) {
        $entry = $archive.GetEntry($item.Entry)
        if ($null -eq $entry) {
            throw "Required file is missing from the FFmpeg archive: $($item.Entry)"
        }
        New-Item -ItemType Directory -Path (Split-Path -Parent $item.Destination) -Force | Out-Null
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $item.Destination, $true)
    }
    $archive.Dispose()
    $archive = $null

    $ffmpegBinary = Join-Path $distributionRoot 'bin\ffmpeg.exe'
    $versionOutput = (& $ffmpegBinary -hide_banner -version 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0 -or $versionOutput -notmatch 'ffmpeg version 9\.0\.2') {
        throw 'The extracted FFmpeg executable failed its version check.'
    }
    $encoderOutput = (& $ffmpegBinary -hide_banner -encoders 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0 -or $encoderOutput -notmatch 'libx264') {
        throw 'The extracted FFmpeg executable does not provide the required libx264 encoder.'
    }

    # GPLv3 requires publishing the corresponding source next to the bundled binary.
    $sourceIsValid = (Test-Path -LiteralPath $sourceTarball -PathType Leaf) -and
        ((Get-FileHash -LiteralPath $sourceTarball -Algorithm SHA256).Hash -eq $sourceSha256)
    if (-not $sourceIsValid) {
        New-Item -ItemType Directory -Path $sourceRoot -Force | Out-Null
        $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
        if ($null -eq $curl) {
            throw 'curl.exe is required to download the FFmpeg source code.'
        }
        foreach ($suffix in @('', '.asc')) {
            & $curl.Source -fL --retry 3 --connect-timeout 30 -o ($sourceTarball + $suffix) ($sourceUrl + $suffix)
            if ($LASTEXITCODE -ne 0) {
                throw "FFmpeg source download failed with curl exit code $LASTEXITCODE."
            }
        }
        $actualSourceSha256 = (Get-FileHash -LiteralPath $sourceTarball -Algorithm SHA256).Hash
        if ($actualSourceSha256 -ne $sourceSha256) {
            throw "FFmpeg source SHA-256 mismatch. Expected $sourceSha256; got $actualSourceSha256."
        }
    }

    Write-Host 'FFmpeg 9.0.2 Essentials is ready for Kinetho.'
    Write-Host "SHA-256: $actualSha256"
    Write-Host "Location: $distributionRoot"
} finally {
    if ($null -ne $archive) {
        $archive.Dispose()
    }
    if ($null -ne $temporaryRoot -and (Test-Path -LiteralPath $temporaryRoot)) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}