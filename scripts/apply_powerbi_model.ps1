param(
    [Parameter(Mandatory = $true)]
    [int]$Port,
    [string]$MeasureJson,
    [string]$ColumnTypesJson
)

$ErrorActionPreference = 'Stop'
if (-not $MeasureJson) {
    $MeasureJson = Join-Path $PSScriptRoot '..\powerbi\measures.generated.json'
}
if (-not $ColumnTypesJson) {
    $ColumnTypesJson = Join-Path $PSScriptRoot '..\powerbi\column_types.generated.json'
}

function Get-AmoLibraryPath {
    $version = '19.84.1'
    $packageName = "microsoft.analysisservices.retail.amd64.$version.nupkg"
    $packagePath = Join-Path $env:TEMP $packageName
    $destination = Join-Path $env:TEMP "amo-$version"
    $tabularDll = Join-Path $destination 'lib\net45\Microsoft.AnalysisServices.Tabular.dll'

    if (-not (Test-Path -LiteralPath $tabularDll)) {
        if (-not (Test-Path -LiteralPath $packagePath)) {
            $uri = "https://api.nuget.org/v3-flatcontainer/microsoft.analysisservices.retail.amd64/$version/$packageName"
            Invoke-WebRequest -Uri $uri -OutFile $packagePath
        }
        if (-not (Test-Path -LiteralPath $destination)) {
            New-Item -ItemType Directory -Path $destination | Out-Null
        }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($packagePath, $destination)
    }
    return (Join-Path $destination 'lib\net45')
}

function Add-RelationshipIfMissing {
    param(
        [Microsoft.AnalysisServices.Tabular.Model]$Model,
        [string]$Name,
        [string]$FromTable,
        [string]$FromColumn,
        [string]$ToTable,
        [string]$ToColumn,
        [bool]$IsActive = $true
    )

    $same = $Model.Relationships | Where-Object {
        $_.FromColumn.Table.Name -eq $FromTable -and
        $_.FromColumn.Name -eq $FromColumn -and
        $_.ToColumn.Table.Name -eq $ToTable -and
        $_.ToColumn.Name -eq $ToColumn
    }
    if ($same) {
        $same.IsActive = $IsActive
        return
    }

    $relationship = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
    $relationship.Name = $Name
    $relationship.FromColumn = $Model.Tables[$FromTable].Columns[$FromColumn]
    $relationship.FromCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many
    $relationship.ToColumn = $Model.Tables[$ToTable].Columns[$ToColumn]
    $relationship.ToCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One
    $relationship.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
    $relationship.IsActive = $IsActive
    $Model.Relationships.Add($relationship)
}

function Get-PowerQueryType([string]$TabularType) {
    switch ($TabularType) {
        'Int64' { return 'Int64.Type' }
        'Double' { return 'type number' }
        'Boolean' { return 'type logical' }
        'DateTime' { return 'type date' }
        default { return 'type text' }
    }
}

$amoPath = Get-AmoLibraryPath
Add-Type -Path (Join-Path $amoPath 'Microsoft.AnalysisServices.Core.dll')
Add-Type -Path (Join-Path $amoPath 'Microsoft.AnalysisServices.Tabular.dll')

$server = New-Object Microsoft.AnalysisServices.Tabular.Server
try {
    $server.Connect("localhost:$Port")
    if ($server.Databases.Count -ne 1) {
        throw "Expected one open Power BI database; found $($server.Databases.Count)."
    }

    $model = $server.Databases[0].Model
    $measureTable = $model.Tables['DimProject']
    $measureDefinitions = Get-Content -LiteralPath $MeasureJson -Raw -Encoding UTF8 | ConvertFrom-Json
    $columnTypeDefinitions = Get-Content -LiteralPath $ColumnTypesJson -Raw -Encoding UTF8 | ConvertFrom-Json

    $timeIntelligenceAnnotation = $model.Annotations | Where-Object Name -eq '__PBI_TimeIntelligenceEnabled'
    if ($timeIntelligenceAnnotation) {
        $timeIntelligenceAnnotation.Value = '0'
    }
    else {
        $timeIntelligenceAnnotation = New-Object Microsoft.AnalysisServices.Tabular.Annotation
        $timeIntelligenceAnnotation.Name = '__PBI_TimeIntelligenceEnabled'
        $timeIntelligenceAnnotation.Value = '0'
        $model.Annotations.Add($timeIntelligenceAnnotation)
    }

    # The explicit DimDate table is canonical. Remove hidden auto-date tables
    # to avoid redundant storage and ambiguous date drill paths.
    foreach ($table in $model.Tables) {
        foreach ($column in $table.Columns) {
            foreach ($variation in @($column.Variations)) {
                $column.Variations.Remove($variation)
            }
        }
    }
    $autoDateRelationships = @($model.Relationships | Where-Object {
        $_.FromColumn.Table.Name -like 'LocalDateTable_*' -or
        $_.ToColumn.Table.Name -like 'LocalDateTable_*' -or
        $_.FromColumn.Table.Name -like 'DateTableTemplate_*' -or
        $_.ToColumn.Table.Name -like 'DateTableTemplate_*'
    })
    foreach ($relationship in $autoDateRelationships) {
        $model.Relationships.Remove($relationship)
    }
    $autoDateTables = @($model.Tables | Where-Object {
        $_.Name -like 'LocalDateTable_*' -or $_.Name -like 'DateTableTemplate_*'
    })
    foreach ($table in $autoDateTables) {
        $model.Tables.Remove($table)
    }

    foreach ($tableProperty in $columnTypeDefinitions.PSObject.Properties) {
        $table = $model.Tables[$tableProperty.Name]
        foreach ($columnProperty in $tableProperty.Value.PSObject.Properties) {
            $column = $table.Columns[$columnProperty.Name]
            $null = $column.DataType = [System.Enum]::Parse(
                [Microsoft.AnalysisServices.Tabular.DataType],
                [string]$columnProperty.Value
            )
        }

        # Python.Execute returns an untyped table unless the M partition applies
        # an explicit transform. Persist the typing in Power Query so a UI
        # refresh cannot silently revert fact columns back to text.
        if ($table.Partitions.Count -eq 1 -and $table.Partitions[0].Source -is [Microsoft.AnalysisServices.Tabular.MPartitionSource]) {
            $source = $table.Partitions[0].Source
            $expression = [string]$source.Expression
            $inMatch = [regex]::Match(
                $expression,
                '\s+in\s+',
                [System.Text.RegularExpressions.RegexOptions]::RightToLeft
            )
            if (-not $inMatch.Success) {
                throw "Could not locate the final M 'in' clause for $($table.Name)."
            }
            $baseExpression = $expression.Substring(0, $inMatch.Index).TrimEnd()
            foreach ($marker in @('#"HoneyWin Typed"', '#"Changed Type"')) {
                $markerIndex = $baseExpression.LastIndexOf($marker)
                if ($markerIndex -ge 0) {
                    $commaIndex = $baseExpression.LastIndexOf(',', $markerIndex)
                    if ($commaIndex -ge 0) {
                        $baseExpression = $baseExpression.Substring(0, $commaIndex).TrimEnd()
                    }
                }
            }
            $pairs = @()
            foreach ($columnProperty in $tableProperty.Value.PSObject.Properties) {
                $escapedColumn = $columnProperty.Name.Replace('"', '""')
                $mType = Get-PowerQueryType ([string]$columnProperty.Value)
                $pairs += '{"' + $escapedColumn + '", ' + $mType + '}'
            }
            $stepName = $table.Name + '1'
            $pairText = $pairs -join ', '
            $source.Expression = "$baseExpression,`r`n    #""HoneyWin Typed"" = Table.TransformColumnTypes($stepName,{$pairText})`r`nin`r`n    #""HoneyWin Typed"""
        }
    }

    $model.Tables['DimDate'].Columns['YearMonth'].SortByColumn =
        $model.Tables['DimDate'].Columns['MonthStartDate']
    $model.Tables['DimDate'].Columns['MonthName'].SortByColumn =
        $model.Tables['DimDate'].Columns['MonthNumber']
    foreach ($table in $model.Tables) {
        foreach ($column in $table.Columns) {
            if ($column.Name -like 'RowNumber-*') {
                $column.IsHidden = $true
            }
        }
    }

    foreach ($definition in $measureDefinitions) {
        $existing = $measureTable.Measures.Find($definition.name)
        if ($existing) {
            $existing.Expression = $definition.expression
            $existing.DisplayFolder = $definition.displayFolder
            $existing.FormatString = if ($definition.formatString) { $definition.formatString } else { '' }
            continue
        }
        $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
        $measure.Name = $definition.name
        $measure.Expression = $definition.expression
        $measure.DisplayFolder = $definition.displayFolder
        if ($definition.formatString) {
            $measure.FormatString = $definition.formatString
        }
        $measureTable.Measures.Add($measure)
    }

    $relationships = @(
        @('R_DimProject_Team', 'DimProject', 'PrimaryTeamKey', 'DimTeam', 'TeamKey', $false),
        @('R_DimEmployee_PrimarySkill', 'DimEmployee', 'PrimarySkillKey', 'DimSkill', 'SkillKey', $false),
        @('R_FactFinancial_Date', 'FactFinancial', 'MonthStartDateKey', 'DimDate', 'DateKey', $true),
        @('R_FactFinancial_Project', 'FactFinancial', 'ProjectKey', 'DimProject', 'ProjectKey', $true),
        @('R_FactLabor_Date', 'FactLabor', 'WeekStartDateKey', 'DimDate', 'DateKey', $true),
        @('R_FactLabor_Project', 'FactLabor', 'ProjectKey', 'DimProject', 'ProjectKey', $true),
        @('R_FactMilestone_Project', 'FactMilestone', 'ProjectKey', 'DimProject', 'ProjectKey', $true),
        @('R_FactMilestone_PlannedDate', 'FactMilestone', 'PlannedDateKey', 'DimDate', 'DateKey', $true),
        @('R_FactMilestone_ForecastDate', 'FactMilestone', 'ForecastDateKey', 'DimDate', 'DateKey', $false),
        @('R_FactRiskIssue_Project', 'FactRiskIssue', 'ProjectKey', 'DimProject', 'ProjectKey', $true),
        @('R_FactRiskIssue_IdentifiedDate', 'FactRiskIssue', 'IdentifiedDateKey', 'DimDate', 'DateKey', $true),
        @('R_FactRiskIssue_DueDate', 'FactRiskIssue', 'DueDateKey', 'DimDate', 'DateKey', $false),
        @('R_FactWorkforcePlan_Date', 'FactWorkforcePlan', 'MonthStartDateKey', 'DimDate', 'DateKey', $true),
        @('R_FactWorkforcePlan_Team', 'FactWorkforcePlan', 'TeamKey', 'DimTeam', 'TeamKey', $true),
        @('R_FactWorkforcePlan_Skill', 'FactWorkforcePlan', 'SkillKey', 'DimSkill', 'SkillKey', $true)
    )
    foreach ($r in $relationships) {
        Add-RelationshipIfMissing -Model $model -Name $r[0] -FromTable $r[1] -FromColumn $r[2] -ToTable $r[3] -ToColumn $r[4] -IsActive $r[5]
    }

    $model.SaveChanges()
    Write-Output "Applied typed columns, $($measureDefinitions.Count) measures, and ensured $($relationships.Count) relationships."
}
finally {
    if ($server.Connected) {
        $server.Disconnect()
    }
}
