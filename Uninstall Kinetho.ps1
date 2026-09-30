param(
    [string]$InstallRoot = $env:KINETHO_INSTALL_DIR,
    [string]$DesktopPath = [Environment]::GetFolderPath('Desktop'),
    [int]$WaitProcessId = 0,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

try {
    if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
        throw 'The Kinetho installation folder was not provided.'
    }
    $InstallRoot = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
    if ($WaitProcessId -gt 0) {
        Wait-Process -Id $WaitProcessId -ErrorAction SilentlyContinue
    }

    $installPrefix = $InstallRoot + '\'
    $runningKinetho = @()
    for ($attempt = 0; $attempt -lt 240; $attempt++) {
        $runningKinetho = @(
            Get-Process -Name 'Kinetho' -ErrorAction SilentlyContinue | Where-Object {
                $_.Path -and $_.Path.StartsWith($installPrefix, [StringComparison]::OrdinalIgnoreCase)
            }
        )
        if ($runningKinetho.Count -eq 0) {
            break
        }
        Start-Sleep -Milliseconds 500
    }
    if ($runningKinetho.Count -gt 0) {
        throw 'Another Kinetho window is still open. Close it and run the uninstaller again.'
    }

    $shortcut = Join-Path $DesktopPath 'Kinetho.lnk'
    if (Test-Path -LiteralPath $shortcut) {
        Remove-Item -LiteralPath $shortcut -Force
    }
    foreach ($name in @(
        'Kinetho.exe',
        'Kinetho.ico',
        'kinetho_logo.png',
        'kinetho_logo_white.png',
        'README.md',
        'README-fr.md',
        'LICENSE',
        'kinetho_settings.json',
        'Uninstall Kinetho.ps1'
    )) {
        $file = Join-Path $InstallRoot $name
        if (Test-Path -LiteralPath $file) {
            Remove-Item -LiteralPath $file -Force
        }
    }
    $ffmpegDirectory = Join-Path $InstallRoot 'ffmpeg'
    if (Test-Path -LiteralPath $ffmpegDirectory) {
        Remove-Item -LiteralPath $ffmpegDirectory -Recurse -Force
    }

    if (-not $Quiet) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            "Kinetho and its bundled FFmpeg dependency have been removed.`r`n`r`nYour point configuration, videos, extracted images, and annotations were kept in:`r`n$InstallRoot",
            'Kinetho Uninstalled',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        ) | Out-Null
    }
} catch {
    if (-not $Quiet) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            'Kinetho Uninstall Failed',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
    }
    exit 1
} finally {
    if ($MyInvocation.MyCommand.Path -and (Test-Path -LiteralPath $MyInvocation.MyCommand.Path)) {
        Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
    }
}