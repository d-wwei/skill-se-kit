# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building standalone skill-se-kit binary.

Usage:
    pip install pyinstaller
    pyinstaller build/pyinstaller.spec

Output:
    dist/skill-se-kit  (single executable)
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Find the source root
spec_dir = os.path.dirname(os.path.abspath(SPEC))
repo_root = os.path.dirname(spec_dir)
src_root = os.path.join(repo_root, "src")

a = Analysis(
    [os.path.join(src_root, "skill_se_kit", "cli.py")],
    pathex=[src_root],
    binaries=[],
    datas=[],
    hiddenimports=[
        "skill_se_kit",
        "skill_se_kit.cli",
        "skill_se_kit.serve",
        "skill_se_kit.runtime.skill_runtime",
        "skill_se_kit.integration.auto_bootstrap",
        "skill_se_kit.integration.easy_mode",
        "skill_se_kit.intelligence.backend",
        "skill_se_kit.intelligence.local_backend",
        "skill_se_kit.intelligence.llm_backend",
        "skill_se_kit.evolution.autonomous_engine",
        "skill_se_kit.evolution.proposal_generator",
        "skill_se_kit.evolution.overlay_applier",
        "skill_se_kit.evaluation.local_evaluator",
        "skill_se_kit.evaluation.regression_runner",
        "skill_se_kit.feedback.extractor",
        "skill_se_kit.governance.governor_client",
        "skill_se_kit.governance.local_promoter",
        "skill_se_kit.protocol.adapter",
        "skill_se_kit.repair.planner",
        "skill_se_kit.reporting.evolution_reporter",
        "skill_se_kit.storage.workspace",
        "skill_se_kit.storage.knowledge_store",
        "skill_se_kit.storage.experience_store",
        "skill_se_kit.storage.skill_contract_store",
        "skill_se_kit.storage.version_store",
        "skill_se_kit.verification.hooks",
        "skill_se_kit.audit.logger",
        "skill_se_kit.provenance.store",
        "skill_se_kit.common",
        "jsonschema",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="skill-se-kit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
