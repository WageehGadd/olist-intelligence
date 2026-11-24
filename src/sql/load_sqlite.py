import csv
import sqlite3
from pathlib import Path

ENCODING = "utf-8-sig"


def sanitize_identifier(name: str) -> str:
    #Turn any text into a safe, lowercase SQL identifier."""
    cleaned = name.strip().lower()
    result = []
    for ch in cleaned:
        if ch.isalnum() or ch == "_":
            result.append(ch)
        else:
            result.append("_")
    identifier = "".join(result).strip("_")
    if not identifier:
        return "col"
    if identifier[0].isdigit():
        return "col_" + identifier
    return identifier


def read_csv_rows(csv_path: Path) -> list[list[str]] | None:
    #Read all rows of a CSV. Returns None if the file is not valid UTF-8."""
    try:
        with csv_path.open("r", encoding=ENCODING, newline="") as f:
            return list(csv.reader(f))
    except UnicodeDecodeError:
        return None


def build_column_names(header: list[str]) -> list[str]:
    #Sanitize header names and make duplicates unique (name, name_2, name_3...)."""
    columns = []
    seen_names = {}
    for raw_col in header:
        col_name = sanitize_identifier(raw_col)
        count = seen_names.get(col_name, 0) + 1
        seen_names[col_name] = count
        if count > 1:
            col_name = f"{col_name}_{count}"
        columns.append(col_name)
    return columns


def normalize_row(row: list[str], width: int) -> list[str | None]:
    #Pad short rows with None and trim long rows so every row has `width` fields."""
    return (row + [None] * width)[:width]


def load_table(
    conn: sqlite3.Connection,
    table_name: str,
    columns: list[str],
    data_rows: list[list[str]],
) -> int:
    #Recreate the table and insert all rows. Returns the number of rows loaded."""
    col_defs = ", ".join(f'"{col}" TEXT' for col in columns)
    col_list = ", ".join(f'"{col}"' for col in columns)
    placeholders = ", ".join("?" for _ in columns)

    rows_to_insert = [normalize_row(row, len(columns)) for row in data_rows]

    # `with conn` commits on success and rolls back if anything fails
    with conn:
        # Reset table on re-run so duplicate rows are not appended
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        conn.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
        conn.executemany(
            f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})',
            rows_to_insert,
        )

    return len(rows_to_insert)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    local_dir = project_root / "data" / "local"
    db_path = local_dir / "Customer_database.sqlite"

    local_dir.mkdir(parents=True, exist_ok=True)

    # Start from a fresh database so tables left over from old runs don't stay behind
    db_path.unlink(missing_ok=True)

    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {raw_dir}")
        return

    conn = sqlite3.connect(db_path)
    try:
        for csv_path in csv_files:
            rows = read_csv_rows(csv_path)

            if rows is None:
                print(f"Skipping {csv_path.name}: unable to decode file")
                continue
            if not rows:
                print(f"Skipping empty file: {csv_path.name}")
                continue

            table_name = sanitize_identifier(csv_path.stem)
            columns = build_column_names(rows[0])
            row_count = load_table(conn, table_name, columns, rows[1:])

            print(f"Loaded {row_count} rows from {csv_path.name} into table '{table_name}'")
    finally:
        conn.close()


if __name__ == "__main__":
    main()