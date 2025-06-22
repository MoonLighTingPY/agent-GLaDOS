if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Creating it now..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment."
        Read-Host "Press Enter to continue"
        exit 1
    }
}
& ".venv\Scripts\Activate.ps1"
Write-Host "Virtual environment activated successfully!"