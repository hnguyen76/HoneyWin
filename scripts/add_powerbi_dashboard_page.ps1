param(
    [Parameter(Mandatory = $true)] [long]$WindowHandle,
    [Parameter(Mandatory = $true)] [string]$PageName,
    [Parameter(Mandatory = $true)] [string[]]$Cards,
    [Parameter(Mandatory = $true)]
    [ValidateSet('Line', 'ClusteredBar', 'ClusteredColumn')]
    [string]$ChartType,
    [Parameter(Mandatory = $true)] [string]$Dimension,
    [Parameter(Mandatory = $true)] [string]$ChartMeasure,
    [Parameter(Mandatory = $true)] [string]$ChartTitle
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class PowerBIDashboardMouse {
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint x, uint y, uint data, UIntPtr extraInfo);
}
'@

function Get-PowerBIRoot {
    return [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$WindowHandle)
}

function Invoke-Click([int]$X, [int]$Y) {
    [PowerBIDashboardMouse]::SetCursorPos($X, $Y) | Out-Null
    [PowerBIDashboardMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
    [PowerBIDashboardMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 220
}

function Invoke-Drag([int]$StartX, [int]$StartY, [int]$EndX, [int]$EndY) {
    [PowerBIDashboardMouse]::SetCursorPos($StartX, $StartY) | Out-Null
    [PowerBIDashboardMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
    for ($step = 1; $step -le 20; $step++) {
        $x = [int]($StartX + (($EndX - $StartX) * $step / 20))
        $y = [int]($StartY + (($EndY - $StartY) * $step / 20))
        [PowerBIDashboardMouse]::SetCursorPos($x, $y) | Out-Null
        Start-Sleep -Milliseconds 12
    }
    [PowerBIDashboardMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 280
}

function Set-DataSearch([string]$Value) {
    $edits = (Get-PowerBIRoot).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Edit
        ))
    )
    foreach ($edit in $edits) {
        $bounds = $edit.Current.BoundingRectangle
        if ($bounds.X -gt 4050 -and $bounds.X -lt 4250 -and $bounds.Y -gt 250 -and $bounds.Y -lt 300) {
            ($edit.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)).SetValue($Value)
            Start-Sleep -Milliseconds 450
            return
        }
    }
    throw 'Visible Data pane search box was not found.'
}

function Select-Field([string]$AutomationName) {
    $elements = (Get-PowerBIRoot).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty,
            $AutomationName
        ))
    )
    foreach ($element in $elements) {
        if (
            $element.Current.ControlType -eq [System.Windows.Automation.ControlType]::CheckBox -and
            $element.Current.BoundingRectangle.Width -gt 0
        ) {
            ($element.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)).Toggle()
            return
        }
    }
    throw "Visible field checkbox was not found: $AutomationName"
}

function Select-Page([string]$Name) {
    $page = (Get-PowerBIRoot).FindFirst(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty,
            $Name
        ))
    )
    if (-not $page) {
        throw "Page not found: $Name"
    }
    ($page.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
    Start-Sleep -Milliseconds 550
}

function Find-ChartGroup([string]$Title) {
    $groups = (Get-PowerBIRoot).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Group
        ))
    )
    foreach ($group in $groups) {
        if ($group.Current.BoundingRectangle.Width -gt 0 -and $group.Current.Name.Trim() -eq $Title) {
            return $group
        }
    }
    throw "Chart visual was not found: $Title"
}

Select-Page $PageName

foreach ($measureName in $Cards) {
    Invoke-Click 3500 900
    Invoke-Click 3895 459  # Card visual
    Set-DataSearch $measureName
    Select-Field "Measure Field $measureName"
    Start-Sleep -Milliseconds 450
}

# Arrange the automatic three-left/one-right placement into a 2x2 KPI grid.
Invoke-Drag 3052 255 3052 525
Invoke-Drag 2780 525 3052 255
Invoke-Drag 2780 785 2780 525

$chartPoint = switch ($ChartType) {
    'Line' { @(3895, 375) }
    'ClusteredBar' { @(3951, 347) }
    'ClusteredColumn' { @(3979, 347) }
}

Invoke-Click 3500 900
Invoke-Click $chartPoint[0] $chartPoint[1]
Set-DataSearch $Dimension
Select-Field " $Dimension"
Set-DataSearch $ChartMeasure
Select-Field "Measure Field $ChartMeasure"
Start-Sleep -Seconds 1

# Move the default chart to the right, then expand its top-left handle while
# keeping its bottom-right aligned with the KPI grid.
$chart = Find-ChartGroup $ChartTitle
$bounds = $chart.Current.BoundingRectangle
$smallX = 3563
$smallY = 618
Invoke-Drag `
    ([int]($bounds.X + ($bounds.Width / 2))) `
    ([int]($bounds.Y + 10)) `
    ([int]($smallX + ($bounds.Width / 2))) `
    ($smallY + 10)

$chart = Find-ChartGroup $ChartTitle
$bounds = $chart.Current.BoundingRectangle
Invoke-Click ([int]($bounds.X + ($bounds.Width / 2))) ([int]($bounds.Y + 10))
Invoke-Drag ([int]$bounds.X) ([int]$bounds.Y) 3210 226
Invoke-Click 3800 800

Write-Output "Built page '$PageName' with $($Cards.Count) cards and one $ChartType chart."
