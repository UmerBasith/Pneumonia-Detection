# Opens the generated report in Microsoft Word, updates all fields (table of contents, lists of figures and
# tables, page numbers) twice so page numbers settle, saves the .docx and exports the PDF.
param(
    [string]$Docx = "$PSScriptRoot\PneumoScan_AI_Report.docx",
    [string]$Pdf = "$PSScriptRoot\PneumoScan_AI_Report.pdf"
)
$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
# If Word handed us a window the user already has open, leave it visible and never quit it.
$shared = $word.Documents.Count -gt 0
if (-not $shared) { $word.Visible = $false }
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open((Resolve-Path $Docx).Path, $false, $false, $false)
    for ($pass = 0; $pass -lt 3; $pass++) {
        $doc.Fields.Update() | Out-Null
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
        $doc.Repaginate()
    }
    $pages = $doc.ComputeStatistics(2)
    $doc.Save()
    # 17 = wdExportFormatPDF, OpenAfterExport false, 0 = optimise for print, 0 = whole document,
    # 0,0 from/to, 0 = content, IncludeDocProps true, KeepIRM true, 1 = create bookmarks from headings
    $doc.ExportAsFixedFormat($Pdf, 17, $false, 0, 0, 0, 0, 0, $true, $true, 1)
    $doc.Close($false)
    Write-Output "pages=$pages"
}
finally {
    if (-not $shared -and $word.Documents.Count -eq 0) { $word.Quit() }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
