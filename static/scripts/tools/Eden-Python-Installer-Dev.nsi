; Define your application name
!define APPNAME "Python environment to develop Sahana Eden"
!define APPNAMEANDVERSION "Python environment to develop Sahana Eden"


; Main Install settings
Name "${APPNAMEANDVERSION}"
InstallDir "$PROGRAMFILES\Eden"
OutFile "Eden-Python-Installer-Dev.exe"
; This is where the dependencies are dumped before installation.
!define DEPSTORE "$TEMP\Edendependencies"

; Use compression
SetCompressor /SOLID LZMA

; Modern interface settings
!include "MUI.nsh"
!define MUI_ICON "favicon.ico"
!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
; Uncomment the following for Eclipse
;!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Set languages (first is default language)
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_RESERVEFILE_LANGDLL

Section "Python 2.6" Section1

	; Set Section properties
	SetOverwrite on

	; Set Section Files and Shortcuts
	SetOutPath "${DEPSTORE}"
	ReadRegStr $0 HKLM "SOFTWARE\Python\PythonCore\2.6\InstallPath" ""
	strCmp $0 "" python
	MessageBox MB_OK "A previous installation of Python 2.6 was found" 
	Goto done
python:
	; The Python installation stuff goes here - We enter this function if python isn't already present.
	File "python-2.6.6.msi"
	ExecWait '"msiexec" /i "${DEPSTORE}\python-2.6.6.msi"'
	RMDir /r ${DEPSTORE}
done:
SectionEnd

Section "Required Python Libraries" Section2
	ReadRegStr $0 HKLM "SOFTWARE\Python\PythonCore\2.6\InstallPath" ""
	strCmp $0 "" python
	Goto libraries
python:
	MessageBox MB_OK "Python 2.6 Installation was not found on the system."
	Goto done
libraries:
    ; Even if python and any of the following libraries are preinstalled - The installation remains the same.

	File "lxml-2.3.win32-py2.6.exe"
	ExecWait '${DEPSTORE}\lxml-2.3.win32-py2.6.exe'
	RMDir /r ${DEPSTORE}
	
	File "Shapely-1.2.12.win32-py2.6.exe"
	ExecWait '${DEPSTORE}\Shapely-1.2.12.win32-py2.6.exe'
	RMDir /r ${DEPSTORE}

	File "pywin32-214.win32-py2.6.exe"
	ExecWait '${DEPSTORE}\pywin32-214.win32-py2.6.exe'
	RMDir /r ${DEPSTORE}
	
	File "PIL-1.1.7.win32-py2.6.exe"
	ExecWait '${DEPSTORE}\PIL-1.1.7.win32-py2.6.exe'
	RMDir /r ${DEPSTORE}
	
	File "reportlab-2.4.win32-py2.6.exe"
	ExecWait '${DEPSTORE}\reportlab-2.4.win32-py2.6.exe'
	RMDir /r ${DEPSTORE}
	
	;File "xlrd-0.7.1.win32.exe"
	;ExecWait '${DEPSTORE}\xlrd-0.7.1.win32.exe'
	;RMDir /r ${DEPSTORE}

	File "xlwt-0.7.2.win32.exe"
	ExecWait '${DEPSTORE}\xlwt-0.7.2.win32.exe'
	RMDir /r ${DEPSTORE}

	File "pyserial-2.5.win32.exe"
	ExecWait '${DEPSTORE}\pyserial-2.5.win32.exe'
	RMDir /r ${DEPSTORE}
	
    ; Dev-only below
	File "pyreadline-1.5-win32-setup.exe"
	ExecWait '${DEPSTORE}\pyreadline-1.5-win32-setup.exe'
	RMDir /r ${DEPSTORE}
	
	File "ipython-0.10.win32-setup.exe"
	ExecWait '${DEPSTORE}\ipython-0.10.win32-setup.exe'
	RMDir /r ${DEPSTORE}
	
	File "bzr-2.3.4-1.win32-py2.6.exe"
	ExecWait '${DEPSTORE}\bzr-2.3.4-1.win32-py2.6.exe'
	RMDir /r ${DEPSTORE}
	
	;File "setuptools-0.6c11.win32-py2.6.exe"
	;ExecWait '${DEPSTORE}\setuptools-0.6c11.win32-py2.6.exe'
	;RMDir /r ${DEPSTORE}	
	
done:
	
SectionEnd

; Uncomment for Eclipse
;Section "Eclipse Environment" Section3 
;	ReadRegStr $0 HKLM "SOFTWARE\Python\PythonCore\2.6\InstallPath" ""
;	strCmp $0 "" python
;	Goto edeneclipse
;python:
;	MessageBox MB_OK "Python 2.6 Installation was not found on the system." 
;	Goto done	
;edeneclipse:
;	SetOverwrite off
;	SetOutPath "$INSTDIR\"
;	File /r "Sahana-Eden\*.*"
;done:
;SectionEnd	


; Modern install component descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
	!insertmacro MUI_DESCRIPTION_TEXT ${Section1} "Python 2.6"
	!insertmacro MUI_DESCRIPTION_TEXT ${Section2} "Python libraries needed to develop Eden"
;	!insertmacro MUI_DESCRIPTION_TEXT ${Section3} "Eclipse Environment"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

BrandingText "Eden"

; eof