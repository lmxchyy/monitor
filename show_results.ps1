$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutDir = Join-Path $RootDir 'results'
$OutDate = Get-Date -Format 'yyyy-MM-dd'
$OutFile = Join-Path $OutDir ("results_{0}.txt" -f $OutDate)

$DbName = if ($env:MONITOR_DB_NAME) { $env:MONITOR_DB_NAME } else { 'monitor' }
$DbUser = if ($env:MONITOR_DB_USER) { $env:MONITOR_DB_USER } else { 'monitor' }
$DbPass = if ($env:MONITOR_DB_PASSWORD) { $env:MONITOR_DB_PASSWORD } else { 'monitor' }
$Container = if ($env:MONITOR_DB_CONTAINER) { $env:MONITOR_DB_CONTAINER } else { 'monitor-mysql' }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Invoke-MySqlQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql
    )

    docker exec $Container mysql --default-character-set=utf8mb4 ("-u{0}" -f $DbUser) ("-p{0}" -f $DbPass) $DbName -e $Sql
}

$txt = New-Object System.Collections.Generic.List[string]
$txt.Add("Generated: $(Get-Date -Format s)")
$txt.Add("")
$txt.Add("== Companies (top 20) ==")
$txt.Add((Invoke-MySqlQuery "SELECT id,name,aliases FROM companies ORDER BY id LIMIT 20;" | Out-String).TrimEnd())
$txt.Add("")
$txt.Add("== Hiring snapshots by date/channel ==")
$txt.Add((Invoke-MySqlQuery "SELECT snapshot_date, channel, COUNT(*) cnt FROM hiring_snapshots GROUP BY snapshot_date, channel ORDER BY snapshot_date DESC, channel;" | Out-String).TrimEnd())
$txt.Add("")
$txt.Add("== Latest hiring snapshots (10) ==")
$txt.Add((Invoke-MySqlQuery "SELECT h.id, h.snapshot_date, c.name, h.channel, h.open_jobs_count, h.keywords, h.source_url FROM hiring_snapshots h JOIN companies c ON c.id=h.company_id ORDER BY h.id DESC LIMIT 10;" | Out-String).TrimEnd())
$txt.Add("")
$txt.Add("== Funding events by source_type ==")
$txt.Add((Invoke-MySqlQuery "SELECT source_type, COUNT(*) cnt FROM funding_events GROUP BY source_type ORDER BY source_type;" | Out-String).TrimEnd())
$txt.Add("")
$txt.Add("== Latest funding events (10) ==")
$txt.Add((Invoke-MySqlQuery "SELECT f.id, c.name, f.source_type, f.event_date, f.source_url, f.raw_text FROM funding_events f JOIN companies c ON c.id=f.company_id ORDER BY f.id DESC LIMIT 10;" | Out-String).TrimEnd())
$txt.Add("")
$txt.Add("== Daily metrics (latest date, top 20) ==")
$txt.Add((Invoke-MySqlQuery "SELECT m.date, c.name, m.open_jobs_total, m.funding_last_90d_count, m.latest_funding_date FROM company_daily_metrics m JOIN companies c ON c.id=m.company_id ORDER BY m.date DESC, c.id LIMIT 20;" | Out-String).TrimEnd())

[System.IO.File]::WriteAllLines($OutFile, $txt, [System.Text.UTF8Encoding]::new($false))
Write-Output $OutFile

$PythonExe = Join-Path $RootDir '.venv\Scripts\python.exe'
$HtmlScript = Join-Path $RootDir 'show_results_html.py'

function Test-MonitorPython {
    param([string]$Candidate)
    if (($Candidate -ne 'python') -and !(Test-Path $Candidate)) {
        return $false
    }
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $Candidate -c "import pymysql, jinja2" 2>$null | Out-Null
    $ExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousErrorActionPreference
    return ($ExitCode -eq 0)
}

if (!(Test-MonitorPython $PythonExe)) {
    $PythonExe = 'python'
}

& $PythonExe $HtmlScript
