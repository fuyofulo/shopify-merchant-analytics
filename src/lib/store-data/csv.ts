/**
 * Minimal RFC 4180 CSV parser: handles quoted fields, escaped quotes (`""`),
 * commas and newlines inside quotes, and both LF and CRLF line endings.
 * Returns every non-empty record as an array of raw string fields.
 */
export function parseCsv(text: string): string[][] {
  const records: string[][] = [];
  let record: string[] = [];
  let field = "";
  let inQuotes = false;

  const endField = () => {
    record.push(field);
    field = "";
  };
  const endRecord = () => {
    endField();
    // Skip blank lines (a record with a single empty field).
    if (record.length > 1 || record[0] !== "") records.push(record);
    record = [];
  };

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += char;
      }
      continue;
    }

    if (char === '"') inQuotes = true;
    else if (char === ",") endField();
    else if (char === "\n") endRecord();
    else if (char === "\r") {
      if (text[i + 1] === "\n") i++;
      endRecord();
    } else field += char;
  }

  if (inQuotes) throw new Error("Malformed CSV: unterminated quoted field.");
  if (field !== "" || record.length > 0) endRecord();

  return records;
}
