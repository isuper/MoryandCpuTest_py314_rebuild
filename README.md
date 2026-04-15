This directory contains a recovered Python source version of `MoryandCpuTest.exe`.

Facts confirmed from the original executable:

- It is a Windows `PyInstaller` one-file bundle.
- It was built against Python 3.7, not Python 3.14.
- The original entry script name inside the bundle is `MoryandCpuTset.py`.

What is included here:

- `main.py`: decompiled primary script recovered from the original executable.
- `requirements.txt`: baseline non-Qt runtime dependencies.
- `build_windows_py314.ps1`: Windows build script with Python-version and Qt-binding fallback logic.
- `.github/workflows/build-windows.yml`: GitHub Actions workflow for remote Windows builds.

Important limitations:

- This project was reconstructed from bytecode. It is close to source, but not guaranteed to be identical to the original authoring source.
- Building a Windows `.exe` should be done on Windows with Python 3.14 installed.
- Qt wheel availability is version-dependent. The build script now tries `PyQt5` first and falls back to `PySide6`.
- If Python 3.14 cannot build this project because dependency wheels are missing, the script falls back to Python 3.13 and then 3.12.

Build behavior:

1. Detects an installed Windows `py` launcher target in this order: `3.14`, `3.13`, `3.12`.
2. Creates a fresh virtual environment.
3. Installs base dependencies plus `PyInstaller`.
4. Tries `PyQt5`; if unavailable, tries `PySide6`.
5. Builds `dist\MoryandCpuTest.exe`.

Suggested Windows build steps:

1. Install Python 3.14 on Windows.
2. Open PowerShell in this directory.
3. Run `.\build_windows_py314.ps1`.

If you need to verify what version actually got used, the script prints it at startup.

No local Windows computer:

1. Create a new GitHub repository.
2. Upload this whole directory to the repository root.
3. Push the repository to GitHub.
4. Open the repository `Actions` tab.
5. Run the `Build Windows EXE` workflow manually.
6. Download the `MoryandCpuTest-windows-exe` artifact after the workflow finishes.

Other remote options:

- GitHub Actions: best free option for one-off remote Windows packaging.
- Microsoft Dev Box / Azure Windows VM: best if you need repeated builds and debugging.
- Borrowed Windows machine: simplest if you only need one final executable.
# MoryandCpuTest_py314_rebuild
