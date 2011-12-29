cd tests
IF dummy==dummy%1 (
python nose.py
) ELSE (
python nose.py %1
)
PAUSE