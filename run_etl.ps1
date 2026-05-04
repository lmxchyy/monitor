param(
    [string]$Date = $(Get-Date -Format 'yyyy-MM-dd'),
    [string]$Csv = ''
)

$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $RootDir '.venv\Scripts\python.exe'
$CsvPath = if ($Csv) { $Csv } else { Join-Path $RootDir 'data\companies.csv' }

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

$env:MONITOR_DB_HOST = '127.0.0.1'
$env:MONITOR_DB_PORT = '3306'
$env:MONITOR_DB_USER = 'monitor'
$env:MONITOR_DB_PASSWORD = 'monitor'
$env:MONITOR_DB_NAME = 'monitor'

Write-Host "Ensure database schema"
& $PythonExe (Join-Path $RootDir 'etl\ensure_schema.py')

Write-Host "Run import_companies.py"
& $PythonExe (Join-Path $RootDir 'etl\import_companies.py') --csv $CsvPath

Write-Host "Run run_hiring_daily.py"
& $PythonExe (Join-Path $RootDir 'etl\run_hiring_daily.py') --date $Date

Write-Host "Run run_funding_daily.py"
& $PythonExe (Join-Path $RootDir 'etl\run_funding_daily.py') --date $Date

Write-Host "Run daily_job.py"
& $PythonExe (Join-Path $RootDir 'etl\daily_job.py') --date $Date

Write-Host "Generate HTML results"
& $PythonExe (Join-Path $RootDir 'show_results_html.py')

Write-Host "Done. Date=$Date"
