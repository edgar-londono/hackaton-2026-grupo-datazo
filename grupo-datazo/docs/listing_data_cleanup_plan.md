# Listing data cleanup plan

## Goal

Prepare all 117 supplied listing rows for analysis. Keep each source value traceable. Do not claim that an ad value is true without evidence.

## Source boundary

- Keep `data/anuncios_muestra.csv` unchanged.
- Do not scrape property portals or add listings.
- Use official public records only to check fields already present in the sample.
- Do not inspect or change geographic layers during this phase.
- Do not fill missing values with estimates or assumptions.

## Processing steps

1. Record the source file, row number, and all 14 original field values.
2. Trim surrounding whitespace and collapse repeated whitespace in the prepared copy.
3. Parse numeric fields for calculations without replacing the source text.
4. Map known condition labels with the configured aliases. Keep unknown labels unclassified.
5. Find possible repeats by listing ID or configured candidate fields. Treat these keys as alerts only.
6. Remove a row only when every source column matches after safe whitespace and numeric formatting normalization. Preserve case and accents during this exact comparison.
7. Keep partial matches as separate records. The team may include or exclude these rows from calculations.
8. Check each calculation against its own required fields. Do not exclude a full row because one unrelated field is missing.
9. Check an existing value against an official source only when the record can be identified without doubt.
10. Record the source, old value, result, rule, URL, license, and check date for each official check or correction.

## Include or exclude possible repeats

Possible repeats are separate records by default. This follows the rule that a difference does not prove that two ads describe the same listing.

Use one of these commands:

```powershell
python src/mvp.py --include-candidates
python src/mvp.py --exclude-candidates
```

The command option overrides `deduplicacion.incluir_candidatos_en_calculos` in `config/parametros.yaml`. Without a command option, the configured value applies. The report and cards record the selected choice.

## Field audit statuses

The generated `output/prepared/auditoria_campos_anuncios.csv` has one row for each source field. It records the source value, prepared value, status, rule, evidence file, source row, official source URL, and check date.

- `missing`: the source field is empty.
- `format_normalized`: safe whitespace cleanup changed the prepared value.
- `reported_by_source_unverified`: the value appears in the supplied ad sample, but no official source confirms it.
- `invalid_or_out_of_range`: the value fails a configured format, range, or category check.
- `officially_confirmed`: an official record confirms the existing value.
- `corrected_with_evidence`: an official record supports a replacement value.

The source sample has no street address or unique public listing record for every ad. Therefore, official sources may confirm that a municipality or neighborhood name exists, but they may not prove that a specific ad belongs there. Do not correct an ad from a name match alone.

Record approved checks in `data/anuncios_verificaciones.csv`. Each row must name the input row and field, the original and result values, an HTTPS source URL, a source record ID, a license note, an ISO check date, the decision rule, and a snapshot path or reason for not retaining a snapshot. The pipeline rejects incomplete evidence or a source value that does not match the input.

Official checks do not change the original CSV. The prepared copy and field audit show the supported result.

## Completion rule

Cleanup is complete when all 1,638 source field values have an audit status, all possible-repeat groups have a recorded difference list, and both candidate inclusion modes produce reproducible outputs. Completion means every value has a documented outcome. It does not mean every ad claim has independent public confirmation.
