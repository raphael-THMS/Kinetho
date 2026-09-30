param(
    [string]$InstallRoot = $env:KINETHO_INSTALL_DIR,
    [string]$DesktopPath = [Environment]::GetFolderPath('Desktop'),
    [int]$WaitProcessId = 0,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

$language = if ((Get-UICulture).TwoLetterISOLanguageName -eq 'fr') { 'fr' } else { 'en' }
try {
    $settingsFile = Join-Path $InstallRoot 'kinetho_settings.json'
    if ($InstallRoot -and (Test-Path -LiteralPath $settingsFile)) {
        $savedLanguage = (Get-Content -LiteralPath $settingsFile -Raw | ConvertFrom-Json).language
        if ($savedLanguage -in @('en', 'fr')) { $language = $savedLanguage }
    }
} catch {
    # An unreadable settings file only affects the message language.
}
$messages = @{
    en = @{
        NoFolder     = 'The Kinetho installation folder was not provided.'
        StillOpen    = 'Another Kinetho window is still open. Close it and run the uninstaller again.'
        DoneTitle    = 'Kinetho Uninstalled'
        Done         = "Kinetho and its bundled FFmpeg dependency have been removed.`r`n`r`nYour point configuration, videos, extracted images, and annotations were kept in:`r`n{0}"
        FailedTitle  = 'Kinetho Uninstall Failed'
    }
    fr = @{
        NoFolder     = "Le dossier d'installation de Kinetho n'a pas été indiqué."
        StillOpen    = 'Une autre fenêtre Kinetho est encore ouverte. Fermez-la, puis relancez la désinstallation.'
        DoneTitle    = 'Kinetho désinstallé'
        Done         = "Kinetho et FFmpeg ont été supprimés.`r`n`r`nVotre configuration des points, vos vidéos, les images extraites et les annotations ont été conservées dans :`r`n{0}"
        FailedTitle  = 'Échec de la désinstallation de Kinetho'
    }
}[$language]

try {
    if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
        throw $messages.NoFolder
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
        throw $messages.StillOpen
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
    foreach ($directoryName in @('ffmpeg', '_internal')) {
        $appDirectory = Join-Path $InstallRoot $directoryName
        if (Test-Path -LiteralPath $appDirectory) {
            Remove-Item -LiteralPath $appDirectory -Recurse -Force
        }
    }

    if (-not $Quiet) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            ($messages.Done -f $InstallRoot),
            $messages.DoneTitle,
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        ) | Out-Null
    }
} catch {
    if (-not $Quiet) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            $messages.FailedTitle,
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