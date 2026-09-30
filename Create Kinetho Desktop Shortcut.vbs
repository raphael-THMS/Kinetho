Option Explicit

Dim shell, fileSystem, appRoot, desktopPath, shortcutPath, launcherPath, iconPath, shortcut
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")
appRoot = fileSystem.GetParentFolderName(WScript.ScriptFullName)
desktopPath = shell.SpecialFolders("Desktop")
shortcutPath = fileSystem.BuildPath(desktopPath, "Kinetho.lnk")
launcherPath = fileSystem.BuildPath(appRoot, "Kinetho.vbs")
iconPath = fileSystem.BuildPath(appRoot, "Kinetho.ico")
If Not fileSystem.FileExists(launcherPath) Or Not fileSystem.FileExists(iconPath) Then
	MsgBox "Kinetho launcher or icon is missing. Re-extract the complete Kinetho folder.", vbCritical, "Kinetho"
	WScript.Quit 1
End If

Set shortcut = shell.CreateShortcut(shortcutPath)
shortcut.TargetPath = shell.ExpandEnvironmentStrings("%SystemRoot%\System32\wscript.exe")
shortcut.Arguments = Chr(34) & launcherPath & Chr(34)
shortcut.WorkingDirectory = appRoot
shortcut.IconLocation = iconPath & ",0"
shortcut.Description = "Launch Kinetho video processing and point annotation"
shortcut.WindowStyle = 1
shortcut.Save
