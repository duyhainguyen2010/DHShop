param([switch]$Setup, [string]$MySqlBin = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Can cai Python 3.12 truoc.' }
    $Setup = $true
}
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if ($Setup) {
    & $pythonPath -m pip install --isolated --index-url https://pypi.org/simple -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Khong cai duoc thu vien.' }
}
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
$dbConfig = @{}
Get-Content -LiteralPath '.env' | ForEach-Object {
    if ($_ -match '^([A-Z_]+)=(.*)$') { $dbConfig[$Matches[1]] = $Matches[2] }
}
$dbPort = [int]$dbConfig['DB_PORT']
$dbHost = $dbConfig['DB_HOST']
$connectionReady = $false
$tcp = [Net.Sockets.TcpClient]::new()
try { $tcp.Connect($dbHost, $dbPort); $connectionReady = $true } catch {} finally { $tcp.Dispose() }
if (-not $connectionReady -and $dbPort -eq 3308 -and $dbHost -eq '127.0.0.1') {
    if (-not $MySqlBin) {
        $servicePath = (Get-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Services\wampmysqld64' -ErrorAction SilentlyContinue).ImagePath
        if ($servicePath -match '(?i)([a-z]:\\.+?\\bin)\\mysqld.exe') { $MySqlBin = $Matches[1] }
    }
    $serverPath = Join-Path $MySqlBin 'mysqld.exe'
    if (-not (Test-Path -LiteralPath $serverPath)) { throw 'Bat MySQL va sua DB_PORT trong .env, hoac truyen -MySqlBin duong_dan_bin.' }
    $mysqlBase = (Split-Path -Parent $MySqlBin).Replace('\', '/')
    $mysqlData = (Join-Path $PSScriptRoot 'runtime\mysql').Replace('\', '/')
    $mysqlParent = Split-Path -Parent $mysqlData
    if (-not (Test-Path -LiteralPath $mysqlParent)) { New-Item -ItemType Directory -Path $mysqlParent | Out-Null }
    if (-not (Test-Path -LiteralPath (Join-Path $mysqlData 'mysql'))) {
        & $serverPath --no-defaults --initialize-insecure "--basedir=$mysqlBase" "--datadir=$mysqlData" --innodb-undo-log-truncate=OFF --console
        if ($LASTEXITCODE -ne 0) { throw 'Khong khoi tao duoc MySQL.' }
    }
    $serverArgs = @('--no-defaults', ('--basedir="{0}"' -f $mysqlBase), ('--datadir="{0}"' -f $mysqlData), '--port=3308', '--bind-address=127.0.0.1', '--mysqlx=OFF', '--innodb-undo-log-truncate=OFF')
    Start-Process -FilePath $serverPath -ArgumentList $serverArgs -WindowStyle Hidden | Out-Null
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 500
        $tcp = [Net.Sockets.TcpClient]::new()
        try { $tcp.Connect($dbHost, $dbPort); $connectionReady = $true; break } catch {} finally { $tcp.Dispose() }
    }
}
& $pythonPath scripts\create_database.py
if ($LASTEXITCODE -ne 0) { throw 'Khong ket noi duoc MySQL. Kiem tra DB_HOST, DB_PORT, DB_USER, DB_PASSWORD trong .env.' }
& $pythonPath manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw 'Migration that bai.' }
& $pythonPath khoi_tao_du_lieu.py
if ($LASTEXITCODE -ne 0) { throw 'Khoi tao du lieu that bai.' }
$env:DEBUG = 'True'
Write-Host 'DHShop: http://127.0.0.1:8000/ | Admin: /admin/ | Ctrl+C de dung web'
& $pythonPath manage.py runserver 127.0.0.1:8000
