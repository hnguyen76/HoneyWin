param([Parameter(Mandatory = $true)] [long]$WindowHandle)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class HoneyWinFormatMouse {
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint x, uint y, uint data, UIntPtr extraInfo);
}
'@

function Get-Root {
    return [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$WindowHandle)
}

function Click-Point([int]$X, [int]$Y) {
    [HoneyWinFormatMouse]::SetCursorPos($X, $Y) | Out-Null
    [HoneyWinFormatMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
    [HoneyWinFormatMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 430
}

function Click-Element($Element) {
    $bounds = $Element.Current.BoundingRectangle
    Click-Point ([int]($bounds.X + $bounds.Width / 2)) ([int]($bounds.Y + $bounds.Height / 2))
}

function Find-Visible([string]$Name, $ControlType = $null) {
    $elements = (Get-Root).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty,
            $Name
        ))
    )
    foreach ($element in $elements) {
        $bounds = $element.Current.BoundingRectangle
        if ($bounds.Width -gt 0 -and ($null -eq $ControlType -or $element.Current.ControlType -eq $ControlType)) {
            return $element
        }
    }
    throw "Visible UI element not found: $Name"
}

function Select-Page([string]$Name) {
    $page = Find-Visible $Name
    ($page.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
    Start-Sleep -Milliseconds 500
}

function Open-FormatPane([string]$ChartTitlePattern) {
    $groups = (Get-Root).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Group
        ))
    )
    $chart = $null
    foreach ($group in $groups) {
        if ($group.Current.BoundingRectangle.Width -gt 0 -and $group.Current.Name.Trim() -like $ChartTitlePattern) {
            $chart = $group
            break
        }
    }
    if (-not $chart) { throw "Visible chart not found: $ChartTitlePattern" }
    $bounds = $chart.Current.BoundingRectangle
    Click-Point ([int]($bounds.X + $bounds.Width / 2)) ([int]($bounds.Y + 10))
    $formatTab = Find-Visible 'Format visual' ([System.Windows.Automation.ControlType]::TabItem)
    Click-Element $formatTab
}

function Enable-DataLabels {
    $labels = (Get-Root).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty,
            'Data labels'
        ))
    )
    $row = $null
    foreach ($element in $labels) {
        $bounds = $element.Current.BoundingRectangle
        if ($bounds.X -gt 3800 -and $bounds.Width -gt 100 -and $bounds.Height -gt 15) {
            $row = $element
            break
        }
    }
    if (-not $row) { throw 'Data labels format row was not found.' }
    $rowBounds = $row.Current.BoundingRectangle
    $offElements = (Get-Root).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty,
            'Off'
        ))
    )
    $isOff = $false
    foreach ($element in $offElements) {
        $bounds = $element.Current.BoundingRectangle
        if ([math]::Abs(($bounds.Y + $bounds.Height / 2) - ($rowBounds.Y + $rowBounds.Height / 2)) -lt 15) {
            $isOff = $true
            break
        }
    }
    if ($isOff) {
        Click-Point 4031 ([int]($rowBounds.Y + $rowBounds.Height / 2))
    }
}

function Set-BarSeriesColor([string]$Series, [string]$PaletteName) {
    $bars = Find-Visible 'Bars' ([System.Windows.Automation.ControlType]::Button)
    $seriesButton = $null
    $buttons = (Get-Root).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Button
        ))
    )
    foreach ($button in $buttons) {
        if ($button.Current.Name -like 'Series *' -and $button.Current.BoundingRectangle.Width -gt 100) {
            $seriesButton = $button
            break
        }
    }
    if (-not $seriesButton) { Click-Element $bars }
    if (-not $seriesButton) {
        $buttons = (Get-Root).FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            (New-Object System.Windows.Automation.PropertyCondition(
                [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                [System.Windows.Automation.ControlType]::Button
            ))
        )
        foreach ($button in $buttons) {
            if ($button.Current.Name -like 'Series *' -and $button.Current.BoundingRectangle.Width -gt 100) {
                $seriesButton = $button
                break
            }
        }
    }
    if (-not $seriesButton) { throw 'Series selector was not found.' }
    Click-Element $seriesButton
    $seriesItem = Find-Visible $Series ([System.Windows.Automation.ControlType]::ListItem)
    Click-Element $seriesItem
    $colorMenus = (Get-Root).FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Menu
        ))
    )
    $colorMenu = $null
    foreach ($menu in $colorMenus) {
        if ($menu.Current.Name -like 'Color #*' -and $menu.Current.BoundingRectangle.Width -gt 0) {
            $colorMenu = $menu
            break
        }
    }
    if (-not $colorMenu) { throw "Color menu not found for series: $Series" }
    Click-Element $colorMenu
    $paletteItem = Find-Visible $PaletteName ([System.Windows.Automation.ControlType]::ListItem)
    Click-Element $paletteItem
}

Select-Page 'Executive Overview'
Open-FormatPane '*Approved Budget*Program*'
Enable-DataLabels

Select-Page 'Governance & Risk'
Open-FormatPane '*Open Critical Risks*RiskCategory*'
Enable-DataLabels
Set-BarSeriesColor 'Open Critical Risks' '#D13438, Theme color 5, 0% darker'
Set-BarSeriesColor 'Overdue Actions' '#FFB900, Theme color 4, 0% darker'

Write-Output 'Applied data labels and Fluent governance status colors.'
