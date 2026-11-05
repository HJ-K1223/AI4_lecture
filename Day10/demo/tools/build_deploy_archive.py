"""Build a small source-only upload archive; never include local secrets or runtimes."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "note-demo-deploy.zip"
DIRECTORIES = ("accounts", "board", "config", "moderation", "templates", "static", "seeds")
ROOT_FILES = ("manage.py", "requirements.txt", ".env.production.example", "README.md")
ALLOWED_SUFFIXES = {".py", ".html", ".css", ".json"}


def build():
    paths = [ROOT / name for name in ROOT_FILES]
    for directory in DIRECTORIES:
        paths.extend(
            path for path in (ROOT / directory).rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
            and path.suffix in ALLOWED_SUFFIXES
        )
    with ZipFile(DESTINATION, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(DESTINATION) as archive:
        names = archive.namelist()
        assert "manage.py" in names and "config/wsgi.py" in names
        assert not any(Path(name).name == ".env" for name in names)
        assert not any(name.startswith((".runtime/", ".venv/", "staticfiles/")) for name in names)
        assert archive.testzip() is None
    print(f"Created {DESTINATION.name}: {len(names)} files, {DESTINATION.stat().st_size:,} bytes")


if __name__ == "__main__":
    build()
