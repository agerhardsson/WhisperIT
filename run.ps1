param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "update", "gui", "cli", "help")]
    [string]$Mode = "gui",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs = @()
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}

switch ($Mode) {
    "setup" { uv sync }
    "update" { uv lock --upgrade; uv sync }
    "gui" { uv run whisperit-gui @AppArgs }
    "cli" { uv run whisperit @AppArgs }
    "help" {
        Write-Output "Usage: .\run.ps1 [setup|update|gui|cli|help] [args...]"
    }
}
