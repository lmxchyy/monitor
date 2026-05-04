$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $RootDir '.venv\Scripts\python.exe'
$CsvPath = Join-Path $RootDir 'data\companies.csv'
$Today = Get-Date -Format 'yyyy-MM-dd'

function Test-MonitorPython {
    param([string]$Candidate)
    if (($Candidate -ne 'python') -and !(Test-Path $Candidate)) {
        return $false
    }
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $Candidate -c "import pymysql, sqlalchemy, requests, bs4, feedparser, yaml, jinja2; import greenlet._greenlet" 2>$null | Out-Null
    $ExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousErrorActionPreference
    return ($ExitCode -eq 0)
}

if (!(Test-MonitorPython $PythonExe)) {
    $PythonExe = 'python'
}

if (!(Test-Path $CsvPath)) {
    throw "companies.csv not found: $CsvPath"
}

Write-Host "[1/5] Start MySQL (Docker Compose)"
docker compose -f (Join-Path $RootDir 'docker\compose.yml') up -d

Write-Host "[2/5] Wait for MySQL to be ready"
do {
    Start-Sleep -Seconds 2
    docker exec monitor-mysql mysql -umonitor -pmonitor -e "SELECT 1" | Out-Null
    $ok = ($LASTEXITCODE -eq 0)
} until ($ok)

Write-Host "[3/5] Install Python requirements and Playwright browser"
& $PythonExe -m pip install -r (Join-Path $RootDir 'etl\requirements.txt')
& $PythonExe -m playwright install chromium

$env:MONITOR_DB_HOST = '127.0.0.1'
$env:MONITOR_DB_PORT = '3306'
$env:MONITOR_DB_USER = 'monitor'
$env:MONITOR_DB_PASSWORD = 'monitor'
$env:MONITOR_DB_NAME = 'monitor'

Write-Host "[4/5] Run ETL: import companies, hiring, funding, daily metrics"
& $PythonExe (Join-Path $RootDir 'etl\ensure_schema.py')
& $PythonExe (Join-Path $RootDir 'etl\import_companies.py') --csv $CsvPath
& $PythonExe (Join-Path $RootDir 'etl\run_hiring_daily.py') --date $Today
& $PythonExe (Join-Path $RootDir 'etl\run_funding_daily.py') --date $Today
& $PythonExe (Join-Path $RootDir 'etl\daily_job.py') --date $Today

Write-Host "[5/5] Generate results files"
& powershell -ExecutionPolicy Bypass -File (Join-Path $RootDir 'show_results.ps1')

Write-Host "Done. Date=$Today"
