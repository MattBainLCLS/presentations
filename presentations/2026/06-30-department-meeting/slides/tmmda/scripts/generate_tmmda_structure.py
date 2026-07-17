"""Generate a clean 2D skeletal structure for TMMDA
(N,N,N',N'-tetramethylmethanediamine, SMILES: CN(C)CN(C)C).

Matches the style of the existing molecule figures in the slide library:
black bonds, transparent background, implicit carbons/hydrogens, labelled
heteroatoms. Output is written to figures/ relative to the slide folder root,
so run this from the tmmda/ folder:

    ../.venv/bin/python scripts/generate_tmmda_structure.py
"""

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

SMILES = "CN(C)CN(C)C"
OUT = "figures/TMMDA_structure.png"

mol = Chem.MolFromSmiles(SMILES)
AllChem.Compute2DCoords(mol)

drawer = rdMolDraw2D.MolDraw2DCairo(700, 420)
opts = drawer.drawOptions()
opts.clearBackground = False          # transparent background
opts.bondLineWidth = 5
opts.padding = 0.12
# SLAC dark blue-grey for atom labels, matching the theme palette
opts.updateAtomPalette({7: (0.267, 0.329, 0.416)})  # N -> --slac-dark #44546A

rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
drawer.FinishDrawing()

with open(OUT, "wb") as f:
    f.write(drawer.GetDrawingText())

print(f"wrote {OUT}")
