param(
    [string]$Root = (Join-Path (Split-Path -Parent $PSScriptRoot) 'tracks\demos'),
    [switch]$IncludePublisher
)

$ErrorActionPreference = 'Stop'
$index = Join-Path $Root 'index.tsv'
$pdfDir = Join-Path $Root 'pdf'
New-Item -ItemType Directory -Path $pdfDir -Force | Out-Null
$rows = Import-Csv -LiteralPath $index -Delimiter "`t"

$downloaded = 0
$failed = 0
foreach ($row in $rows) {
    $destination = Join-Path $pdfDir $row.filename
    if (Test-Path -LiteralPath $destination) {
        Write-Host "SKIP $($row.paper_id) already present"
        continue
    }
    if (-not $row.pdf_url) {
        Write-Host "MISS $($row.paper_id) no PDF URL"
        $failed++
        continue
    }
    if ($row.pdf_source -eq 'publisher' -and -not $IncludePublisher) {
        Write-Host "MISS $($row.paper_id) publisher-only"
        $failed++
        continue
    }
    try {
        Write-Host "GET  $($row.paper_id) [$($row.pdf_source)]"
        Invoke-WebRequest -Uri $row.pdf_url -OutFile $destination -Headers @{
            'User-Agent' = 'Mozilla/5.0 (compatible; research corpus builder)'
            'Accept' = 'application/pdf'
        }
        $stream = [System.IO.File]::OpenRead($destination)
        try {
            $header = New-Object byte[] 5
            [void]$stream.Read($header, 0, 5)
        }
        finally {
            $stream.Dispose()
        }
        if ([System.Text.Encoding]::ASCII.GetString($header) -ne '%PDF-') {
            Remove-Item -LiteralPath $destination -Force
            throw 'response was not a PDF'
        }
        $size = (Get-Item -LiteralPath $destination).Length
        Write-Host "OK   $($row.paper_id) $size bytes"
        $downloaded++
    }
    catch {
        if (Test-Path -LiteralPath $destination) {
            Remove-Item -LiteralPath $destination -Force
        }
        Write-Warning "FAIL $($row.paper_id): $($_.Exception.Message)"
        $failed++
    }
}

Write-Host "Downloaded: $downloaded; unresolved/failed: $failed"
