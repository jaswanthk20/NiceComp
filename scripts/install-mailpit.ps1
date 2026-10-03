$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$mailpitDirectory = Join-Path $projectRoot '.local/mailpit'
New-Item -ItemType Directory -Force -Path $mailpitDirectory | Out-Null
$archivePath = Join-Path $mailpitDirectory 'mailpit.zip'
Invoke-WebRequest -Uri 'https://github.com/axllent/mailpit/releases/download/v1.31.3/mailpit-windows-amd64.zip' -OutFile $archivePath
$expectedHash = '863E9502D4E0F14A78C0F91C5091797B1C7B7B7E3FC7E5EAB62E5770CE44B76E'
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash -ne $expectedHash) {
    throw 'Mailpit checksum does not match the pinned release. Do not run it.'
}
Expand-Archive -LiteralPath $archivePath -DestinationPath $mailpitDirectory -Force
Write-Output 'Mailpit v1.31.3 installed locally. Start it with .local/mailpit/mailpit.exe --listen 127.0.0.1:8025 --smtp 127.0.0.1:1025'
