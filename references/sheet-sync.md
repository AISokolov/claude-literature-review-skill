# Google Sheets sync (optional)

Used only when the profile has a `sheet` section with `mapping_confirmed: true`. If `mapping_confirmed` is missing or false, don't append: keep accepted papers as `sync_pending` and offer `update sheet` (see `profile-setup.md`).

- **Spreadsheet:** `sheet.spreadsheet_id`. Never write to any ID listed in `sheet.do_not_write`.
- **Tab:** `sheet.tab` (with `sheet.sheet_id`). Header row: `sheet.header_row` (default 1).
- **Columns:** `sheet.columns`, in sheet order (A, B, C, …).
- **Tools:** the Google Sheets connector (`get_values`, `get_spreadsheet`, `update_spreadsheet`). If they're deferred, load them with ToolSearch. If the connector isn't connected, keep papers `sync_pending` and tell the user to connect it (claude.ai → Settings → Connectors; check with `/mcp` in the CLI).

## Step 1: build the dedupe index (start of session and before every append)
1. `get_values` on `<tab>!A<header_row+1>:A`: take each cell's first line as a title. If a column other than A holds titles, use that column (the one whose key is `title_link` or `title`).
2. `get_spreadsheet` with that range, `includeGridData:true`, `fields:["sheets.data.rowData.values.textFormatRuns.format.link.uri","sheets.data.rowData.values.hyperlink"]`. Extract every `10.\d{4,}/\S+` DOI from link URLs. If the sheet has a DOI column, read it too.
3. Write `{"titles":[...],"dois":[...]}` to a temp file **in your scratchpad** and run `state.py sheet-index <file>`.
4. Remember the current number of data rows (`last_row`).

## Step 2: append one accepted paper
1. Run step 1 again (fresh read). If the paper's DOI or normalized title is already in the sheet, **do not append**. Run `state.py sync-ok <key>` and tell the user "already present in the sheet". This also covers an earlier append that succeeded but whose response was lost.
2. **Copy the row format:** `get_spreadsheet` on the last data row (`<tab>!A<last>:<lastcol><last>`, `includeGridData:true`, `fields:["sheets.data.rowData.values.userEnteredFormat"]`). Reuse each cell's `userEnteredFormat` for the matching new cell. If the sheet has no data rows yet, send values only.
3. Build the row from the stored record with a small Python script, not by hand:
   - **Ordinary column:** `{"userEnteredValue":{"stringValue": record.sheet[key]}, "userEnteredFormat": FMT_i}`
   - **Column with `link`:** value `"<title>\n\n<link.text>"`, plus `textFormatRuns` `[{"startIndex":0,"format":{}}, {"startIndex": <UTF-16 length of title + 2>, "format":{"link":{"uri": URL},"underline":true}}]`. URL = `pdf_url` if `target` is `pdf_then_doi` and a PDF exists, else `https://doi.org/<doi>`. **Never** use signed or expiring URLs (`X-Amz-*`, `token=`, `Expires=`).
4. Call `update_spreadsheet` with a single `appendCells` request (`sheetId`, `rows:[{values:[...]}]`, `fields:"userEnteredValue,userEnteredFormat,textFormatRuns"`). It's one atomic call, so a row is never half-written.
5. **Verify:** read rows `last_row` to `last_row+2` and confirm the new row holds the title and link, and that the previous row is unchanged. Then run `state.py sync-ok <key> --row <n>` and add the title/DOI to the sheet index.
6. **On any error or failed verification:** `state.py sync-fail <key> --error "<message>"`. The paper stays `accepted` + `sync_pending`. Tell the user and continue reviewing. `sync` retries later, always through step 2.1, so a retry can never create a duplicate.

## Never
- Use `update_values`, `batch_clear_values`, `deleteDimension`, `sortRange`, `findReplace` or any request that touches existing rows, unless the user explicitly asks for that specific change.
- Create spreadsheets or tabs, or change headers, column widths or existing formatting.
