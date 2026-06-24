#!/usr/bin/env python
"""
Wrapper to run Phase 5 tests via manage.py shell properly
"""

import subprocess
import sys
import os

os.chdir('c:\\Users\\DELL\\Desktop\\Management Info Sys')

# Read the phase5 script with UTF-8 encoding
with open('phase5_multi_school_isolation.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Execute via manage.py shell
process = subprocess.Popen(
    [sys.executable, 'manage.py', 'shell'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

stdout, stderr = process.communicate(input=code)
print(stdout)
if stderr:
    print("STDERR:")
    print(stderr)

sys.exit(process.returncode)
