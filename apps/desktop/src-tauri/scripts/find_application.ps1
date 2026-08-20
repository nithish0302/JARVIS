param(
    [Parameter(Mandatory=$true)]
    [string]$AppName
)

# 1. Search Start Apps
$startApp = Get-StartApps | Where-Object { $_.Name -like "*$AppName*" } | Select-Object -First 1 -ExpandProperty AppID
if ($startApp) {
    Write-Output "shell:appsFolder\$startApp"
    exit 0
}

# 2. Search AppData
$escaped = [regex]::Escape($AppName)
$appData = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs","$env:APPDATA" -Recurse -Depth 3 -Filter "*.exe" -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -match "^$escaped(\.exe)?$" } | 
    Select-Object -First 1 -ExpandProperty FullName

if ($appData) {
    Write-Output $appData
    exit 0
}
