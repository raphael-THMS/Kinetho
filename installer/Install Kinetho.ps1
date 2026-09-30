$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$packageApp = Join-Path $PSScriptRoot 'Kinetho App'
$defaultInstallPath = Join-Path $env:LOCALAPPDATA 'Programs\Kinetho'
$logoPath = Join-Path $packageApp 'kinetho_logo_white.png'
if (-not (Test-Path -LiteralPath $logoPath)) {
    $logoPath = Join-Path $packageApp 'Kinetho.ico'
}

$texts = @{
    en = @{
        WindowTitle      = 'Install Kinetho'
        Subtitle         = 'Choose where to install the application.'
        Language         = 'Language'
        Folder           = 'Installation folder'
        Browse           = 'Browse...'
        BrowseTitle      = 'Choose the parent folder for the Kinetho installation folder'
        Shortcut         = 'Create a Kinetho shortcut on the desktop'
        Info             = 'Kinetho will be installed for your Windows account. Your point configuration and existing data in the selected folder will be kept.'
        Ready            = 'Ready to install'
        Install          = 'Install'
        Cancel           = 'Cancel'
        Close            = 'Close'
        Copying          = 'Copying Kinetho files...'
        Complete         = 'Installation complete'
        Failed           = 'Installation failed'
        DoneShortcut     = "Kinetho is installed in:`r`n{0}`r`n`r`nA desktop shortcut has been created. Kinetho is ready to launch."
        DoneNoShortcut   = "Kinetho is installed in:`r`n{0}`r`n`r`nYou can start it by opening Kinetho.exe in this folder."
        ChooseFolder     = 'Choose an installation folder first.'
        InvalidPath      = 'The installation path is not valid.'
        ProtectedFolder  = "Kinetho cannot be installed in {0} because it needs to save settings and data in its own folder.`r`n`r`nChoose a folder in your user profile, for example the default location."
        MissingExe       = "Kinetho.exe was not found in the installation package.`r`n`r`n1. Make sure you extracted the whole ZIP (right-click > Extract All...) instead of opening Install Kinetho.bat from inside the ZIP.`r`n2. If you did, your antivirus probably removed Kinetho.exe after extraction. Check Windows Security > Virus & threat protection > Protection history, restore or allow Kinetho.exe, then extract the ZIP again."
        MissingFiles     = 'The Kinetho application files were not found in the package.'
        ShortcutComment  = 'Kinetho video processing and point annotation'
    }
    fr = @{
        WindowTitle      = 'Installer Kinetho'
        Subtitle         = "Choisissez où installer l'application."
        Language         = 'Langue'
        Folder           = "Dossier d'installation"
        Browse           = 'Parcourir...'
        BrowseTitle      = "Choisissez le dossier dans lequel créer le dossier d'installation de Kinetho"
        Shortcut         = 'Créer un raccourci Kinetho sur le Bureau'
        Info             = 'Kinetho sera installé pour votre compte Windows. Votre configuration des points et les données déjà présentes dans ce dossier seront conservées.'
        Ready            = "Prêt pour l'installation"
        Install          = 'Installer'
        Cancel           = 'Annuler'
        Close            = 'Fermer'
        Copying          = 'Copie des fichiers de Kinetho...'
        Complete         = 'Installation terminée'
        Failed           = "L'installation a échoué"
        DoneShortcut     = "Kinetho est installé dans :`r`n{0}`r`n`r`nUn raccourci a été créé sur le Bureau. Kinetho est prêt à être lancé."
        DoneNoShortcut   = "Kinetho est installé dans :`r`n{0}`r`n`r`nVous pouvez le lancer en ouvrant Kinetho.exe dans ce dossier."
        ChooseFolder     = "Choisissez d'abord un dossier d'installation."
        InvalidPath      = "Le chemin d'installation n'est pas valide."
        ProtectedFolder  = "Kinetho ne peut pas être installé dans {0}, car il doit enregistrer ses réglages et ses données dans son propre dossier.`r`n`r`nChoisissez un dossier de votre profil utilisateur, par exemple l'emplacement proposé par défaut."
        MissingExe       = "Kinetho.exe est introuvable dans le paquet d'installation.`r`n`r`n1. Vérifiez que vous avez extrait tout le ZIP (clic droit > Extraire tout...) au lieu d'ouvrir Install Kinetho.bat directement dans le ZIP.`r`n2. Si c'est le cas, votre antivirus a probablement supprimé Kinetho.exe après l'extraction. Ouvrez Sécurité Windows > Protection contre les virus et menaces > Historique de protection, restaurez ou autorisez Kinetho.exe, puis extrayez à nouveau le ZIP."
        MissingFiles     = "Les fichiers de l'application Kinetho sont introuvables dans le paquet."
        ShortcutComment  = 'Kinetho : traitement vidéo et annotation de points'
    }
}
$script:language = if ((Get-UICulture).TwoLetterISOLanguageName -eq 'fr') { 'fr' } else { 'en' }
function T([string]$key) { return $texts[$script:language][$key] }

if (-not (Test-Path -LiteralPath (Join-Path $packageApp 'Kinetho.exe'))) {
    [System.Windows.Forms.MessageBox]::Show(
        (T 'MissingExe'),
        'Kinetho',
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
    exit 1
}

$form = New-Object System.Windows.Forms.Form
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
$title.Font = New-Object System.Drawing.Font('Segoe UI', 19, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = [System.Drawing.Color]::FromArgb(26, 26, 26)
$title.Location = New-Object System.Drawing.Point(105, 24)
$title.Size = New-Object System.Drawing.Size(330, 38)
$form.Controls.Add($title)

$languageLabel = New-Object System.Windows.Forms.Label
$languageLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleRight
$languageLabel.Location = New-Object System.Drawing.Point(420, 28)
$languageLabel.Size = New-Object System.Drawing.Size(60, 24)
$form.Controls.Add($languageLabel)

$languageBox = New-Object System.Windows.Forms.ComboBox
$languageBox.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
[void]$languageBox.Items.AddRange(@('English', 'Français'))
$languageBox.SelectedIndex = if ($script:language -eq 'fr') { 1 } else { 0 }
$languageBox.Location = New-Object System.Drawing.Point(485, 28)
$languageBox.Size = New-Object System.Drawing.Size(100, 24)
$form.Controls.Add($languageBox)

$subtitle = New-Object System.Windows.Forms.Label
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
$browseButton.Location = New-Object System.Drawing.Point(470, 149)
$browseButton.Size = New-Object System.Drawing.Size(115, 30)
$browseButton.Add_Click({
    $picker = New-Object System.Windows.Forms.FolderBrowserDialog
    $picker.Description = T 'BrowseTitle'
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
$shortcutCheck.Checked = $true
$shortcutCheck.Location = New-Object System.Drawing.Point(31, 198)
$shortcutCheck.Size = New-Object System.Drawing.Size(550, 28)
$form.Controls.Add($shortcutCheck)

$info = New-Object System.Windows.Forms.Label
$info.ForeColor = [System.Drawing.Color]::FromArgb(90, 90, 90)
$info.Location = New-Object System.Drawing.Point(31, 235)
$info.Size = New-Object System.Drawing.Size(550, 58)
$form.Controls.Add($info)

$status = New-Object System.Windows.Forms.Label
$status.Location = New-Object System.Drawing.Point(31, 296)
$status.Size = New-Object System.Drawing.Size(550, 24)
$form.Controls.Add($status)

$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Location = New-Object System.Drawing.Point(31, 324)
$progress.Size = New-Object System.Drawing.Size(554, 18)
$progress.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
$form.Controls.Add($progress)

$installButton = New-Object System.Windows.Forms.Button
$installButton.Location = New-Object System.Drawing.Point(359, 377)
$installButton.Size = New-Object System.Drawing.Size(105, 34)
$installButton.BackColor = [System.Drawing.Color]::FromArgb(235, 0, 0)
$installButton.ForeColor = [System.Drawing.Color]::White
$installButton.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$installButton.FlatAppearance.BorderSize = 0
$form.Controls.Add($installButton)
$form.AcceptButton = $installButton

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Location = New-Object System.Drawing.Point(480, 377)
$cancelButton.Size = New-Object System.Drawing.Size(105, 34)
$cancelButton.Add_Click({ $form.Close() })
$form.Controls.Add($cancelButton)
$form.CancelButton = $cancelButton

function Set-FormTexts {
    $form.Text = T 'WindowTitle'
    $title.Text = T 'WindowTitle'
    $subtitle.Text = T 'Subtitle'
    $languageLabel.Text = T 'Language'
    $locationLabel.Text = T 'Folder'
    $browseButton.Text = T 'Browse'
    $shortcutCheck.Text = T 'Shortcut'
    $info.Text = T 'Info'
    $status.Text = T 'Ready'
    $installButton.Text = T 'Install'
    $cancelButton.Text = T 'Cancel'
}
Set-FormTexts

$languageBox.Add_SelectedIndexChanged({
    $script:language = if ($languageBox.SelectedIndex -eq 1) { 'fr' } else { 'en' }
    Set-FormTexts
})

$installButton.Add_Click({
    $destination = $pathBox.Text.Trim()
    if ([string]::IsNullOrWhiteSpace($destination)) {
        [System.Windows.Forms.MessageBox]::Show((T 'ChooseFolder'), (T 'WindowTitle'), 'OK', 'Warning') | Out-Null
        return
    }
    try {
        $destination = [System.IO.Path]::GetFullPath($destination)
    } catch {
        [System.Windows.Forms.MessageBox]::Show((T 'InvalidPath'), (T 'WindowTitle'), 'OK', 'Error') | Out-Null
        return
    }
    # Kinetho writes its settings and data next to Kinetho.exe, which fails in admin-only folders.
    $protectedRoots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:SystemRoot) | Where-Object { $_ }
    foreach ($protectedRoot in $protectedRoots) {
        if ($destination.StartsWith($protectedRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase) -or
            $destination.Equals($protectedRoot.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
            [System.Windows.Forms.MessageBox]::Show(((T 'ProtectedFolder') -f $protectedRoot), (T 'WindowTitle'), 'OK', 'Warning') | Out-Null
            return
        }
    }

    $installButton.Enabled = $false
    $browseButton.Enabled = $false
    $pathBox.Enabled = $false
    $shortcutCheck.Enabled = $false
    $languageBox.Enabled = $false
    $cancelButton.Enabled = $false
    $status.Text = T 'Copying'
    $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
    $progress.MarqueeAnimationSpeed = 22
    $form.Refresh()

    try {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        # Stale libraries from a previous version could conflict with the new ones.
        $previousLibraries = Join-Path $destination '_internal'
        if (Test-Path -LiteralPath $previousLibraries) {
            Remove-Item -LiteralPath $previousLibraries -Recurse -Force
        }
        $files = @(Get-ChildItem -LiteralPath $packageApp -File -Recurse -Force)
        if ($files.Count -eq 0) {
            throw (T 'MissingFiles')
        }
        $preservedFiles = @('points.txt')
        foreach ($file in $files) {
            $relativePath = $file.FullName.Substring($packageApp.Length).TrimStart('\')
            $targetPath = Join-Path $destination $relativePath
            if (($relativePath -in $preservedFiles) -and (Test-Path -LiteralPath $targetPath)) {
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

        # Start Kinetho in the language chosen here, unless the user already picked one in the app.
        $settingsFile = Join-Path $destination 'kinetho_settings.json'
        if (-not (Test-Path -LiteralPath $settingsFile)) {
            [System.IO.File]::WriteAllText($settingsFile, "{`n  `"language`": `"$script:language`"`n}", (New-Object System.Text.UTF8Encoding($false)))
        }

        if ($shortcutCheck.Checked) {
            $shell = New-Object -ComObject WScript.Shell
            $desktopPath = [Environment]::GetFolderPath('Desktop')
            $shortcutPath = Join-Path $desktopPath 'Kinetho.lnk'
            $shortcut = $shell.CreateShortcut($shortcutPath)
            $shortcut.TargetPath = Join-Path $destination 'Kinetho.exe'
            $shortcut.WorkingDirectory = $destination
            $shortcut.IconLocation = (Join-Path $destination 'Kinetho.ico') + ',0'
            $shortcut.Description = T 'ShortcutComment'
            $shortcut.Save()
        }

        $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Blocks
        $progress.MarqueeAnimationSpeed = 0
        $progress.Value = 100
        $status.Text = T 'Complete'
        if ($shortcutCheck.Checked) {
            $info.Text = (T 'DoneShortcut') -f $destination
        } else {
            $info.Text = (T 'DoneNoShortcut') -f $destination
        }
        $cancelButton.Text = T 'Close'
        $cancelButton.Enabled = $true
        $installButton.Visible = $false
        $browseButton.Visible = $false
        $form.CancelButton = $cancelButton
        $cancelButton.Focus()
    } catch {
        $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Blocks
        $progress.MarqueeAnimationSpeed = 0
        $progress.Value = 0
        $status.Text = T 'Failed'
        $info.Text = $_.Exception.Message
        $installButton.Enabled = $true
        $browseButton.Enabled = $true
        $pathBox.Enabled = $true
        $shortcutCheck.Enabled = $true
        $languageBox.Enabled = $true
        $cancelButton.Text = T 'Close'
        $cancelButton.Enabled = $true
    }
})

$form.Add_Shown({ $installButton.Focus() })
[void]$form.ShowDialog()
if ($null -ne $logo.Image) {
    $logo.Image.Dispose()
}
$form.Dispose()
