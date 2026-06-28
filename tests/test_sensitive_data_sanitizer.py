from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from scripts.sanitize_sensitive_data_repo import sanitize_sensitive_repo


def test_sanitize_sensitive_repo_creates_requested_layout(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "data"
    for folder in ("custom_libs", "robot", "output", "success", "fail"):
        (source_root / folder).mkdir(parents=True)

    (source_root / "custom_libs" / "SensitiveLibrary.py").write_text(
        """
class SensitiveLibrary:
    def connect(self):
        password = "do-not-copy"
        return "http://internal.example.test", "10.20.30.40"
""",
        encoding="utf-8",
    )
    (source_root / "robot" / "SensitiveSuite.robot").write_text(
        """
*** Test Cases ***
SensitiveSuite
    Log    123456789012345
""",
        encoding="utf-8",
    )
    _write_minimal_xlsx(
        source_root / "output" / "SensitiveReport.xlsx",
        "http://report.example.test",
    )

    manifest = sanitize_sensitive_repo(source_root=source_root, target_root=target_root)

    assert (target_root / ".git").exists() is False
    assert (target_root / "robot-tests").is_dir()
    assert (target_root / "custom-libs").is_dir()
    assert (target_root / "report-example").is_dir()
    assert (target_root / "successful-execution").is_dir()
    assert (target_root / "failed-execution").is_dir()
    assert manifest["summary"]["files"] == 3
    assert manifest["summary"]["redactions"] >= 5

    combined_text = "\n".join(
        file.read_text(encoding="utf-8", errors="ignore")
        for file in target_root.rglob("*")
        if file.is_file() and file.suffix.lower() != ".xlsx"
    )
    assert "http://internal.example.test" not in combined_text
    assert "10.20.30.40" not in combined_text
    assert "SensitiveLibrary" not in combined_text
    assert "SensitiveSuite" not in combined_text
    assert "123456789012345" not in combined_text

    xlsx_files = list((target_root / "report-example").glob("*.xlsx"))
    assert len(xlsx_files) == 1
    with ZipFile(xlsx_files[0], "r") as workbook:
        shared_strings = workbook.read("xl/sharedStrings.xml").decode("utf-8")
    assert "http://report.example.test" not in shared_strings


def test_sanitize_sensitive_repo_requires_clean_for_existing_target(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "data"
    (source_root / "custom_libs").mkdir(parents=True)
    target_root.mkdir()

    with pytest.raises(FileExistsError, match="Use --clean"):
        sanitize_sensitive_repo(source_root=source_root, target_root=target_root)


def _write_minimal_xlsx(path: Path, shared_value: str) -> None:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as workbook:
        workbook.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="xml" ContentType="application/xml"/>
</Types>
""",
        )
        workbook.writestr(
            "xl/sharedStrings.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<si><t>{shared_value}</t></si>
</sst>
""",
        )
