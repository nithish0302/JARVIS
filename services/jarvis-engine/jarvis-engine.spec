# PyInstaller spec for the JARVIS backend, frozen as the Tauri sidecar
# binary. --onedir (not --onefile): onefile's self-extracting startup is
# markedly slower and considerably more fragile for a dependency set this
# heavy (torch+CUDA, chromadb, sentence-transformers) - onedir avoids the
# per-launch extraction step entirely and is the combination that actually
# works for this class of app in practice.
#
# Build: uv run pyinstaller jarvis-engine.spec --noconfirm
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

HEAVY_PACKAGES = [
    "chromadb",
    "sentence_transformers",
    "transformers",
    "tokenizers",
    "kokoro",
    "faster_whisper",
    "ctranslate2",
    "onnxruntime",
    "openwakeword",
    "huggingface_hub",
    "tiktoken",
    "edge_tts",
    "duckduckgo_search",
    "misaki",
    "espeakng_loader",
    "groq",
    "pydantic",
    "pydantic_settings",
    "aiosqlite",
    "sounddevice",
    "soundfile",
    "pygame",
    "torch",
    # misaki[en] (kokoro's phonemizer) pulls in the CLDF/phonemizer data
    # ecosystem below - each ships JSON/CSV language data that collect_all
    # is needed for, not just the Python code.
    "spacy",
    "spacy_curated_transformers",
    "phonemizer_fork",
    "segments",
    "csvw",
    "language_tags",
    "clldutils",
    "langcodes",
    "language_data",
    "num2words",
    "regex",
]

datas = []
binaries = []
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "jarvis_engine.api.routes",
]

for pkg in HEAVY_PACKAGES:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as e:
        print(f"[spec] collect_all({pkg!r}) failed, skipping: {e}")

a = Analysis(
    ["pyinstaller_entry.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pyinstaller", "pytest", "pyright", "black", "ruff"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="jarvis-engine-x86_64-pc-windows-msvc",
    debug=False,
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
    name="jarvis-engine",
)
