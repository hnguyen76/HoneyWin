let
    // Replace this path or parameter with the local dataset folder.
    Source = Csv.Document(
        File.Contents(DataFolderPath & "\\FactLabor.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(
        PromotedHeaders,
        {
            {"LaborRecordID", type text},
            {"WeekStartDateKey", Int64.Type},
            {"EmployeeKey", Int64.Type},
            {"ProjectKey", Int64.Type},
            {"ScheduledHours", type number},
            {"AvailableHours", type number},
            {"ProjectHours", type number},
            {"NonProjectHours", type number},
            {"OvertimeHours", type number},
            {"PTOHours", type number},
            {"StandardLaborRate", Currency.Type},
            {"OvertimeRateMultiplier", type number},
            {"ActualLaborCost", Currency.Type},
            {"SubmissionDate", type date},
            {"SubmissionStatus", type text},
            {"TimeEntrySource", type text}
        }
    ),
    CompleteRows = Table.SelectRows(
        Typed,
        each [ProjectHours] <> null and [ActualLaborCost] <> null
    ),
    SortedForDeterministicRetention = Table.Sort(
        CompleteRows,
        {{"LaborRecordID", Order.Ascending}}
    ),
    BufferedForDeterministicRetention = Table.Buffer(SortedForDeterministicRetention),
    DeduplicatedNaturalGrain = Table.Distinct(
        BufferedForDeterministicRetention,
        {"EmployeeKey", "ProjectKey", "WeekStartDateKey"}
    )
in
    DeduplicatedNaturalGrain
