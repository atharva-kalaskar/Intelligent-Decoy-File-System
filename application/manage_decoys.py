"""
Decoy & Dummy File Manager
Handles creation, validation, path-traversal safety, and deployment of harmless
canary decoy files and baseline benign documents within the designated monitored directory.
"""

import os
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "settings.json"


def load_settings():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "paths": {
            "monitored_directory": "runtime/monitored",
            "manifest_file": "decoys/manifest.json"
        }
    }


def save_settings(data: dict) -> bool:
    """Safely writes settings dictionary to config/settings.json."""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save settings: {e}")
        return False


def is_safe_path(base_directory: Path, path_to_check: Path) -> bool:
    """
    Validates that path_to_check resolves strictly within base_directory
    to prevent path traversal vulnerabilities.
    """
    try:
        resolved_base = base_directory.resolve()
        resolved_target = path_to_check.resolve()
        return resolved_base in resolved_target.parents or resolved_base == resolved_target
    except Exception:
        return False


def validate_manifest(manifest_path: Path) -> dict:
    """
    Loads and validates decoy manifest structure, checking for unique IDs and safe paths.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "decoys" not in data or not isinstance(data["decoys"], list):
        raise ValueError("Invalid manifest: missing 'decoys' list")

    seen_ids = set()
    seen_paths = set()

    for item in data["decoys"]:
        file_id = item.get("file_id")
        rel_path = item.get("relative_path")

        if not file_id or not rel_path:
            raise ValueError(f"Decoy item missing file_id or relative_path: {item}")

        if file_id in seen_ids:
            raise ValueError(f"Duplicate file_id in manifest: {file_id}")
        seen_ids.add(file_id)

        # Check path traversal
        norm_rel = os.path.normpath(rel_path)
        if norm_rel.startswith("..") or os.path.isabs(norm_rel):
            raise ValueError(f"Path traversal detected in relative_path: {rel_path}")

        if norm_rel in seen_paths:
            raise ValueError(f"Duplicate relative_path in manifest: {rel_path}")
        seen_paths.add(norm_rel)

    return data


def setup_monitored_environment(base_dir: Path = BASE_DIR):
    """
    Deploys harmless dummy documents and decoy files into runtime/monitored.
    """
    settings = load_settings()
    monitored_dir = base_dir / settings["paths"]["monitored_directory"]
    manifest_file = base_dir / settings["paths"]["manifest_file"]

    manifest = validate_manifest(manifest_file)

    monitored_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = monitored_dir / "documents"
    decoys_dir = monitored_dir / "decoys"
    docs_dir.mkdir(parents=True, exist_ok=True)
    decoys_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create standard benign dummy documents
    dummy_docs = {
        "assignment.txt": (
            "Network Security Course - Assignment 3\n"
            "Topic: Intrusion Detection Systems and Deception Technology\n"
            "Student Notes: Ensure all honeypot decoys are monitored.\n"
        ),
        "project_notes.txt": (
            "Project Architecture Notes:\n"
            "- C Monitor captures events with ReadDirectoryChangesW.\n"
            "- Python extracts 11 behavioral features.\n"
            "- Random Forest performs inference.\n"
        ),
        "research_paper.txt": (
            "Abstract:\n"
            "Decoy systems provide high-fidelity tripwires in network defense.\n"
            "When paired with machine learning, automated triage minimizes false alarms.\n"
        ),
        "meeting_minutes.txt": (
            "Weekly Team Standup:\n"
            "- Completed Phase 1 environment verification.\n"
            "- Commencing C watcher implementation.\n"
        )
    }

    for name, content in dummy_docs.items():
        doc_path = docs_dir / name
        if is_safe_path(monitored_dir, doc_path):
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(content)

    # 2. Deploy decoy files according to manifest
    for decoy in manifest["decoys"]:
        target_path = monitored_dir / decoy["relative_path"]
        if not is_safe_path(monitored_dir, target_path):
            raise SecurityError(f"Target path escapes monitored directory: {target_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            f"=== SECURITY DECOY / CANARY FILE ===\n"
            f"DECOY_ID: {decoy['file_id']}\n"
            f"CATEGORY: {decoy.get('category', 'unknown')}\n"
            f"CANARY_TOKEN: {decoy.get('canary_token', 'NONE')}\n"
            f"WARNING: This is a harmless educational honeypot file.\n"
            f"Unauthorized modification or deletion triggers defensive telemetry.\n"
            f"====================================\n"
            f"Synthetic payload content simulating {decoy.get('description', 'dummy data')}.\n"
        )
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[OK] Monitored environment initialized at: {monitored_dir}")
    print(f"[OK] Created {len(dummy_docs)} benign documents and {len(manifest['decoys'])} decoy canary files.")


def clean_monitored_environment(base_dir: Path = BASE_DIR):
    """
    Cleans generated files within runtime/monitored safely.
    """
    settings = load_settings()
    monitored_dir = base_dir / settings["paths"]["monitored_directory"]
    if not monitored_dir.exists():
        return

    import shutil
    for item in monitored_dir.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    print(f"[OK] Cleaned monitored directory: {monitored_dir}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clean_monitored_environment()
    elif len(sys.argv) > 1 and sys.argv[1] == "--verify":
        validate_manifest(BASE_DIR / "decoys" / "manifest.json")
        print("[OK] Manifest verification passed.")
    else:
        setup_monitored_environment()
