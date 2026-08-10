param(
    [Parameter(Mandatory = $true)] [long]$WindowHandle,
    [ValidateSet('Charts', 'Slicers', 'All')] [string]$Stage = 'All'
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class HoneyWinReportMouse {
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint x, uint y, uint data, UIntPtr extraInfo);
}
'@

function Get-Root {
    return [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$WindowHandle)
}

function Invoke-Click([int]$X, [int]$Y) {
    [HoneyWinReportMouse]::SetCursorPos($X, $Y) | Out-Null
    [HoneyWinReportMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
    [HoneyWinReportMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 260
}

function Invoke-Drag([int]$StartX, [int]$StartY, [int]$EndX, [int]$EndY) {
    [HoneyWinReportMouse]::SetCursorPos($StartX, $StartY) | Out-Null
    [HoneyWinReportMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
    for ($step = 1; $step -le 24; $step++) {
        $x = [int]($StartX + (($EndX - $StartX) * $step / 24))
        $y = [int]($StartY + (($EndY - $StartY) * $step / 24))
        [HoneyWinReportMouse]::SetCursorPos($x, $y) | Out-Null
        Start-Sleep -Milliseconds 10
    }
    [HoneyWinReportMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 360
}

function Select-Page([string]$Name) {
    $page = (Get-Root).FindFirst(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty,
            $Name
        ))
    )
    if (-not $page) { throw "Page not found: $Name" }
    ($page.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
    Start-Sleep -Milliseconds 650
}

function Set-DataSearch([string]$Value) {
    $edits = (Get-Root).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Edit
        ))
    )
    foreach ($edit in $edits) {
        $bounds = $edit.Current.BoundingRectangle
        if ($bounds.X -gt 4050 -and $bounds.X -lt 4250 -and $bounds.Y -gt 250 -and $bounds.Y -lt 310) {
            ($edit.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)).SetValue($Value)
            Start-Sleep -Milliseconds 430
            return
        }
    }
    throw 'Visible Data pane search box was not found.'
}

function Select-Field([string]$AutomationName) {
    $elements = (Get-Root).FindAll(
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
            Start-Sleep -Milliseconds 450
            return
        }
    }
    throw "Visible field checkbox was not found: $AutomationName"
}

function Find-VisualGroup([string]$Title) {
    $groups = (Get-Root).FindAll(
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
    $visibleNames = @(
        foreach ($group in $groups) {
            if ($group.Current.BoundingRectangle.Width -gt 0 -and $group.Current.Name.Trim()) {
                $group.Current.Name.Trim()
            }
        }
    ) -join ' | '
    throw "Visual was not found: $Title. Visible groups: $visibleNames"
}

function Select-Visual([string]$Title) {
    $visual = Find-VisualGroup $Title
    $bounds = $visual.Current.BoundingRectangle
    Invoke-Click ([int]($bounds.X + $bounds.Width / 2)) ([int]($bounds.Y + 10))
    return $visual
}

function Add-MeasuresToVisual([string]$Title, [string[]]$Measures) {
    $null = Select-Visual $Title
    foreach ($measure in $Measures) {
        Set-DataSearch $measure
        Select-Field "Measure Field $measure"
    }
}

function Remove-Visual([string]$Title) {
    $null = Select-Visual $Title
    [System.Windows.Forms.SendKeys]::SendWait('{DELETE}')
    Start-Sleep -Milliseconds 550
}

function Set-VisualBounds([string]$Title, [int]$X, [int]$Y, [int]$Width, [int]$Height) {
    $visual = Find-VisualGroup $Title
    $bounds = $visual.Current.BoundingRectangle
    Invoke-Drag `
        ([int]($bounds.X + $bounds.Width / 2)) `
        ([int]($bounds.Y + 10)) `
        ([int]($X + $bounds.Width / 2)) `
        ($Y + 10)
    $visual = Find-VisualGroup $Title
    $bounds = $visual.Current.BoundingRectangle
    Invoke-Click ([int]($bounds.X + $bounds.Width / 2)) ([int]($bounds.Y + 10))
    Invoke-Drag ([int]($bounds.Right - 1)) ([int]($bounds.Bottom - 1)) ($X + $Width) ($Y + $Height)
    Invoke-Click 3800 800
}

function New-Chart(
    [ValidateSet('Line', 'ClusteredBar')] [string]$Type,
    [string]$Dimension,
    [string[]]$Measures,
    [string]$ExpectedTitle
) {
    $point = if ($Type -eq 'Line') { @(3895, 375) } else { @(3951, 347) }
    Invoke-Click 3500 900
    Invoke-Click $point[0] $point[1]
    Set-DataSearch $Dimension
    Select-Field " $Dimension"
    foreach ($measure in $Measures) {
        Set-DataSearch $measure
        Select-Field "Measure Field $measure"
    }
    Start-Sleep -Milliseconds 900
    $null = Find-VisualGroup $ExpectedTitle
    Set-VisualBounds -Title $ExpectedTitle -X 3210 -Y 226 -Width 616 -Height 470
}

function Add-Slicer([string]$Field, [string]$ExpectedTitle) {
    Invoke-Click 3500 900
    Invoke-Click 3951 459
    Set-DataSearch $Field
    Select-Field " $Field"
    Start-Sleep -Milliseconds 750
    $null = Find-VisualGroup $ExpectedTitle
}

if ($Stage -in @('Charts', 'All')) {
    Select-Page 'Executive Overview'
    Add-MeasuresToVisual -Title 'Approved Budget by Program' -Measures @('Actual Cost', 'EAC')

    Select-Page 'Financial & Cost'
    Add-MeasuresToVisual -Title 'Monthly Actual + Forecast Spend by YearMonth' -Measures @('Phased Budget')

    Select-Page 'Labor Utilization'
    Remove-Visual 'Project Hours by TeamName'
    New-Chart -Type Line -Dimension 'YearMonth' `
        -Measures @('Labor Utilization %', 'Weighted Utilization Target %') `
        -ExpectedTitle 'Labor Utilization % and Weighted Utilization Target % by YearMonth'

    Select-Page 'Workforce Capacity'
    Remove-Visual 'Open Demand FTE by SkillName'
    New-Chart -Type Line -Dimension 'YearMonth' `
        -Measures @('Actual FTE', 'Required FTE') `
        -ExpectedTitle 'Actual FTE and Required FTE by YearMonth'

    Select-Page 'Governance & Risk'
    Remove-Visual 'Total Projects by ProjectStatus'
    New-Chart -Type ClusteredBar -Dimension 'RiskCategory' `
        -Measures @('Open Critical Risks', 'Overdue Actions') `
        -ExpectedTitle 'Open Critical Risks and Overdue Actions by RiskCategory'
}

if ($Stage -in @('Slicers', 'All')) {
    $slicers = @(
        @('Executive Overview', 'Program', 'Program'),
        @('Financial & Cost', 'PeriodType', 'PeriodType'),
        @('Labor Utilization', 'EmploymentType', 'EmploymentType'),
        @('Workforce Capacity', 'Location', 'Location'),
        @('Governance & Risk', 'RiskSeverity', 'RiskSeverity')
    )
    foreach ($item in $slicers) {
        Select-Page $item[0]
        Add-Slicer -Field $item[1] -ExpectedTitle $item[2]
    }
}

Write-Output "Completed Power BI report optimization stage: $Stage"
