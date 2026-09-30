$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$logoPath = Join-Path $scriptDirectory 'kinetho_logo_white.png'
$venvDirectory = Join-Path $scriptDirectory '.venv'
$venvPython = Join-Path $venvDirectory 'Scripts\python.exe'
$requirementsFile = Join-Path $scriptDirectory 'requirements.txt'
$logFile = Join-Path $env:TEMP ("Kinetho_Setup_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
$stdoutFile = Join-Path $env:TEMP ("Kinetho_Setup_{0}.stdout" -f [guid]::NewGuid().ToString('N'))
$stderrFile = Join-Path $env:TEMP ("Kinetho_Setup_{0}.stderr" -f [guid]::NewGuid().ToString('N'))
$script:steps = New-Object System.Collections.ArrayList
$script:stepIndex = 0
$script:process = $null

Set-Content -Path $logFile -Value ("Kinetho setup - {0}" -f (Get-Date)) -Encoding UTF8

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Kinetho Setup'
$form.Size = New-Object System.Drawing.Size(610, 410)
$form.MinimumSize = New-Object System.Drawing.Size(610, 410)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $true

$title = New-Object System.Windows.Forms.Label
$title.Text = 'Kinetho'
$title.Font = New-Object System.Drawing.Font('Segoe UI', 13, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = [System.Drawing.Color]::FromArgb(255, 0, 0)
$title.Location = New-Object System.Drawing.Point(92, 12)
$title.Size = New-Object System.Drawing.Size(485, 28)
$form.Controls.Add($title)

$logo = New-Object System.Windows.Forms.PictureBox
$logo.Location = New-Object System.Drawing.Point(18, 10)
$logo.Size = New-Object System.Drawing.Size(62, 56)
$logo.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::Zoom
if (Test-Path $logoPath) {
    $logo.Image = [System.Drawing.Image]::FromFile($logoPath)
}
$form.Controls.Add($logo)

$subtitle = New-Object System.Windows.Forms.Label
$subtitle.Text = 'Application setup'
$subtitle.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$subtitle.ForeColor = [System.Drawing.Color]::FromArgb(92, 92, 92)
$subtitle.Location = New-Object System.Drawing.Point(94, 40)
$subtitle.Size = New-Object System.Drawing.Size(485, 18)
$form.Controls.Add($subtitle)

$status = New-Object System.Windows.Forms.Label
$status.Text = 'Preparing installation...'
$status.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$status.Location = New-Object System.Drawing.Point(20, 72)
$status.Size = New-Object System.Drawing.Size(555, 25)
$form.Controls.Add($status)

$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Location = New-Object System.Drawing.Point(20, 104)
$progress.Size = New-Object System.Drawing.Size(555, 22)
$progress.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
$progress.MarqueeAnimationSpeed = 25
$form.Controls.Add($progress)

$details = New-Object System.Windows.Forms.TextBox
$details.Location = New-Object System.Drawing.Point(20, 138)
$details.Size = New-Object System.Drawing.Size(555, 179)
$details.Multiline = $true
$details.ReadOnly = $true
$details.ScrollBars = 'Vertical'
$details.WordWrap = $true
$details.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$details.Text = "Installation may take a few minutes depending on your Internet connection.`r`n`r`nKeep this window open while files are being downloaded."
$form.Controls.Add($details)

$openLog = New-Object System.Windows.Forms.Button
$openLog.Text = 'Open log'
$openLog.Location = New-Object System.Drawing.Point(20, 330)
$openLog.Size = New-Object System.Drawing.Size(130, 30)
$openLog.Enabled = $false
$openLog.Add_Click({
    if (Test-Path $logFile) {
        Start-Process notepad.exe -ArgumentList ('"{0}"' -f $logFile)
    }
})
$form.Controls.Add($openLog)

$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Text = 'Close'
$closeButton.Location = New-Object System.Drawing.Point(475, 330)
$closeButton.Size = New-Object System.Drawing.Size(100, 30)
$closeButton.Enabled = $false
$closeButton.Add_Click({ $form.Close() })
$form.Controls.Add($closeButton)

$openLog.BackColor = [System.Drawing.Color]::FromArgb(255, 0, 0)
$openLog.ForeColor = [System.Drawing.Color]::White
$closeButton.BackColor = [System.Drawing.Color]::FromArgb(32, 32, 32)
$closeButton.ForeColor = [System.Drawing.Color]::White

function Get-QuotedArgument([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}

function Add-InstallStep([string]$Name, [string]$Executable, [string[]]$Arguments) {
    [void]$script:steps.Add([pscustomobject]@{
        Name = $Name
        Executable = $Executable
        Arguments = $Arguments
    })
}

function Get-ErrorSummary([string]$Text) {
    $causes = New-Object System.Collections.ArrayList
    if ($Text -match '(?i)pip\._vendor\.rich|cannot import name .themes.|ImportError: cannot import name') {
        [void]$causes.Add("The existing pip installation is incomplete or corrupted. Preserve it for diagnosis, then create a clean application environment by running Setup.bat again.")
    }
    if ($Text -match '(?i)Python was not found|Install Python') {
        [void]$causes.Add("Python 3.10 or later was not found. Install Python from python.org, then run Setup.bat again.")
    }
    if ($Text -match '(?i)timed out|timeout|name resolution|connection refused|network is unreachable|proxyerror|connectionerror') {
        [void]$causes.Add("The Internet connection is unavailable or unstable. Check the network, proxy settings, and access to pypi.org.")
    }
    if ($Text -match '(?i)ssl|certificate verify failed|CERTIFICATE_VERIFY_FAILED') {
        [void]$causes.Add("HTTPS certificate verification failed. Check the Windows date and the computer's certificates or network restrictions.")
    }
    if ($Text -match '(?i)No matching distribution found|Requires-Python|requires a different Python|not a supported wheel|UnsupportedPythonVersion') {
        [void]$causes.Add("This Python version may not be compatible. Install 64-bit Python 3.10 or later, then run the installer again.")
    }
    if ($Text -match '(?i)Access is denied|PermissionError|WinError 5') {
        [void]$causes.Add("Windows denied access to a file. Close the application if it is running and check write permissions for this folder.")
    }
    if ($Text -match '(?i)No module named pip|No module named venv|No module named ensurepip|ensurepip.*failed|failed to create.*virtual environment') {
        [void]$causes.Add("Python could not create its virtual environment or install pip. Repair Python and make sure the pip and venv components are installed.")
    }
    if ($Text -match '(?i)No space left|not enough space|disk full') {
        [void]$causes.Add("There is not enough disk space. Free some space and run the installer again.")
    }
    if ($Text -match '(?i)Could not find a version that satisfies the requirement|ERROR: Could not find a version') {
        [void]$causes.Add("pip could not find Pillow in the package index. Check Internet access, proxy settings, or the pip index configuration.")
    }
    if ($causes.Count -eq 0) {
        [void]$causes.Add("The cause could not be determined automatically. Open the technical log to see the full error message.")
    }
    return ($causes -join "`r`n`r`n")
}

function Finish-Installation([bool]$Success, [string]$Message) {
    $timer.Stop()
    $script:process = $null
    $progress.MarqueeAnimationSpeed = 0
    $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Blocks
    $progress.Value = if ($Success) { 100 } else { 0 }
    $status.Text = if ($Success) { 'Installation complete' } else { 'Installation failed' }
    $details.Text = $Message
    $openLog.Enabled = $true
    $closeButton.Enabled = $true
    if ($Success) {
        Add-Content -Path $logFile -Value ("`r`nInstallation completed successfully - {0}" -f (Get-Date)) -Encoding UTF8
    }
}

function Start-NextStep {
    if ($script:stepIndex -ge $script:steps.Count) {
        Finish-Installation $true "Everything is installed. Close this window and run Launch.bat.`r`n`r`nLog: $logFile"
        return
    }

    $step = $script:steps[$script:stepIndex]
    $status.Text = $step.Name
    $details.Text = "Step $($script:stepIndex + 1) of $($script:steps.Count).`r`n`r`nThe animated bar indicates that this operation is in progress."
    Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
    Add-Content -Path $logFile -Value ("`r`n===== {0} - {1} =====" -f (Get-Date), $step.Name) -Encoding UTF8

    try {
        $argumentLine = (($step.Arguments | ForEach-Object { Get-QuotedArgument $_ }) -join ' ')
        $script:process = Start-Process -FilePath $step.Executable -ArgumentList $argumentLine -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
    } catch {
        $failure = "Could not start this step: $($_.Exception.Message)"
        Add-Content -Path $logFile -Value $failure -Encoding UTF8
        Finish-Installation $false ((Get-ErrorSummary $failure) + "`r`n`r`nJournal : $logFile")
    }
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 400
$timer.Add_Tick({
    if ($null -eq $script:process) {
        return
    }

    if (-not $script:process.HasExited) {
        $liveOutput = @(
            if (Test-Path $stdoutFile) { Get-Content -Path $stdoutFile -Tail 20 -ErrorAction SilentlyContinue }
            if (Test-Path $stderrFile) { Get-Content -Path $stderrFile -Tail 20 -ErrorAction SilentlyContinue }
        ) -join "`n"
        $percentages = [regex]::Matches($liveOutput, '(\d{1,3})\s*%')
        if ($percentages.Count -gt 0) {
            $percent = [int]$percentages[$percentages.Count - 1].Groups[1].Value
            if ($percent -ge 0 -and $percent -le 100) {
                $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
                $progress.MarqueeAnimationSpeed = 0
                $progress.Value = $percent
                $details.Text = "Download progress: $percent %`r`n`r`nLog: $logFile"
            }
        }
        return
    }

    $processExitCode = $script:process.ExitCode
    $step = $script:steps[$script:stepIndex]
    $stdout = if (Test-Path $stdoutFile) { Get-Content -Path $stdoutFile -Raw -ErrorAction SilentlyContinue } else { '' }
    $stderr = if (Test-Path $stderrFile) { Get-Content -Path $stderrFile -Raw -ErrorAction SilentlyContinue } else { '' }
    $output = ($stdout, $stderr) -join "`r`n"
    if (-not [string]::IsNullOrWhiteSpace($output)) {
        Add-Content -Path $logFile -Value $output -Encoding UTF8
    }

    $script:process = $null
    $exitCodeMissing = $null -eq $processExitCode -or [string]::IsNullOrWhiteSpace([string]$processExitCode)
    if ($exitCodeMissing -or $processExitCode -ne 0) {
        if ($exitCodeMissing) {
            $processExitCode = 'unknown'
        }
        Add-Content -Path $logFile -Value ("Process exit code: {0}" -f $processExitCode) -Encoding UTF8
        $summary = Get-ErrorSummary $output
        $details.Text = "Likely cause(s):`r`n$summary`r`n`r`nFailed step: $($step.Name)`r`nExit code: $processExitCode`r`n`r`nTechnical log: $logFile"
        $status.Text = 'An error prevented installation'
        $progress.MarqueeAnimationSpeed = 0
        $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Blocks
        $progress.Value = 0
        $openLog.Enabled = $true
        $closeButton.Enabled = $true
        return
    }

    $script:stepIndex++
    Start-NextStep
})

try {
    $needsNewEnvironment = -not (Test-Path $venvPython)
    if (Test-Path $venvPython) {
        $venvConfiguration = Join-Path $venvDirectory 'pyvenv.cfg'
        $venvHome = $null
        if (Test-Path $venvConfiguration) {
            $homeSetting = Get-Content -Path $venvConfiguration | Where-Object { $_ -match '^\s*home\s*=' } | Select-Object -First 1
            if ($homeSetting -match '^\s*home\s*=\s*(.+?)\s*$') {
                $venvHome = $Matches[1]
            }
        }
        $basePython = if ($venvHome) { Join-Path $venvHome 'python.exe' } else { $null }
        if (-not $basePython -or -not (Test-Path $basePython)) {
            $backupDirectory = Join-Path $scriptDirectory ('.venv.portable-old-{0}' -f (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
            Add-Content -Path $logFile -Value "`r`nThe virtual environment points to a Python installation that is not available on this computer." -Encoding UTF8
            Move-Item -LiteralPath $venvDirectory -Destination $backupDirectory
            Add-Content -Path $logFile -Value ("Moved the non-portable environment to: {0}" -f $backupDirectory) -Encoding UTF8
            $needsNewEnvironment = $true
        } else {
            Add-Content -Path $logFile -Value "`r`nChecking the existing pip installation..." -Encoding UTF8
            Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
            $pipCheckProcess = Start-Process -FilePath $venvPython -ArgumentList '"-m" "pip" "--version"' -PassThru -Wait -WindowStyle Hidden -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
            $pipCheckExitCode = $pipCheckProcess.ExitCode
            $pipCheckStdout = if (Test-Path $stdoutFile) { Get-Content -Path $stdoutFile -Raw -ErrorAction SilentlyContinue } else { '' }
            $pipCheckStderr = if (Test-Path $stderrFile) { Get-Content -Path $stderrFile -Raw -ErrorAction SilentlyContinue } else { '' }
            $pipCheckOutput = ($pipCheckStdout, $pipCheckStderr) -join "`r`n"
            if ($pipCheckExitCode -eq 0) {
                Add-Content -Path $logFile -Value $pipCheckOutput -Encoding UTF8
            } else {
                $backupDirectory = Join-Path $scriptDirectory ('.venv.broken-{0}' -f (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
                Add-Content -Path $logFile -Value ("Existing pip check failed with exit code {0}." -f $pipCheckExitCode) -Encoding UTF8
                Add-Content -Path $logFile -Value $pipCheckOutput -Encoding UTF8
                Move-Item -LiteralPath $venvDirectory -Destination $backupDirectory
                Add-Content -Path $logFile -Value ("Preserved the broken environment at: {0}" -f $backupDirectory) -Encoding UTF8
                $needsNewEnvironment = $true
            }
        }
    }

    if ($needsNewEnvironment) {
        $pythonCommand = Get-Command 'python.exe' -ErrorAction SilentlyContinue
        if ($null -ne $pythonCommand) {
            Add-InstallStep 'Creating the Python environment' $pythonCommand.Source @('-m', 'venv', $venvDirectory)
        } else {
            $pyLauncher = Get-Command 'py.exe' -ErrorAction SilentlyContinue
            if ($null -eq $pyLauncher) {
                throw "Python was not found. Install Python 3.10 or later from python.org, then run Setup.bat again."
            }
            Add-InstallStep 'Creating the Python environment' $pyLauncher.Source @('-3', '-m', 'venv', $venvDirectory)
        }
        Add-InstallStep 'Downloading and installing dependencies' $venvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '--progress-bar', 'on', '-r', $requirementsFile)
    } else {
        Add-InstallStep 'Installing dependencies' $venvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '--progress-bar', 'on', '-r', $requirementsFile)
    }

    $timer.Start()
    $form.Add_Shown({ Start-NextStep })
    [void]$form.ShowDialog()
} catch {
    $message = $_.Exception.Message
    Add-Content -Path $logFile -Value ("`r`nSetup error: {0}" -f $message) -Encoding UTF8
    $timer.Stop()
    $progress.MarqueeAnimationSpeed = 0
    $progress.Style = [System.Windows.Forms.ProgressBarStyle]::Blocks
    $progress.Value = 0
    $status.Text = 'Setup could not continue'
    $details.Text = "Likely cause:`r`n$(Get-ErrorSummary $message)`r`n`r`nTechnical log: $logFile"
    $openLog.Enabled = $true
    $closeButton.Enabled = $true
    [void]$form.ShowDialog()
} finally {
    Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
    $timer.Dispose()
    if ($null -ne $logo.Image) {
        $logo.Image.Dispose()
    }
    $form.Dispose()
}
