Option Explicit

Dim shell, fileSystem, appRoot, startScript
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")
appRoot = fileSystem.GetParentFolderName(WScript.ScriptFullName)
startScript = fileSystem.BuildPath(appRoot, "Kinetho.bat")
If Not fileSystem.FileExists(startScript) Then
	MsgBox "Kinetho could not find Kinetho.bat in its application folder.", vbCritical, "Kinetho"
	WScript.Quit 1
End If
shell.CurrentDirectory = appRoot
shell.Run Chr(34) & startScript & Chr(34), 0, False
