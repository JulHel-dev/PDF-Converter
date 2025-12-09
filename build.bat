@echo off
REM ========================================
REM  Building PDF-Converter as Windows .exe
REM ========================================
echo.
echo ========================================
echo  Building PDF-Converter as Windows .exe
echo ========================================
echo.

REM Check Python is available
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Install PyInstaller
echo Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Build executable
echo.
echo Building executable...
pyinstaller PDF-Converter.spec
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Build Complete!
echo  Output: dist\PDF-Converter.exe
echo ========================================
echo.

REM Create distribution folder structure
echo Creating distribution folders...
if not exist "dist\Log" mkdir "dist\Log"
if not exist "dist\Log\diagnostics" mkdir "dist\Log\diagnostics"
if not exist "dist\Input" mkdir "dist\Input"
if not exist "dist\Output" mkdir "dist\Output"

REM Copy documentation
if exist "README.md" copy "README.md" "dist\" > nul
if exist "docs" xcopy "docs" "dist\docs\" /E /I /Q > nul

echo.
echo ========================================
echo  Distribution ready in dist\ folder
echo  
echo  To run: dist\PDF-Converter.exe
echo  
echo  For GUI mode: dist\PDF-Converter.exe --gui
echo ========================================
echo.

pause
