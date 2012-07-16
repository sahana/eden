@echo off
IF dummy==dummy%1 (
    set application=eden
) ELSE IF dummy==dummy%2 (
    IF %1==gis (
        set application=eden
        set arg=gis
    ) ELSE (
        set application=%1
    )
) ELSE (
    set application=%1
    set arg=%2
)

c:
cd ..\..\..\..\..\web2py
IF dummy==dummy%arg% (
    python web2py.py -S %application% -M -R applications/%application%/static/scripts/tools/build.sahana.py
) ELSE (
    python web2py.py -S %application% -M -R applications/%application%/static/scripts/tools/build.sahana.py -A %arg%
)
