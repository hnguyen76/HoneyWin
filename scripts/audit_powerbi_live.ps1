param(
    [Parameter(Mandatory = $true)] [int]$Port,
    [switch]$Refresh,
    [string]$OutputJson
)

$ErrorActionPreference = 'Stop'
if (-not $OutputJson) {
    $OutputJson = Join-Path $PSScriptRoot '..\quality\powerbi_live_audit.json'
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

function Invoke-DaxScalar {
    param(
        [Microsoft.AnalysisServices.AdomdClient.AdomdConnection]$Connection,
        [string]$Query
    )
    $command = $Connection.CreateCommand()
    $command.CommandText = $Query
    $reader = $null
    try {
        $reader = $command.ExecuteReader()
        if (-not $reader.Read()) { return $null }
        if ($reader.IsDBNull(0)) { return $null }
        return $reader.GetValue(0)
    }
    finally {
        if ($reader) { $reader.Dispose() }
        $command.Dispose()
    }
}

$amoPath = Get-AmoLibraryPath
Add-Type -Path (Join-Path $amoPath 'Microsoft.AnalysisServices.Core.dll')
Add-Type -Path (Join-Path $amoPath 'Microsoft.AnalysisServices.Tabular.dll')
$powerBiExecutable = Get-Process -Name PBIDesktop -ErrorAction Stop |
    Select-Object -First 1 -ExpandProperty Path
$adomdDll = Join-Path (Split-Path -Parent $powerBiExecutable) 'Microsoft.PowerBI.AdomdClient.dll'
if (-not $adomdDll) { throw 'Power BI ADOMD client assembly was not found.' }
Add-Type -Path $adomdDll

$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$connection = $null
try {
    $server.Connect("localhost:$Port")
    if ($server.Databases.Count -ne 1) {
        throw "Expected one open Power BI database; found $($server.Databases.Count)."
    }
    $database = $server.Databases[0]
    $model = $database.Model
    if ($Refresh) {
        foreach ($table in $model.Tables) {
            $table.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
        }
        $model.SaveChanges()
    }

    $connection = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$Port")
    $connection.Open()

    $tableResults = @()
    foreach ($table in $model.Tables | Sort-Object Name) {
        $escapedTable = $table.Name.Replace("'", "''")
        $rowCount = Invoke-DaxScalar -Connection $connection -Query "EVALUATE ROW(`"Rows`", COUNTROWS('$escapedTable'))"
        $tableResults += [pscustomobject]@{
            Name = $table.Name
            Rows = [long]$rowCount
            Columns = $table.Columns.Count
            Measures = $table.Measures.Count
            Partitions = $table.Partitions.Count
        }
    }

    $relationshipResults = @(
        foreach ($relationship in $model.Relationships | Sort-Object Name) {
            [pscustomobject]@{
                Name = $relationship.Name
                From = "$($relationship.FromColumn.Table.Name).$($relationship.FromColumn.Name)"
                To = "$($relationship.ToColumn.Table.Name).$($relationship.ToColumn.Name)"
                FromCardinality = [string]$relationship.FromCardinality
                ToCardinality = [string]$relationship.ToCardinality
                CrossFilter = [string]$relationship.CrossFilteringBehavior
                IsActive = [bool]$relationship.IsActive
            }
        }
    )

    $measureResults = @()
    foreach ($table in $model.Tables) {
        foreach ($measure in $table.Measures | Sort-Object Name) {
            $test = [ordered]@{
                Name = $measure.Name
                Table = $table.Name
                DisplayFolder = $measure.DisplayFolder
                FormatString = $measure.FormatString
                Status = 'PASS'
                Value = $null
                Error = $null
            }
            try {
                $escapedMeasure = $measure.Name.Replace(']', ']]')
                $value = Invoke-DaxScalar -Connection $connection -Query "EVALUATE ROW(`"Value`", [$escapedMeasure])"
                $test.Value = if ($null -eq $value) { $null } else { [string]$value }
            }
            catch {
                $test.Status = 'FAIL'
                $test.Error = $_.Exception.Message
            }
            $measureResults += [pscustomobject]$test
        }
    }

    $audit = [ordered]@{
        Database = $database.Name
        RefreshRequested = [bool]$Refresh
        TableCount = $model.Tables.Count
        MeasureCount = @($measureResults).Count
        MeasurePassCount = @($measureResults | Where-Object Status -eq 'PASS').Count
        MeasureFailCount = @($measureResults | Where-Object Status -eq 'FAIL').Count
        RelationshipCount = $model.Relationships.Count
        ActiveRelationshipCount = @($model.Relationships | Where-Object IsActive).Count
        InactiveRelationshipCount = @($model.Relationships | Where-Object { -not $_.IsActive }).Count
        Tables = $tableResults
        Relationships = $relationshipResults
        Measures = $measureResults
    }
    $outputDirectory = Split-Path -Parent $OutputJson
    if (-not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory | Out-Null
    }
    $audit | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputJson -Encoding UTF8
    Write-Output "Tables=$($audit.TableCount); Measures=$($audit.MeasurePassCount)/$($audit.MeasureCount); Relationships=$($audit.ActiveRelationshipCount) active + $($audit.InactiveRelationshipCount) inactive."
    Write-Output "Wrote $OutputJson"
    if ($audit.MeasureFailCount -gt 0) { exit 1 }
}
finally {
    if ($connection -and $connection.State -eq 'Open') { $connection.Close() }
    if ($connection) { $connection.Dispose() }
    if ($server.Connected) { $server.Disconnect() }
}
