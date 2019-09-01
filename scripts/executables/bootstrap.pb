EnableExplicit
Prototype.l EnumProcesses(a,b,c)
Global EnumProcesses.EnumProcesses
Procedure moveToTarget(source.s, target.s)
  CopyDirectory(source, target, "", #PB_FileSystem_Recursive|#PB_FileSystem_Force)
  DeleteDirectory(source, "", #PB_FileSystem_Recursive|#PB_FileSystem_Force)
EndProcedure
Procedure processExists(pid)
Define.l cb = 1024, result, bytesReturned
Dim pids.l(cb/4)
Repeat
result = EnumProcesses(@pids(0), cb, @bytesReturned)
If cb > bytesReturned : Break : EndIf
cb*2
ReDim pids(cb/4)
ForEver
Define.l nPids = bytesReturned/4
Define.l i
For i = 0 To nPids-1
  If pids(i) = pid
    ProcedureReturn 1
  EndIf
Next
    ProcedureReturn 0
  EndProcedure
Procedure WaitForProcessToEnd(pid.l, timeout.l)
  Protected h=OpenProcess_(#SYNCHRONIZE, 0, pid)
  If h
    WaitForSingleObject_(h, timeout)
    CloseHandle_(h)
  EndIf
EndProcedure
Procedure execute(program.s)
  ShellExecute_(#Null, "open", program, #Null, #Null, #SW_NORMAL)
EndProcedure
Procedure kill(pid, exitcode)
  Protected handle = OpenProcess_(#PROCESS_TERMINATE, 0, pid)
If handle > 0  
  Protected r=TerminateProcess_(handle, exitcode)
  CloseHandle_(handle)
  ProcedureReturn r
EndIf
ProcedureReturn 0
EndProcedure

Define sd.s{#MAX_PATH}
GetSystemDirectory_(@sd, #MAX_PATH-1)
OpenLibrary(0, sd+"\psapi.dll")
Global EnumProcesses = GetFunction(0, "EnumProcesses")
If CountProgramParameters() < 4
  MessageBox_(0, "Please note: this is a stand-alone bootstrapper For the autoupdate facility. It cannot be run independently.", "Update Bootstrapper", 0)
  End
EndIf
Define pid=Val(ProgramParameter(0))
Define source.s = ProgramParameter(1)
Define dest.s = ProgramParameter(2)
Define prg.s = ProgramParameter(3)
WaitForProcessToEnd(pid, 500)
kill(pid, 1)
WaitForProcessToEnd(pid, 500)
moveToTarget(source, dest)
execute(prg)

; IDE Options = PureBasic 4.51 (Windows - x86)
; CursorPosition = 62
; FirstLine = 7
; Folding = 1
; EnableUnicode
; EnableXP
; EnableAdmin
; Executable = bootstrap.exe
; Compiler = PureBasic 4.51 (Windows - x86)
; IncludeVersionInfo
; VersionField0 = 1,2,0
; VersionField1 = 5,0,1
; VersionField2 = Mongoose Enterprises
; VersionField3 = Autoupdate Bootstrapper
; VersionField4 = 2.0
; VersionField5 = 1.2.1
; VersionField6 = Moves files around and relaunches the updated application.
; VersionField7 = bootstrap
; VersionField8 = bootstrap.pb
; VersionField17 = 0409 English (United States)