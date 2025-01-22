from pathlib import Path
import shutil 
from ase.io import read
from tqdm import tqdm
from multiprocessing import Pool

TRANSITION_METALS = {'Co', 'Cr', 'Fe', 'Mn', 'Mo', 'Ni', 'V', 'W'}
ANIONS = {'O', 'F'}

def contains_tm_and_anion(atoms):
    symbols = set(atoms.get_chemical_symbols())
    return bool(symbols & TRANSITION_METALS) and bool(symbols & ANIONS)

mptrj_dir = Path('mptrj-gga-ggapu')
mptrj_ggapu_dir = Path('mptrj-ggapu'); mptrj_ggapu_dir.mkdir(exist_ok=True)
mptrj_gga_dir = Path('mptrj-gga'); mptrj_gga_dir.mkdir(exist_ok=True)


def process_file(mp_entry):
    atoms = read(mp_entry, '0')
    if contains_tm_and_anion(atoms):
        shutil.copy2(mp_entry, mptrj_ggapu_dir / mp_entry.name)
    else:
        shutil.copy2(mp_entry, mptrj_gga_dir / mp_entry.name)

if __name__ == '__main__':
    files = list(mptrj_dir.iterdir())
    with Pool() as pool:
        list(tqdm(pool.imap(process_file, files), total=len(files)))
