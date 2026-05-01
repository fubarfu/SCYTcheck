# -*- mode: python ; coding: utf-8 -*-

import decorator

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


repo_root = Path(SPEC).resolve().parent
paddle_model_root = repo_root / "third_party" / "paddleocr" / "x64"
binaries = collect_dynamic_libs("paddle")
datas = collect_data_files("paddleocr", include_py_files=True)
datas += collect_data_files("paddle", include_py_files=True)
# Paddle imports setuptools.build_ext -> Cython.Compiler on some code paths,
# which requires Cython utility/include assets (e.g. Utility/CppSupport.cpp).
datas += collect_data_files("Cython", include_py_files=True)
datas.append((str(Path(decorator.__file__).resolve()), "."))
frontend_dist = repo_root / "src" / "web" / "frontend" / "dist"
if not frontend_dist.exists():
    raise RuntimeError(
        "Missing web frontend build: src/web/frontend/dist. "
        "Run: cd src/web/frontend && npm run build"
    )
datas.append((str(frontend_dist), "src/web/frontend/dist"))
hiddenimports = [
    "cv2",
    "tkinter",
    "tkinter.filedialog",
    "webbrowser",
    "decorator",
    *collect_submodules("paddleocr"),
    *collect_submodules("paddle"),
]
if not paddle_model_root.exists():
    raise RuntimeError(
        "Missing PaddleOCR model root for portable build: "
        f"{paddle_model_root}. Run scripts/download_paddleocr_models.ps1 first."
    )

for child in sorted(paddle_model_root.iterdir()):
    if child.is_dir() and (
        child.name.lower().startswith("det")
        or child.name.lower().startswith("rec")
        or child.name.lower().startswith("cls")
    ):
        for model_file in child.rglob("*"):
            if not model_file.is_file():
                continue
            relative_parent = model_file.relative_to(child).parent
            destination = Path("paddleocr") / child.name / relative_parent
            datas.append((str(model_file), str(destination)))

if not any(Path(dst).name.startswith("det") for _, dst in datas):
    raise RuntimeError("Missing det* PaddleOCR model directory in third_party/paddleocr/x64")
if not any(Path(dst).name.startswith("rec") for _, dst in datas):
    raise RuntimeError("Missing rec* PaddleOCR model directory in third_party/paddleocr/x64")
if not any(Path(dst).name.startswith("cls") for _, dst in datas):
    raise RuntimeError("Missing cls* PaddleOCR model directory in third_party/paddleocr/x64")


a = Analysis(
    [str(repo_root / "src" / "main.py")],
    pathex=[str(repo_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(repo_root / "scripts" / "release" / "runtime_hook_paddleocr.py")],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SCYTcheck",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SCYTcheck",
)
