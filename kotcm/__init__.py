"""kotcm : le mode creatif de King of Thieves (formes de base, pieges editables).

Spec : docs/superpowers/specs/2026-10-13-kotcm-mode-creatif-design.md.
N'importe rien de controller/ ni de scripts/ : le paquet doit pouvoir partir seul.
Le noyau commun (`kotnoyau`) vient du venv, ou de la copie de `_noyau/` dans le depot publie.
"""

import sys
from pathlib import Path

try:
    import kotnoyau  # noqa: F401  (installe en editable dans le depot prive)
except ImportError:  # depot publie : le noyau est recopie sous kotcm/_noyau/ (scripts/publier_kotcm.py)
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_noyau"))
