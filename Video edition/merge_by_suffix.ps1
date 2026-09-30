param(
  [Parameter(Mandatory=$true)][string]$InputDir,
  [Parameter(Mandatory=$true)][string]$OutputDir,
  [Parameter(Mandatory=$true)][string]$Ffmpeg,
  [Parameter(Mandatory=$false)][string]$Mode = '1'
)

$ErrorActionPreference = 'Stop'

function Write-Utf8NoBomLines {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string[]]$Lines
  )
  $enc = [System.Text.UTF8Encoding]::new($false)
  [System.IO.File]::WriteAllLines($Path, $Lines, $enc)
}

$ffmpegExe = $Ffmpeg.Trim('"')

if (-not (Test-Path -LiteralPath $InputDir)) {
  throw "Input folder not found: $InputDir"
}
if (-not (Test-Path -LiteralPath $OutputDir)) {
  New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$extSet = @('.mp4', '.avi', '.mov', '.mkv')
$files = Get-ChildItem -LiteralPath $InputDir -File -ErrorAction Stop |
  Where-Object { $extSet -contains $_.Extension.ToLowerInvariant() }

$matches = foreach ($f in $files) {
  $m = [regex]::Match($f.BaseName, '^(?<base>.+)_(?<idx>\d+)$')
  if ($m.Success) {
    [pscustomobject]@{
      File = $f
      Base = $m.Groups['base'].Value
      Idx  = [int]$m.Groups['idx'].Value
      Ext  = $f.Extension.ToLowerInvariant()
    }
  }
}

if (-not $matches) {
  Write-Host 'No files matched the pattern *_<number>.* in:'
  Write-Host $InputDir
  exit 0
}

$groups = $matches | Group-Object Base
Write-Host ("Groups found: {0}" -f $groups.Count)

$hadFailure = $false

foreach ($g in $groups) {
  $items = $g.Group | Sort-Object Idx
  if ($items.Count -lt 2) { continue }

  $extUnique = @($items | Select-Object -ExpandProperty Ext -Unique)
  if ($extUnique.Count -ne 1) {
    Write-Warning ("Skip {0}: mixed extensions ({1})" -f $g.Name, ($extUnique -join ', '))
    continue
  }

  $outExt = $extUnique[0]

  $outFile = Join-Path $OutputDir ($g.Name + '_MERGED' + $outExt)
  if ($Mode -eq '2') {
    $outFile = Join-Path $OutputDir ($g.Name + '_MERGED.mp4')
  }
  $listFile = Join-Path $env:TEMP ('ffmpeg_concat_' + [guid]::NewGuid().ToString('N') + '.txt')

  $lines = foreach ($it in $items) {
    $p = $it.File.FullName
    # ffmpeg concat file format uses single quotes; single quotes in paths are rare on Windows.
    if ($p -like "*'*" ) {
      $p = $p -replace "'", "\\'"
    }
    "file '$p'"
  }

  Write-Utf8NoBomLines -Path $listFile -Lines $lines

  Write-Host ("--- Merge: {0} ({1} parts) -> {2}" -f $g.Name, $items.Count, $outFile)

  if ($Mode -eq '2') {
    # SAFE: re-encode to regenerate timestamps and avoid non-monotonic DTS issues.
    & $ffmpegExe -hide_banner -stats -loglevel warning -y -fflags +genpts -f concat -safe 0 -i $listFile `
      -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart $outFile
  } else {
    # FAST: stream copy (may warn about DTS if segments have odd timestamps)
    & $ffmpegExe -hide_banner -stats -loglevel warning -y -fflags +genpts -avoid_negative_ts make_zero -f concat -safe 0 -i $listFile -c copy -movflags +faststart $outFile
  }
  $code = $LASTEXITCODE

  Remove-Item -LiteralPath $listFile -Force -ErrorAction SilentlyContinue

  if ($code -ne 0) {
    Write-Warning ("ffmpeg failed for {0}. Ensure all parts have same codec/resolution/fps, or re-encode first." -f $g.Name)
    $hadFailure = $true
  }
}

if ($hadFailure) { exit 2 }
exit 0
