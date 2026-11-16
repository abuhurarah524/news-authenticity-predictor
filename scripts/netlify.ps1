param(
    [ValidateSet('login', 'status', 'deploy')]
    [string]$Action = 'deploy'
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$runtime = Get-ChildItem -LiteralPath (Join-Path $projectRoot '.tools') -Directory -Filter 'node-v*-win-x64' |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $runtime) {
    throw 'Run .\.venv\Scripts\python.exe scripts\setup_node.py first.'
}
$nodePath = Join-Path $runtime.FullName 'node.exe'
$cliPath = Join-Path $projectRoot 'node_modules\netlify-cli\bin\run.js'
if (-not (Test-Path -LiteralPath $cliPath)) {
    throw 'Install the package.json dependencies with npm install first.'
}
$previousPath = $env:PATH
Push-Location -LiteralPath $projectRoot
try {
    $env:PATH = $runtime.FullName + ';' + $env:PATH
    if ($Action -eq 'deploy') {
        & $nodePath $cliPath deploy --prod --no-build
    } else {
        & $nodePath $cliPath $Action
    }
    if ($LASTEXITCODE -ne 0) { throw "Netlify $Action did not complete successfully." }
} finally {
    $env:PATH = $previousPath
    Pop-Location
}
