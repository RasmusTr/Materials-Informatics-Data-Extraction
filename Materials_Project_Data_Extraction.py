rom mp_api.client import MPRester
import os 
import re 
import pandas as pd

# API configuration and target element definition
API_KEY = "sVvRkDqxcrtMFBNy4vXC6vO9lBrx9ARm"
refractory_metals = ["W", "Mo", "Ta", "Nb", "V", "Cr", "Hf", "Zr", "Ti", "Re"]

all_docs = []

# ------------------------------------------------------------------------
# 1️⃣ Search Materials Project Summary API
# ------------------------------------------------------------------------

with MPRester(API_KEY) as mpr:
    for el in refractory_metals:
        print("Scanning for element:", el)

        # Query the summary endpoint for general material properties
        docs = mpr.materials.summary.search(
            elements=[el],

            # Optional: exclude unwanted elements such as oxides or nitrides
            # exclude_elements=["O", "N", "S"],

            # Only include materials close to thermodynamic stability
            energy_above_hull=(0, 0.05),

            # Only return materials with elasticity data available
            has_props=["elasticity"],

            # Fields to retrieve from the Summary endpoint
            fields=[
                # ID
                "material_id",

                # Chemistry
                "formula_pretty",
                "formula_anonymous",
                "elements",
                "nelements",

                # Structure
                "structure",
                "nsites",
                "volume",
                "density",

                # Symmetry
                "symmetry",

                # Electronic properties
                "band_gap",
                "is_metal",
                "total_magnetization",

                # Energetics
                "formation_energy_per_atom",
                "energy_per_atom",
            ],
        )

        all_docs.extend(docs)

# Remove duplicates by material_id using a dictionary comprehension
unique_docs = {doc.material_id: doc for doc in all_docs}

# Extract material IDs for the next query
material_ids = [doc.material_id for doc in all_docs]

print(f"{len(material_ids)} materials with elasticity data found")

# ------------------------------------------------------------------------
# 2️⃣ Retrieve Elasticity Data
# ------------------------------------------------------------------------

with MPRester(API_KEY) as mpr:
    # Query the specialized elasticity endpoint using the extracted material IDs
    elastic_docs = mpr.materials.elasticity.search(
        material_ids=material_ids,
        fields=[
            "material_id",
            "bulk_modulus",
            "shear_modulus",
            "homogeneous_poisson",   # Poisson ratio
            "universal_anisotropy",  # Elastic anisotropy
        ],
    )

# Create dictionary for fast O(1) lookup during the merge phase
elastic_dict = {doc.material_id: doc for doc in elastic_docs}

# ------------------------------------------------------------------------
# 3️⃣ Merge Summary + Mechanical Properties
# ------------------------------------------------------------------------

rows = []

# Iterate through the gathered summary data to build structured row entries
for doc in all_docs:

    structure = doc.structure
    symmetry = doc.symmetry
    elastic = elastic_dict.get(doc.material_id)

    row = {

        # ----------------
        # ID
        # ----------------
        "material_id": doc.material_id,

        # ----------------
        # Chemistry
        # ----------------
        "formula_pretty": doc.formula_pretty,
        "formula_anonymous": doc.formula_anonymous,
        #"elements": doc.elements,
        "nelements": doc.nelements,
        "natoms": doc.nsites,

        # ----------------
        # Structural Properties
        # ----------------
        "a (A)": round(structure.lattice.a, 3) if structure else None,
        "b (A)": round(structure.lattice.b, 3) if structure else None,
        "c (A)": round(structure.lattice.c, 3) if structure else None,

        "alpha (deg)": round(structure.lattice.alpha, 3) if structure else None,
        "beta (deg)": round(structure.lattice.beta, 3) if structure else None,
        "gamma (deg)": round(structure.lattice.gamma, 3) if structure else None,

        "volume (A^3)": round(structure.volume, 3) if structure else None,
        "density (g/cm^3)": round(doc.density, 3),

        # ----------------
        # Symmetry
        # ----------------
        "spacegroup_symbol": symmetry.symbol if symmetry else None,
        "spacegroup_number": symmetry.number if symmetry else None,
        "crystal_system": symmetry.crystal_system if symmetry else None,

        # ----------------
        # Electronic Properties
        # ----------------
        "band_gap (eV)": round(doc.band_gap, 3),
        "is_metal (bool)": doc.is_metal,
        "total_magnetization": doc.total_magnetization,

        # ----------------
        # Energetics
        # ----------------
        "formation_energy_per_atom (eV/atom)": doc.formation_energy_per_atom,
        "energy_per_atom (eV/atom)": doc.energy_per_atom, 

        # ----------------
        # Mechanical Properties
        # ----------------
        "bulk_voigt (GPa)": round(elastic.bulk_modulus.voigt, 3) if elastic else None,
        "bulk_reuss (GPa)": round(elastic.bulk_modulus.reuss, 3) if elastic else None,
        "bulk_vrh (GPa)": round(elastic.bulk_modulus.vrh, 3) if elastic else None,

        "shear_voigt (GPa)": round(elastic.shear_modulus.voigt, 3) if elastic else None,
        "shear_reuss (GPa)": round(elastic.shear_modulus.reuss, 3) if elastic else None,
        "shear_vrh (GPa)": round(elastic.shear_modulus.vrh, 3) if elastic else None,

        "poisson_ratio": round(elastic.homogeneous_poisson, 3) if elastic else None,
        "universal_anisotropy": round(elastic.universal_anisotropy, 3) if elastic else None,
    }

    rows.append(row)

# Convert the list of structured rows into a unified Pandas DataFrame
df = pd.DataFrame(rows)

print(df.head())

# Create target directories for data storage
base_folder = "Data_Materials_Project"
os.makedirs(base_folder, exist_ok=True)

# Sanitize the file name string to guarantee operating system compatibility
name = "Mat_Project_Refractory_Raw"
safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)

# Define full file path and export dataset to a CSV file
csv_filepath = os.path.join(base_folder, f"{safe_name}.csv")
df.to_csv(csv_filepath, index=False)

print("Finished! DataFrame now contains all summary fields and mechanical properties.")
