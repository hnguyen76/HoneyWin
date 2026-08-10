param(
    [Parameter(Mandatory = $true)] [long]$WindowHandle,
    [string]$OutputDirectory = 'docs/assets/dashboard'
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Drawing

$outputPath = Join-Path (Resolve-Path '.').Path $OutputDirectory
if (-not (Test-Path -LiteralPath $outputPath)) {
    New-Item -ItemType Directory -Path $outputPath | Out-Null
}

$root = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$WindowHandle)
if (-not $root) {
    throw "Power BI window not found: $WindowHandle"
}

$pages = [ordered]@{
    'Executive Overview' = 'executive-overview.png'
    'Financial & Cost' = 'financial-cost.png'
    'Labor Utilization' = 'labor-utilization.png'
    'Workforce Capacity' = 'workforce-capacity.png'
    'Governance & Risk' = 'governance-risk.png'
}

$nameProperty = [System.Windows.Automation.AutomationElement]::NameProperty
$controlTypeProperty = [System.Windows.Automation.AutomationElement]::ControlTypeProperty

foreach ($entry in $pages.GetEnumerator()) {
    $pageName = $entry.Key
    $page = $root.FindFirst(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition($nameProperty, $pageName))
    )
    if (-not $page) {
        throw "Report page not found: $pageName"
    }

    ($page.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
    Start-Sleep -Milliseconds 900

    $report = $root.FindFirst(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition($nameProperty, 'Power BI Report'))
    )
    if (-not $report) {
        throw "Report canvas not found on page: $pageName"
    }

    $bounds = $report.Current.BoundingRectangle
    if ([int]$bounds.Width -ne 1200 -or [int]$bounds.Height -ne 675) {
        throw "Unexpected canvas size on $pageName`: $([int]$bounds.Width)x$([int]$bounds.Height)"
    }

    # Baseline: no slicer checkbox is selected. In Power BI this means all values.
    $checkboxes = $root.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            $controlTypeProperty,
            [System.Windows.Automation.ControlType]::CheckBox
        ))
    )
    foreach ($checkbox in $checkboxes) {
        $checkboxBounds = $checkbox.Current.BoundingRectangle
        $insideReport =
            $checkboxBounds.X -ge $bounds.X -and
            $checkboxBounds.X -lt ($bounds.X + $bounds.Width) -and
            $checkboxBounds.Y -ge $bounds.Y -and
            $checkboxBounds.Y -lt ($bounds.Y + $bounds.Height)
        if ($insideReport) {
            $toggle = $checkbox.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
            if ($toggle.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::Off) {
                throw "Active slicer selection on $pageName`: $($checkbox.Current.Name)"
            }
        }
    }

    $bitmap = New-Object System.Drawing.Bitmap 1200, 675
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen([int]$bounds.X, [int]$bounds.Y, 0, 0, $bitmap.Size)
    $destination = Join-Path $outputPath $entry.Value
    $bitmap.Save($destination, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()

    Write-Output "$pageName -> $destination (1200x675; slicer baseline: All)"
}

# Leave the PBIX on its landing page for the next reviewer.
$executivePage = $root.FindFirst(
    [System.Windows.Automation.TreeScope]::Descendants,
    (New-Object System.Windows.Automation.PropertyCondition($nameProperty, 'Executive Overview'))
)
($executivePage.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
