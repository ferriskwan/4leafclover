import sys
import os

print(f"Current python: {sys.executable}")
print(f"Arguments: {sys.argv}")

venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", ".venv")
venv_dir = os.path.abspath(venv_dir)
print(f"Target venv_dir: {venv_dir}")

if os.path.isdir(venv_dir):
    venv_python = os.path.join(venv_dir, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_dir, "bin", "python")
    print(f"Target venv_python: {venv_python}")
    if os.path.exists(venv_python) and os.path.abspath(sys.executable).lower() != os.path.abspath(venv_python).lower():
        print("Re-executing...")
        os.execv(venv_python, [venv_python] + sys.argv)
else:
    print("venv not found")
