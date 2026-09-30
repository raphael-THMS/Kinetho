@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ==========================================================
rem Video Tools (all-in-one)
rem - Designed for supplementary materials: simple, readable UI
rem - Uses ffmpeg from PATH or local <ROOT>\ffmpeg\bin
rem - Default workflow:
rem   1) Put raw videos in: Video edition\Videos_before_modifications
rem   2) Run this script, choose an action
rem   3) Outputs go to: <ROOT>\Videos and/or <ROOT>\Image folders
rem ==========================================================

call :init_paths
call :resolve_ffmpeg

echo ===========================================================
echo                 VIDEO TOOLS (FFMPEG)
echo ===========================================================
echo Root folder : %ROOT_DIR%
echo Input (raw) : %INPUT_RAW_DIR%
echo Videos out  : %OUTPUT_VIDEOS_DIR%
echo Images out  : %OUTPUT_IMAGES_DIR%
echo.

:MAIN_MENU
echo --------------------- MENU ----------------------
echo   1 = Fix doubled duration (x2 speed)
echo   2 = Enhance quality / brightness
echo   3 = Split videos by time (minutes)
echo   4 = Split videos by width/height (crop/split)
echo   5 = Extract 1 frame every X minutes
echo   6 = Merge videos by suffix (_1, _2, _3 ...)
echo   7 = Repair duration / timestamps (MP4)
echo.
echo   9 = Check FFmpeg setup instructions
echo   0 = Exit
echo -------------------------------------------------
set "CHOICE="
set /p CHOICE=^>^> Choose an option (0-9): 

rem If input is redirected and reaches EOF, avoid looping forever.
if errorlevel 1 goto :EOF

set "CHOICE=%CHOICE: =%"
if "%CHOICE%"=="" goto :MAIN_MENU

if "%CHOICE%"=="0" goto :EOF
if "%CHOICE%"=="1" call :action_fix_doubled_duration & goto :MAIN_MENU
if "%CHOICE%"=="2" call :action_enhance_quality & goto :MAIN_MENU
if "%CHOICE%"=="3" call :action_split_by_time & goto :MAIN_MENU
if "%CHOICE%"=="4" call :action_split_spatial & goto :MAIN_MENU
if "%CHOICE%"=="5" call :action_extract_frames & goto :MAIN_MENU
if "%CHOICE%"=="6" call :action_merge_by_suffix & goto :MAIN_MENU
if "%CHOICE%"=="7" call :action_repair_duration & goto :MAIN_MENU
if "%CHOICE%"=="9" call :action_setup_ffmpeg & call :resolve_ffmpeg & goto :MAIN_MENU

echo.
echo ERROR: Invalid choice.
pause
goto :MAIN_MENU

rem ------------------------
rem Init / Helpers
rem ------------------------
:init_paths
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%SCRIPT_DIR%\..") do set "ROOT_DIR=%%~fI"

set "INPUT_RAW_DIR=%SCRIPT_DIR%\Videos_before_modifications"
set "OUTPUT_VIDEOS_DIR=%ROOT_DIR%\Videos"
set "OUTPUT_IMAGES_DIR=%ROOT_DIR%\Image folders"
set "LOCAL_FFMPEG_DIR=%ROOT_DIR%\ffmpeg\bin"
set "LOCAL_FFMPEG_EXE=%LOCAL_FFMPEG_DIR%\ffmpeg.exe"

if not exist "%OUTPUT_VIDEOS_DIR%" mkdir "%OUTPUT_VIDEOS_DIR%" >nul 2>&1
if not exist "%OUTPUT_IMAGES_DIR%" mkdir "%OUTPUT_IMAGES_DIR%" >nul 2>&1
exit /b 0

:resolve_ffmpeg
set "FFMPEG="
if exist "%LOCAL_FFMPEG_EXE%" (
  set "FFMPEG=%LOCAL_FFMPEG_EXE%"
  goto :FFMPEG_OK
)
where ffmpeg >nul 2>&1
if not errorlevel 1 (
  set "FFMPEG=ffmpeg"
  goto :FFMPEG_OK
)
echo.
echo ERROR: ffmpeg not found.
echo - Option 1: install ffmpeg and add to PATH
echo - Option 2: place ffmpeg in: %LOCAL_FFMPEG_EXE%
echo.
pause
exit /b 1

:FFMPEG_OK
"%FFMPEG%" -hide_banner -version >nul 2>&1
if errorlevel 1 (
  echo.
  echo ERROR: ffmpeg command exists but cannot run.
  echo Command: %FFMPEG%
  pause
  exit /b 1
)
exit /b 0

:ask_keep_audio
set "AUDIO_OPT=-an"
set "KEEP_AUDIO="
echo Keep original audio in output?
echo   Y = yes
echo   N = no (default)
set /p KEEP_AUDIO=^>^> Keep audio (Y/N): 
set "KEEP_AUDIO=%KEEP_AUDIO: =%"
set "KEEP_AUDIO=%KEEP_AUDIO:~0,1%"
if /I "%KEEP_AUDIO%"=="Y" set "AUDIO_OPT="
exit /b 0

:ask_encode_profile
rem Output variables: V_CODEC, PROFILE_TAG
set "PROFILE="
echo Encoding profile:
echo   1 = Fast   (libx264, preset veryfast, CRF 18) [default]
echo   2 = HighQ  (libx264, preset slow,     CRF 16)
set /p PROFILE=^>^> Profile (1/2): 
if "%PROFILE%"=="" set "PROFILE=1"
if "%PROFILE%"=="2" (
  set "V_CODEC=-c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p"
  set "PROFILE_TAG=_HQ"
) else (
  set "V_CODEC=-c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p"
  set "PROFILE_TAG=_FAST"
)
exit /b 0

:select_video_input_dir
rem Output variable: WORK_INPUT_DIR
set "WORK_INPUT_DIR=%INPUT_RAW_DIR%"
set "INSEL="
echo.
echo Input folder:
echo   1 = Raw videos (Video edition\Videos_before_modifications) [default]
echo   2 = Processed videos (Videos)
set /p INSEL=^>^> Choose input (1/2): 
if "%INSEL%"=="2" set "WORK_INPUT_DIR=%OUTPUT_VIDEOS_DIR%"
exit /b 0

:ensure_input_raw
if not exist "%INPUT_RAW_DIR%" (
  echo.
  echo ERROR: Input folder does not exist:
  echo %INPUT_RAW_DIR%
  echo.
  echo Create it and put your videos inside.
  pause
  exit /b 1
)
exit /b 0

:ensure_any_video_in_dir
rem args: %1 = directory
set "_DIR=%~1"
if not exist "%_DIR%" (
  echo.
  echo ERROR: Folder does not exist:
  echo %_DIR%
  pause
  exit /b 1
)
set "FOUND=0"
for %%F in ("%_DIR%\*.mp4" "%_DIR%\*.avi" "%_DIR%\*.mov" "%_DIR%\*.mkv") do (
  if exist "%%~fF" set "FOUND=1"
)
if "%FOUND%"=="0" (
  echo.
  echo ERROR: No video files found in:
  echo %_DIR%
  echo Supported: mp4, avi, mov, mkv
  pause
  exit /b 1
)
exit /b 0

:clean_digits
rem Keeps only ASCII digits 0-9 in a variable (in-place).
rem Useful when terminal input contains hidden characters.
rem Usage: call :clean_digits VAR_NAME
setlocal EnableDelayedExpansion
set "VAR=%~1"
set "VAL=!%VAR%!"
set "OUT="
set "DONE="
for /L %%i in (0,1,2048) do (
  if not defined DONE (
    set "ch=!VAL:~%%i,1!"
    if "!ch!"=="" (
      set "DONE=1"
    ) else (
      for %%d in (0 1 2 3 4 5 6 7 8 9) do (
        if "!ch!"=="%%d" set "OUT=!OUT!!ch!"
      )
    )
  )
)
endlocal & set "%~1=%OUT%"
exit /b 0

:parse_minsec_to_sec
rem Parse a time expressed as minutes and optional seconds into total seconds.
rem Accepted inputs (spaces ignored):
rem   - "115"       -> 115:00
rem   - "115,45"    -> 115:45
rem   - "115:45"    -> 115:45
rem   - "115.45"    -> 115:45
rem Usage: call :parse_minsec_to_sec IN_VAR_NAME OUT_VAR_NAME
setlocal EnableDelayedExpansion
set "IN_VAR=%~1"
set "RAW=!%IN_VAR%!"
set "RAW=!RAW: =!"
if not defined RAW (
  endlocal & set "%~2=" & exit /b 1
)

rem Normalize delimiters to comma
set "RAW=!RAW::=,!"
set "RAW=!RAW:.=,!"
set "RAW=!RAW:;=,!"

rem Keep only digits and at most one comma
set "OUT="
set "SEEN_COMMA="
set "DONE="
for /L %%i in (0,1,128) do (
  if not defined DONE (
    set "ch=!RAW:~%%i,1!"
    if "!ch!"=="" (
      set "DONE=1"
    ) else if "!ch!"=="," (
      if not defined SEEN_COMMA (
        set "OUT=!OUT!,"
        set "SEEN_COMMA=1"
      )
    ) else (
      for %%d in (0 1 2 3 4 5 6 7 8 9) do (
        if "!ch!"=="%%d" set "OUT=!OUT!!ch!"
      )
    )
  )
)

set "CLEAN=!OUT!"
for /f "tokens=1,2 delims=," %%A in ("!CLEAN!") do (
  set "MM=%%A"
  set "SS=%%B"
)
if not defined MM set "MM=0"
if not defined SS set "SS=0"
if "!MM!"=="" set "MM=0"
if "!SS!"=="" set "SS=0"

set "MM_NUM=0"
set "SS_NUM=0"
set /a MM_NUM=MM >nul 2>nul
if errorlevel 1 (
  endlocal & set "%~2=" & exit /b 1
)
set /a SS_NUM=SS >nul 2>nul
if errorlevel 1 (
  endlocal & set "%~2=" & exit /b 1
)

if !MM_NUM! LSS 0 (
  endlocal & set "%~2=" & exit /b 1
)
if !SS_NUM! LSS 0 (
  endlocal & set "%~2=" & exit /b 1
)

set /a TOTAL_SEC=MM_NUM*60+SS_NUM >nul 2>nul
if errorlevel 1 (
  endlocal & set "%~2=" & exit /b 1
)

endlocal & set "%~2=%TOTAL_SEC%" & exit /b 0

rem ------------------------
rem Actions
rem ------------------------
:action_setup_ffmpeg
echo.
echo ===========================================================
echo                 FFMPEG SETUP
echo ===========================================================

if exist "%LOCAL_FFMPEG_EXE%" (
  echo OK: Local ffmpeg already present:
  echo %LOCAL_FFMPEG_EXE%
  "%LOCAL_FFMPEG_EXE%" -hide_banner -version
  pause
  exit /b 0
)

where ffmpeg >nul 2>&1
if not errorlevel 1 (
  echo FFmpeg is already available in PATH:
  ffmpeg -version
  pause
  exit /b 0
)

echo FFmpeg is not available.
echo Install FFmpeg and add its bin folder to PATH, or place the portable binary here:
echo %LOCAL_FFMPEG_EXE%
pause
exit /b 1

:action_fix_doubled_duration
call :select_video_input_dir
call :ensure_any_video_in_dir "%WORK_INPUT_DIR%" || exit /b 1
call :ask_encode_profile
call :ask_keep_audio

echo.
echo ===========================================================
echo               FIX DOUBLED DURATION (x2)
echo ===========================================================
echo Input : %WORK_INPUT_DIR%
echo Output: %OUTPUT_VIDEOS_DIR%
echo.

echo Choose fix mode:
echo   1 = Fix timestamps (setpts=0.5*PTS) [default]
echo   2 = Drop 1 frame out of 2 (if frames are duplicated)
set "MODE="
set /p MODE=^>^> Mode (1/2): 
if "%MODE%"=="" set "MODE=1"

for %%F in ("%WORK_INPUT_DIR%\*.mp4" "%WORK_INPUT_DIR%\*.avi" "%WORK_INPUT_DIR%\*.mov" "%WORK_INPUT_DIR%\*.mkv") do (
  if exist "%%~fF" (
    echo --------------------------------------------
    echo Processing: %%~nxF
    if "%MODE%"=="2" (
      "%FFMPEG%" -hide_banner -y -i "%%~fF" ^
        -vf "select='not(mod(n\,2))',setpts=N/FRAME_RATE/TB" ^
        %V_CODEC% %AUDIO_OPT% ^
        "%OUTPUT_VIDEOS_DIR%\%%~nF_FIXEDdrop2%PROFILE_TAG%.mp4"
    ) else (
      "%FFMPEG%" -hide_banner -y -i "%%~fF" ^
        -vf "setpts=0.5*PTS" ^
        %V_CODEC% %AUDIO_OPT% ^
        "%OUTPUT_VIDEOS_DIR%\%%~nF_FIXEDx2%PROFILE_TAG%.mp4"
    )
    echo.
  )
)

echo OK - Done.
pause
exit /b 0

:action_enhance_quality
call :select_video_input_dir
call :ensure_any_video_in_dir "%WORK_INPUT_DIR%" || exit /b 1
call :ask_encode_profile
call :ask_keep_audio

echo.
echo ===========================================================
echo             ENHANCE QUALITY / BRIGHTNESS
echo ===========================================================
echo Input : %WORK_INPUT_DIR%
echo Output: %OUTPUT_VIDEOS_DIR%
echo.

echo Select enhancement preset:
echo   1 = Brighten (gamma lift) - gentle
echo   2 = Denoise + slight sharpen
echo   3 = Brighten + denoise + sharpen [default]
echo   4 = Re-encode only (no visual filter)
set "PRESET="
set /p PRESET=^>^> Preset (1/2/3/4): 
if "%PRESET%"=="" set "PRESET=3"

set "VF="
set "TAG=_ENH"
if "%PRESET%"=="1" (
  set "VF=eq=gamma=0.85:contrast=1.05:brightness=0.02"
  set "TAG=_ENH_P1"
) else if "%PRESET%"=="2" (
  set "VF=hqdn3d=1.5:1.5:6:6,unsharp=5:5:0.35:3:3:0.0"
  set "TAG=_ENH_P2"
) else if "%PRESET%"=="3" (
  set "VF=eq=gamma=0.85:contrast=1.05:brightness=0.02,hqdn3d=1.5:1.5:6:6,unsharp=5:5:0.35:3:3:0.0"
  set "TAG=_ENH_P3"
) else if "%PRESET%"=="4" (
  set "VF="
  set "TAG=_ENH_P4"
) else (
  echo ERROR: Invalid preset.
  pause
  exit /b 1
)

for %%F in ("%WORK_INPUT_DIR%\*.mp4" "%WORK_INPUT_DIR%\*.avi" "%WORK_INPUT_DIR%\*.mov" "%WORK_INPUT_DIR%\*.mkv") do (
  if exist "%%~fF" (
    echo --------------------------------------------
    echo Processing: %%~nxF
    if defined VF (
      "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "%VF%" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF%TAG%%PROFILE_TAG%.mp4"
    ) else (
      "%FFMPEG%" -hide_banner -y -i "%%~fF" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF%TAG%%PROFILE_TAG%.mp4"
    )
    echo.
  )
)

echo OK - Done.
pause
exit /b 0

:action_split_by_time
call :select_video_input_dir
call :ensure_any_video_in_dir "%WORK_INPUT_DIR%" || exit /b 1

echo.
echo ===========================================================
echo                 SPLIT VIDEOS BY TIME
echo ===========================================================
echo Input : %WORK_INPUT_DIR%
echo Output: %OUTPUT_VIDEOS_DIR%
echo.

set "NB_PARTS="
set /p NB_PARTS=^>^> Number of parts to extract: 
call :clean_digits NB_PARTS
if "%NB_PARTS%"=="" (
  echo ERROR: Empty value.
  pause
  exit /b 1
)

set "NB_PARTS_NUM=0"
set /a NB_PARTS_NUM=NB_PARTS >nul 2>nul
if %NB_PARTS_NUM% LEQ 0 (
  echo ERROR: Number of parts must be ^> 0
  pause
  exit /b 1
)
set "NB_PARTS=%NB_PARTS_NUM%"

echo.
echo Enter the start time for each part:
echo   Format: minutes or minutes,seconds
echo   Example: 115,45
for /L %%i in (1,1,%NB_PARTS%) do (
  set "START_TXT="
  set /p START_TXT=   Part %%i starts at mm,ss: 
  set "START_TXT=!START_TXT: =!"
  set "START_SEC_NUM="
  call :parse_minsec_to_sec START_TXT START_SEC_NUM
  if "!START_SEC_NUM!"=="" (
    echo ERROR: Invalid start time for part %%i. Use mm or mm,ss
    pause
    exit /b 1
  )
  if !START_SEC_NUM! LSS 0 (
    echo ERROR: Start time must be ^>= 0 for part %%i.
    pause
    exit /b 1
  )
  set "START_SEC_%%i=!START_SEC_NUM!"
)

echo.
echo Duration mode:
echo   1 = Same duration for all parts [default]
echo   2 = Different duration for each part
set "DUR_MODE="
set /p DUR_MODE=^>^> Mode (1/2): 
set "DUR_MODE=%DUR_MODE: =%"
call :clean_digits DUR_MODE
if "%DUR_MODE%"=="" set "DUR_MODE=1"
if not "%DUR_MODE%"=="1" if not "%DUR_MODE%"=="2" set "DUR_MODE=1"

if "%DUR_MODE%"=="2" goto :SPLIT_TIME_DUR_PER_PART

rem Default: same duration for all parts
set "DUR_MODE=1"
set "PART_DURATION_TXT="
set /p PART_DURATION_TXT=^>^> Duration of each part mm,ss: 
set "PART_DURATION_TXT=%PART_DURATION_TXT: =%"
set "PART_DURATION_SEC="
call :parse_minsec_to_sec PART_DURATION_TXT PART_DURATION_SEC
if "%PART_DURATION_SEC%"=="" (
  echo ERROR: Empty duration.
  pause
  exit /b 1
)
set "PART_DURATION_SEC_NUM=0"
set /a PART_DURATION_SEC_NUM=PART_DURATION_SEC >nul 2>nul
if %PART_DURATION_SEC_NUM% LEQ 0 (
  echo ERROR: Duration must be ^> 0
  pause
  exit /b 1
)
set "PART_DURATION_SEC=%PART_DURATION_SEC_NUM%"
goto :SPLIT_TIME_DUR_DONE

:SPLIT_TIME_DUR_PER_PART
echo.
echo Enter the duration for each part:
echo   Format: minutes or minutes,seconds
echo   Example: 115,45
for /L %%i in (1,1,%NB_PARTS%) do (
  set "DUR_TXT="
  set /p DUR_TXT=   Part %%i duration mm,ss: 
  set "DUR_TXT=!DUR_TXT: =!"
  set "DUR_SEC_NUM="
  call :parse_minsec_to_sec DUR_TXT DUR_SEC_NUM
  if "!DUR_SEC_NUM!"=="" (
    echo ERROR: Empty duration for part %%i.
    pause
    exit /b 1
  )
  if !DUR_SEC_NUM! LEQ 0 (
    echo ERROR: Duration must be ^> 0 for part %%i.
    pause
    exit /b 1
  )
  set "DUR_SEC_%%i=!DUR_SEC_NUM!"
)

:SPLIT_TIME_DUR_DONE

call :ask_keep_audio

echo.
echo Split mode:
echo   1 = FAST   (stream copy, may cut at keyframes) [default]
echo   2 = PRECISE (re-encode, slower)
set "CUT_MODE="
set /p CUT_MODE=^>^> Mode (1/2): 
if "%CUT_MODE%"=="" set "CUT_MODE=1"

if "%CUT_MODE%"=="2" (
  call :ask_encode_profile
) else (
  set "V_CODEC=-c copy"
  set "PROFILE_TAG=_COPY"
)

for %%F in ("%WORK_INPUT_DIR%\*.mp4" "%WORK_INPUT_DIR%\*.avi" "%WORK_INPUT_DIR%\*.mov" "%WORK_INPUT_DIR%\*.mkv") do (
  if exist "%%~fF" (
    echo --------------------------------------------
    echo Processing: %%~nxF

    for /L %%i in (1,1,%NB_PARTS%) do (
      call set "START_SEC=%%START_SEC_%%i%%"
      set "START_SEC=!START_SEC: =!"
      if "!START_SEC!"=="" (
        echo ERROR: Start time for part %%i is invalid.
        pause
        exit /b 1
      )

      if "%DUR_MODE%"=="2" (
        call set "DUR_SEC=%%DUR_SEC_%%i%%"
        set "DUR_SEC=!DUR_SEC: =!"
        if "!DUR_SEC!"=="" (
          echo ERROR: Duration for part %%i is invalid.
          pause
          exit /b 1
        )
      ) else (
        set "DUR_SEC=%PART_DURATION_SEC%"
      )

      if "%CUT_MODE%"=="2" (
        rem Precise: -ss after -i
        "%FFMPEG%" -hide_banner -y -i "%%~fF" -ss !START_SEC! -t !DUR_SEC! %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_part%%i%PROFILE_TAG%.mp4"
      ) else (
        rem Fast: -ss before -i
        "%FFMPEG%" -hide_banner -y -ss !START_SEC! -i "%%~fF" -t !DUR_SEC! %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_part%%i%PROFILE_TAG%.mp4"
      )
    )

    echo.
  )
)

echo OK - Done.
pause
exit /b 0

:action_split_spatial
call :select_video_input_dir
call :ensure_any_video_in_dir "%WORK_INPUT_DIR%" || exit /b 1
call :ask_encode_profile
call :ask_keep_audio

echo.
echo ===========================================================
echo              SPLIT BY WIDTH/HEIGHT (CROP)
echo ===========================================================
echo Input : %WORK_INPUT_DIR%
echo Output: %OUTPUT_VIDEOS_DIR%
echo.

echo Select operation mode:
echo   1 = Crop a single region
echo   2 = Split into 2 equal halves (H or V)
echo   4 = Split into 4 quadrants (2x2)
set "N_SUB="
set /p N_SUB=^>^> Mode (1/2/4): 

if "%N_SUB%"=="1" goto :SPATIAL_MODE_ONE
if "%N_SUB%"=="2" goto :SPATIAL_MODE_TWO
if "%N_SUB%"=="4" goto :SPATIAL_MODE_FOUR

echo ERROR: Supported only: 1, 2, 4
pause
exit /b 1

:SPATIAL_MODE_ONE
echo.
echo Crop sub-mode:
echo   1 = Equal bands (H or V, keep one slice among N)
echo   2 = Manual margins (fractions)
set "CROP_MODE="
set /p CROP_MODE=^>^> Sub-mode (1/2): 

if "%CROP_MODE%"=="1" goto :SPATIAL_ONE_BANDS
if "%CROP_MODE%"=="2" goto :SPATIAL_ONE_MANUAL

echo ERROR: Invalid sub-mode.
pause
exit /b 1

:SPATIAL_ONE_BANDS
echo.
echo Choose direction:
echo   H = Horizontal bands (top->bottom)
echo   V = Vertical bands   (left->right)
set "CUT_DIR="
set /p CUT_DIR=^>^> Direction (H/V): 
set "CUT_DIR=%CUT_DIR: =%"
set "CUT_DIR=%CUT_DIR:~0,1%"
if /I not "%CUT_DIR%"=="H" if /I not "%CUT_DIR%"=="V" (
  echo ERROR: Invalid choice.
  pause
  exit /b 1
)

set "NB_PARTS="
set /p NB_PARTS=^>^> Divide image into how many equal slices? 
if "%NB_PARTS%"=="" (
  echo ERROR: Invalid number.
  pause
  exit /b 1
)

set "KEEP_IDX="
set /p KEEP_IDX=^>^> Keep which slice index (1-%NB_PARTS%): 
if "%KEEP_IDX%"=="" (
  echo ERROR: Invalid index.
  pause
  exit /b 1
)

if /I "%CUT_DIR%"=="V" (
  set "CROP_EXPR=crop=iw/%NB_PARTS%:ih:(%KEEP_IDX%-1)*iw/%NB_PARTS%:0"
) else (
  set "CROP_EXPR=crop=iw:ih/%NB_PARTS%:0:(%KEEP_IDX%-1)*ih/%NB_PARTS%"
)

for %%F in ("%WORK_INPUT_DIR%\*.mp4" "%WORK_INPUT_DIR%\*.avi" "%WORK_INPUT_DIR%\*.mov" "%WORK_INPUT_DIR%\*.mkv") do (
  if exist "%%~fF" (
    echo --------------------------------------------
    echo Cropping: %%~nxF
    "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "%CROP_EXPR%" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_CROP%PROFILE_TAG%.mp4"
    echo.
  )
)

echo OK - Done.
pause
exit /b 0

:SPATIAL_ONE_MANUAL
echo.
echo Enter margins as fractions between 0 and 0.5
echo Example: 0.10 = 10 percent
echo.
set "LEFT_F="
set "RIGHT_F="
set "TOP_F="
set "BOT_F="
set /p LEFT_F=^>^> Left margin  (e.g. 0.10): 
set /p RIGHT_F=^>^> Right margin (e.g. 0.10): 
set /p TOP_F=^>^> Top margin   (e.g. 0.00): 
set /p BOT_F=^>^> Bottom margin(e.g. 0.20): 

set "CROP_EXPR=crop=iw*(1-%LEFT_F%-%RIGHT_F%):ih*(1-%TOP_F%-%BOT_F%):iw*%LEFT_F%:ih*%TOP_F%"

for %%F in ("%WORK_INPUT_DIR%\*.mp4" "%WORK_INPUT_DIR%\*.avi" "%WORK_INPUT_DIR%\*.mov" "%WORK_INPUT_DIR%\*.mkv") do (
  if exist "%%~fF" (
    echo --------------------------------------------
    echo Cropping: %%~nxF
    "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "%CROP_EXPR%" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_CROP_MANUAL%PROFILE_TAG%.mp4"
    echo.
  )
)

echo OK - Done.
pause
exit /b 0

:SPATIAL_MODE_TWO
echo.
echo Choose split direction:
echo   H = Horizontal (top/bottom)
echo   V = Vertical   (left/right)
set "CUT_DIR="
set /p CUT_DIR=^>^> Direction (H/V): 
set "CUT_DIR=%CUT_DIR: =%"
set "CUT_DIR=%CUT_DIR:~0,1%"
if /I not "%CUT_DIR%"=="H" if /I not "%CUT_DIR%"=="V" (
  echo ERROR: Invalid choice.
  pause
  exit /b 1
)

for %%F in ("%WORK_INPUT_DIR%\*.mp4" "%WORK_INPUT_DIR%\*.avi" "%WORK_INPUT_DIR%\*.mov" "%WORK_INPUT_DIR%\*.mkv") do (
  if exist "%%~fF" (
    echo --------------------------------------------
    echo Splitting: %%~nxF
    if /I "%CUT_DIR%"=="V" (
      "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "crop=iw/2:ih:0:0" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_V1%PROFILE_TAG%.mp4"
      "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "crop=iw/2:ih:iw/2:0" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_V2%PROFILE_TAG%.mp4"
    ) else (
      "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "crop=iw:ih/2:0:0" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_H1%PROFILE_TAG%.mp4"
      "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "crop=iw:ih/2:0:ih/2" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_H2%PROFILE_TAG%.mp4"
    )
    echo.
  )
)

echo OK - Done.
pause
exit /b 0

:SPATIAL_MODE_FOUR
for %%F in ("%WORK_INPUT_DIR%\*.mp4" "%WORK_INPUT_DIR%\*.avi" "%WORK_INPUT_DIR%\*.mov" "%WORK_INPUT_DIR%\*.mkv") do (
  if exist "%%~fF" (
    echo --------------------------------------------
    echo Splitting into 4: %%~nxF
    "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "crop=iw/2:ih/2:0:0" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_Q1%PROFILE_TAG%.mp4"
    "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "crop=iw/2:ih/2:iw/2:0" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_Q2%PROFILE_TAG%.mp4"
    "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "crop=iw/2:ih/2:0:ih/2" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_Q3%PROFILE_TAG%.mp4"
    "%FFMPEG%" -hide_banner -y -i "%%~fF" -vf "crop=iw/2:ih/2:iw/2:ih/2" %V_CODEC% %AUDIO_OPT% "%OUTPUT_VIDEOS_DIR%\%%~nF_Q4%PROFILE_TAG%.mp4"
    echo.
  )
)

echo OK - Done.
pause
exit /b 0

:action_extract_frames
call :ensure_any_video_in_dir "%OUTPUT_VIDEOS_DIR%" || exit /b 1

echo.
echo ===========================================================
echo           EXTRACT 1 FRAME EVERY X MINUTES
echo ===========================================================
echo Input videos : %OUTPUT_VIDEOS_DIR%
echo Output images: %OUTPUT_IMAGES_DIR%
echo.

set "X_MIN="
set /p X_MIN=^>^> Sampling interval X (minutes, integer): 
if "%X_MIN%"=="" (
  echo ERROR: X is empty.
  pause
  exit /b 1
)

set /a X_SEC=%X_MIN%*60 >nul 2>&1
if errorlevel 1 (
  echo ERROR: X must be an integer number of minutes.
  pause
  exit /b 1
)
if %X_SEC% LEQ 0 (
  echo ERROR: X must be > 0.
  pause
  exit /b 1
)

echo.
echo Output image format:
echo   1 = JPG (default)
echo   2 = PNG
set "IMG_FMT="
set /p IMG_FMT=^>^> 1/2: 
if "%IMG_FMT%"=="" set "IMG_FMT=1"

set "EXT=jpg"
set "IMG_OPTS=-q:v 2"
if "%IMG_FMT%"=="2" (
  set "EXT=png"
  set "IMG_OPTS="
)

for %%F in ("%OUTPUT_VIDEOS_DIR%\*.mp4" "%OUTPUT_VIDEOS_DIR%\*.avi" "%OUTPUT_VIDEOS_DIR%\*.mov" "%OUTPUT_VIDEOS_DIR%\*.mkv") do (
  if exist "%%~fF" (
    set "VID_NAME=%%~nF"
    set "OUT_DIR=%OUTPUT_IMAGES_DIR%\!VID_NAME!"
    if not exist "!OUT_DIR!" mkdir "!OUT_DIR!" >nul 2>&1

    echo --------------------------------------------
    echo Video: %%~nxF
    echo Out  : !OUT_DIR!

    "%FFMPEG%" -hide_banner -y -i "%%~fF" ^
      -vf "fps=1/%X_SEC%" ^
      -vsync vfr ^
      !IMG_OPTS! ^
      "!OUT_DIR!\frame_%%06d.%EXT%"

    echo.
  )
)

echo OK - Done.
pause
exit /b 0

:action_merge_by_suffix
call :select_video_input_dir
call :ensure_any_video_in_dir "%WORK_INPUT_DIR%" || exit /b 1

echo.
echo ===========================================================
echo                 MERGE VIDEOS BY SUFFIX
echo ===========================================================
echo Naming convention (example):
echo   MyVideo_1.mp4, MyVideo_2.mp4, MyVideo_3.mp4
echo The script will merge into:
echo   MyVideo_MERGED.mp4
echo.
echo Input : %WORK_INPUT_DIR%
echo Output: %OUTPUT_VIDEOS_DIR%
echo.
echo NOTE: FAST mode uses ffmpeg "concat" in stream copy.
echo       If source parts have imperfect timestamps, final duration can be wrong/shorter.
echo       SAFE mode re-encodes and is recommended for reliable duration.
echo.

echo Merge mode:
echo   1 = FAST (stream copy, quicker, may keep bad timestamps)
echo   2 = SAFE (re-encode to fix timestamps) [recommended/default]
set "MERGE_MODE="
set /p MERGE_MODE=^>^> Mode (1/2): 
set "MERGE_MODE=%MERGE_MODE: =%"
call :clean_digits MERGE_MODE
if "%MERGE_MODE%"=="" set "MERGE_MODE=2"
if not "%MERGE_MODE%"=="1" if not "%MERGE_MODE%"=="2" set "MERGE_MODE=2"

set "FFMPEG_CMD=%FFMPEG%"

set "MERGE_PS1=%SCRIPT_DIR%\merge_by_suffix.ps1"
if not exist "%MERGE_PS1%" (
  echo ERROR: Missing helper script "merge_by_suffix.ps1".
  echo Expected here:
  echo - %SCRIPT_DIR%\merge_by_suffix.ps1
  pause
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%MERGE_PS1%" -InputDir "%WORK_INPUT_DIR%" -OutputDir "%OUTPUT_VIDEOS_DIR%" -Ffmpeg "%FFMPEG_CMD%" -Mode "%MERGE_MODE%"
if errorlevel 1 (
  echo.
  echo ERROR: Merge failed.
  pause
  exit /b 1
)

echo.
echo OK - Merge step finished.
pause
exit /b 0

:action_repair_duration
call :select_video_input_dir
call :ensure_any_video_in_dir "%WORK_INPUT_DIR%" || exit /b 1

echo.
echo ===========================================================
echo          REPAIR DURATION / TIMESTAMPS (MP4)
echo ===========================================================
echo Input : %WORK_INPUT_DIR%
echo Output: %OUTPUT_VIDEOS_DIR%
echo.
echo Use this if a video shows a wrong duration (e.g. 35 min instead of 7 h)
echo but you suspect the file still contains the full recording.
echo.
echo Repair mode:
echo   1 = FAST  (remux / copy, regenerate timestamps) [default]
echo   2 = SAFE  (re-encode, slower, fixes most timestamp problems)
set "REP_MODE="
set /p REP_MODE=^>^> Mode (1/2): 
set "REP_MODE=%REP_MODE: =%"
call :clean_digits REP_MODE
if "%REP_MODE%"=="" set "REP_MODE=1"
if not "%REP_MODE%"=="1" if not "%REP_MODE%"=="2" set "REP_MODE=1"

for %%F in ("%WORK_INPUT_DIR%\*.mp4" "%WORK_INPUT_DIR%\*.avi" "%WORK_INPUT_DIR%\*.mov" "%WORK_INPUT_DIR%\*.mkv") do (
  if exist "%%~fF" (
    echo --------------------------------------------
    echo Repairing: %%~nxF
    if "%REP_MODE%"=="2" (
      "%FFMPEG%" -hide_banner -y -err_detect ignore_err -fflags +genpts -i "%%~fF" ^
        -map 0 -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p ^
        -c:a aac -b:a 192k -movflags +faststart ^
        "%OUTPUT_VIDEOS_DIR%\%%~nF_REPAIRED_REENC.mp4"
    ) else (
      "%FFMPEG%" -hide_banner -y -err_detect ignore_err -fflags +genpts -i "%%~fF" ^
        -map 0 -c copy -avoid_negative_ts make_zero -movflags +faststart ^
        "%OUTPUT_VIDEOS_DIR%\%%~nF_REPAIRED_COPY.mp4"
    )
    echo.
  )
)

echo OK - Repair finished.
pause
exit /b 0
