from pathlib import Path
import shutil 
from ase.io import read, write
from tqdm import tqdm
from multiprocessing import Pool
from sklearn.model_selection import train_test_split

TRANSITION_METALS = {'Co', 'Cr', 'Fe', 'Mn', 'Mo', 'Ni', 'V', 'W'}
ANIONS = {'O', 'F'}

def contains_tm_and_anion(atoms):
    symbols = set(atoms.get_chemical_symbols())
    return bool(symbols & TRANSITION_METALS) and bool(symbols & ANIONS)

def sort_file(f):
    configs = read(f, ':')
    return (configs, contains_tm_and_anion(configs[0]))

def write_configs(args):
    configs, dir_path = args
    print(f"Writing {len(configs)} configs to {dir_path}")
    for c in tqdm(configs):
        write(dir_path / f"{c.info['mp_id']}.extxyz", c, append=True)

def count_get_all_elements(configs):
    elements = set()
    for config in configs:
        for element in config.get_chemical_symbols():
            elements.add(element)
    return elements

if __name__ == '__main__':

    mptrj_dir = Path('mptrj-gga-ggapu') # Downloaded from https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0/training_data.zip
    files = list(mptrj_dir.iterdir())
    
    # Sort files into GGA and GGA+U in parallel
    with Pool() as pool:
        results = list(tqdm(pool.imap(sort_file, files), total=len(files)))
    
    # Separate results into GGA and GGA+U lists
    gga_configs_ = [configs for configs, is_ggapu in results if not is_ggapu]
    gga_configs = []
    for c in gga_configs_:
        for atoms in c:
            atoms.info['REF_energy'] = atoms.get_total_energy()
            atoms.arrays['REF_forces'] = atoms.get_forces()
            atoms.info['REF_stress'] = atoms.get_stress(voigt=False).flatten()
        gga_configs.extend(c)
    write('mptrj-gga.xyz', gga_configs)
    gga_elements = count_get_all_elements(gga_configs)
    del gga_configs

    ggapu_config_ = [configs for configs, is_ggapu in results if is_ggapu]
    ggapu_configs = []
    for c in ggapu_config_:
        for atoms in c:
            atoms.info['REF_energy'] = atoms.get_total_energy()
            atoms.arrays['REF_forces'] = atoms.get_forces()
            atoms.info['REF_stress'] = atoms.get_stress(voigt=False).flatten()
        ggapu_configs.extend(c)
    write('mptrj-ggapu.xyz', ggapu_configs)
    ggapu_elements = count_get_all_elements(ggapu_configs)

    # add IsolatedAtoms
    e0s = read('isolated_atoms_VASP_PBE.extxyz', ':')

    write('mptrj-gga.xyz', [config for config in e0s if config[0].symbol in gga_elements], append=True)
    write('mptrj-ggapu.xyz', [config for config in e0s if config[0].symbol in ggapu_elements], append=True)
