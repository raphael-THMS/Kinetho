$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$packageApp = Join-Path $PSScriptRoot 'Kinetho App'
$defaultInstallPath = Join-Path $env:LOCALAPPDATA 'Programs\Kinetho'
$logoPath = Join-Path $packageApp 'kinetho_logo_white.png'
if (-not (Test-Path -LiteralPath $logoPath)) {
    $logoPath = Join-Path $packageApp 'Kinetho.ico'
}

if (-not (Test-Path -LiteralPath (Join-Path $packageApp 'Kinetho.exe'))) {
    [System.Windows.Forms.MessageBox]::Show(
        "Kinetho.exe was not found in the installation package.`r`nExtract the complete Kinetho ZIP and run the installer again.",
        'Kinetho Setup',
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
    exit 1
}

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Install Kinetho'
$form.Size = New-Object System.Drawing.Size(620, 470)
$form.MinimumSize = New-Object System.Drawing.Size(620, 470)
$form.MaximumSize = New-Object System.Drawing.Size(620, 470)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(246, 246, 244)
$form.Font = New-Object System.Drawing.Font('Segoe UI', 9)

$title = New-Object System.Windows.Forms.Label
$title.Text = 'Install Kinetho'
$title.Font = New-Object System.Drawing.Font('Segoe UI', 19, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = [System.Drawing.Color]::FromArgb(26, 26, 26)
$title.Location = New-Object System.Drawing.Point(105, 24)
$title.Size = New-Object System.Drawing.Size(465, 38)
$form.Controls.Add($title)

$subtitle = New-Object System.Windows.Forms.Label
$subtitle.Text = 'Choose where to install the application.'
$subtitle.ForeColor = [System.Drawing.Color]::FromArgb(90, 90, 90)
$subtitle.Location = New-Object System.Drawing.Point(108, 65)
$subtitle.Size = New-Object System.Drawing.Size(460, 25)
$form.Controls.Add($subtitle)

$logo = New-Object System.Windows.Forms.PictureBox
$logo.Location = New-Object System.Drawing.Point(25, 22)
$logo.Size = New-Object System.Drawing.Size(64, 64)
$logo.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::Zoom
try {
    if (Test-Path -LiteralPath $logoPath) {
        $logo.Image = [System.Drawing.Image]::FromFile($logoPath)
    }
} catch {
    $logo.Image = $null
}
$form.Controls.Add($logo)

$locationLabel = New-Object System.Windows.Forms.Label
$locationLabel.Text = 'Installation folder'
$locationLabel.Font = New-Object System.Drawing.Font('Segoe UI', 9, [System.Drawing.FontStyle]::Bold)
$locationLabel.Location = New-Object System.Drawing.Point(28, 125)
$locationLabel.Size = New-Object System.Drawing.Size(550, 22)
$form.Controls.Add($locationLabel)

$pathBox = New-Object System.Windows.Forms.TextBox
$pathBox.Location = New-Object System.Drawing.Point(30, 151)
$pathBox.Size = New-Object System.Drawing.Size(430, 28)
$pathBox.Text = $defaultInstallPath
$form.Controls.Add($pathBox)

$browseButton = New-Object System.Windows.Forms.Button
$browseButton.Text = 'Browse...'
$browseButton.Location = New-Object System.Drawing.Point(470, 149)
$browseButton.Size = New-Object System.Drawing.Size(115, 30)
$browseButton.Add_Click({
    $picker = New-Object System.Windows.Forms.FolderBrowserDialog
    $picker.Description = 'Choose the parent folder for the Kinetho installation folder'
    $picker.ShowNewFolderButton = $true
    $currentDestination = $pathBox.Text.TrimEnd('\')
    $picker.SelectedPath = Split-Path -Parent $currentDestination
    if ($picker.ShowDialog($form) -eq [System.Windows.Forms.DialogResult]::OK) {
        $pathBox.Text = Join-Path $picker.SelectedPath 'Kinetho'
    }
    $picker.Dispose()
})
$form.Controls.Add($browseButton)

$shortcutCheck = New-Object System.Windows.Forms.CheckBox
$shortcutCheck.Text = 'Create a Kinetho shortcut on the desktop'
$shortcutCheck.Checked = $true
$shortcutCheck.Location = New-Object System.Drawing.Point(31, 198)
$shortcutCheck.Size = New-Object System.Drawing.Size(550, 28)
$form.Controls.Add($shortcutCheck)

$info = New-Object System.Windows.Forms.Label
$info.Text = 'Kinetho will be installed for your Windows account. Your point configuration and existing data in the selected folder will be kept.'
$info.ForeColor = [System.Drawing.Color]::FromArgb(90, 90, 90)
$info.Location = New-Object System.Drawing.Point(31, 235)
$info.Size = New-Object System.Drawing.Size(550, 44)
$form.Controls.Add($info)

$status = New-Object System.Windows.Forms.Label
$status.Text = 'Ready to install'
$status.Location = New-Object System.Drawing.Point(31, 296)
$status.Size = New-Object System.Drawing.Size(550, 24)
$form.Controls.Add($status)

$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Location = New-Object System.Drawing.Point(31, 324)
$progress.Size = New-Object System.Drawing.Size(554, 18)
$progress.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
$form.Controls.Add($progress)

$installButton = New-Object System.Windows.Forms.Button
$installButton.Text = 'Install'
$installButton.Location = New-Object System.Drawing.Point(359, 377)
$installButton.Size = New-Object System.Drawing.Size(105, 34)
$installButton.BackColor = [System.Drawing.Color]::FromArgb(235, 0, 0)
$installButton.ForeColor = [System.Drawing.Color]::White
$installButton.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$installButton.FlatAppearance.BorderSize = 0
$form.Controls.Add($installButton)
$form.AcceptButton = $installButton

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Text = 'Cancel'
$cancelButton.Location = New-Object System.Drawing.Point(480, 377)
$cancelButton.Size = New-Object System.Drawing.Size(105, 34)
$cancelButton.Add_Click({ $form.Close() })
$form.Controls.Add($cancelButton)
$form.CancelButton = $cancelButton

$installButton.Add_Click({
    $destination = $pathBox.Text.Trim()
    if ([string]::IsNullOrWhiteSpace($destination)) {
        [System.Windows.Forms.MessageBox]::Show('Choose an installation folder first.', 'Install Kinetho', 'OK', 'Warning') | Out-Null
        return
    }
    try {
        $destination = [System.IO.Path]::GetFullPath($destination)
    } catch {
        [System.Windows.Forms.MessageBox]::Show('The installation path is not valid.', 'Install Kinetho', 'OK', 'Error') | Out-Null
        return
    }

    $installButton.Enabled = $false
    $browseButton.Enabled = $false
    $pathBox.Enabled = $false
    $shortcutCheck.Enabled = $false
    $cancelButton.Enabled = $false
    $status.Text = 'Copying Kinetho files...'
    $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
    $progress.MarqueeAnimationSpeed = 22
    $form.Refresh()

    try {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        $files = @(Get-ChildItem -LiteralPath $packageApp -File -Recurse -Force)
        if ($files.Count -eq 0) {
            throw 'The Kinetho application files were not found in the package.'
        }
        $relativePointFiles = @('points.txt')
        foreach ($file in $files) {
            $relativePath = $file.FullName.Substring($packageApp.Length).TrimStart('\')
            $targetPath = Join-Path $destination $relativePath
            if (($relativePath -in $relativePointFiles) -and (Test-Path -LiteralPath $targetPath)) {
                continue
            }
            $targetDirectory = Split-Path -Parent $targetPath
            New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
            Copy-Item -LiteralPath $file.FullName -Destination $targetPath -Force
            [System.Windows.Forms.Application]::DoEvents()
        }

        foreach ($relativePath in @('Videos', 'Image folders', 'Video edition\Videos_before_modifications')) {
            New-Item -ItemType Directory -Path (Join-Path $destination $relativePath) -Force | Out-Null
        }
        Copy-Item -LiteralPath (Join-Path $packageApp 'Video edition\Videos_before_modifications\README.md') -Destination (Join-Path $destination 'Video edition\Videos_before_modifications\README.md') -Force

        if ($shortcutCheck.Checked) {
            $shell = New-Object -ComObject WScript.Shell
            $desktopPath = [Environment]::GetFolderPath('Desktop')
            $shortcutPath = Join-Path $desktopPath 'Kinetho.lnk'
            $shortcut = $shell.CreateShortcut($shortcutPath)
            $shortcut.TargetPath = Join-Path $destination 'Kinetho.exe'
            $shortcut.WorkingDirectory = $destination
            $shortcut.IconLocation = (Join-Path $destination 'Kinetho.ico') + ',0'
            $shortcut.Description = 'Kinetho video processing and point annotation'
            $shortcut.Save()
        }

        $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Blocks
        $progress.MarqueeAnimationSpeed = 0
        $progress.Value = 100
        $status.Text = 'Installation complete'
        if ($shortcutCheck.Checked) {
            $details = "Kinetho is installed in:`r`n$destination`r`n`r`nA desktop shortcut has been created. Kinetho is ready to launch."
        } else {
            $details = "Kinetho is installed in:`r`n$destination`r`n`r`nYou can start it by opening Kinetho.exe in this folder."
        }
        $info.Text = $details
        $cancelButton.Text = 'Close'
        $cancelButton.Enabled = $true
        $installButton.Visible = $false
        $browseButton.Visible = $false
        $form.CancelButton = $cancelButton
        $cancelButton.Focus()
    } catch {
        $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Blocks
        $progress.MarqueeAnimationSpeed = 0
        $progress.Value = 0
        $status.Text = 'Installation failed'
        $info.Text = $_.Exception.Message
        $installButton.Enabled = $true
        $browseButton.Enabled = $true
        $pathBox.Enabled = $true
        $shortcutCheck.Enabled = $true
        $cancelButton.Text = 'Close'
        $cancelButton.Enabled = $true
    }
})

$form.Add_Shown({ $installButton.Focus() })
[void]$form.ShowDialog()
if ($null -ne $logo.Image) {
    $logo.Image.Dispose()
}
$form.Dispose()
