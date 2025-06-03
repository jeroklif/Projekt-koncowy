# installResources.ps1
# Skrypt instalacyjny dla projektu konwertera formatów danych

Write-Host "Rozpoczynam instalację zależności dla projektu konwertera..." -ForegroundColor Green

# Sprawdzenie czy Python jest zainstalowany
try {
    $pythonVersion = python --version
    Write-Host "Znaleziono Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python nie jest zainstalowany lub nie jest dostępny w PATH" -ForegroundColor Red
    exit 1
}

# Sprawdzenie czy pip jest dostępny
try {
    $pipVersion = pip --version
    Write-Host "Znaleziono pip: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "pip nie jest dostępny" -ForegroundColor Red
    exit 1
}

# Aktualizacja pip
Write-Host "Aktualizacja pip..." -ForegroundColor Yellow
pip install --upgrade pip

# Instalacja głównych zależności
Write-Host "Instalacja PyYAML..." -ForegroundColor Yellow
pip install PyYAML==6.0.1

Write-Host "Instalacja pyinstaller..." -ForegroundColor Yellow
pip install pyinstaller==6.2.0

Write-Host "Instalacja PyQt5..." -ForegroundColor Yellow
pip install PyQt5==5.15.10

Write-Host "Instalacja dodatkowych zależności..." -ForegroundColor Yellow
pip install altgraph==0.17.4
pip install packaging==23.2
pip install pyinstaller-hooks-contrib==2023.10

# Sprawdzenie instalacji
Write-Host "Weryfikacja instalacji..." -ForegroundColor Yellow
python -c "import yaml; print('PyYAML zainstalowany')"
python -c "import PyInstaller; print('PyInstaller zainstalowany')"
python -c "import PyQt5; print('PyQt5 zainstalowany')"

Write-Host "Instalacja zakończona pomyślnie!" -ForegroundColor Green
Write-Host "Lista zainstalowanych pakietów:" -ForegroundColor Cyan
pip list

Write-Host "Aby zbudować projekt użyj komendy:" -ForegroundColor Cyan
Write-Host "pyinstaller --onefile converter.py" -ForegroundColor White
Write-Host "lub dla wersji z UI:" -ForegroundColor Cyan
Write-Host "pyinstaller --onefile --noconsole converter_ui.py" -ForegroundColor White