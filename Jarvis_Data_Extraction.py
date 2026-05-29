import os
import re
import numpy as np
import pandas as pd
import requests


def lattice_vectors_to_parameters(lattice_vectors):
    """Calculate the lattice parameters (a, b, c, alpha, beta, gamma) out of

    three lattice vectors.

    Args:
        lattice_vectors: list of three vectors [[ax, ay, az], [bx, by, bz], [cx,
        cy, cz]]

    Returns:
        dict with a, b, c, alpha, beta, gamma
    """
    # Convert input lattice vectors into NumPy arrays for vector calculations
    a_vec = np.array(lattice_vectors[0])
    b_vec = np.array(lattice_vectors[1])
    c_vec = np.array(lattice_vectors[2])

    # Compute the magnitude (length) of each vector using the Euclidean norm
    a = np.linalg.norm(a_vec)
    b = np.linalg.norm(b_vec)
    c = np.linalg.norm(c_vec)

    # Compute unit cell angles in degrees using the dot product formula
    alpha = np.degrees(np.arccos(np.dot(b_vec, c_vec) / (b * c)))
    beta = np.degrees(np.arccos(np.dot(a_vec, c_vec) / (a * c)))
    gamma = np.degrees(np.arccos(np.dot(a_vec, b_vec) / (a * b)))

    return {
        "a (A)": a,
        "b (A)": b,
        "c (A)": c,
        "alpha (deg)": alpha,
        "beta (deg)": beta,
        "gamma (deg)": gamma,
    }


def jarvis_optimade_query(query):
    """Query the JARVIS OPTIMADE API and handle pagination to retrieve all

    matching records.
    """
    base_url = "https://jarvis.nist.gov/optimade/jarvisdft/v1/structures/?filter="
    url = base_url + query
    results = []

    # Loop through paginated results as long as a 'next' link is provided
    while url:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Append data from the current page to the master list
        results.extend(data["data"])
        url = data.get("links", {}).get("next")

    return results


# Target list of refractory and transition elements to scan
element_list = ["W", "Mo", "Ta", "Nb", "V", "Cr", "Hf", "Zr", "Ti", "Re"]
entries = []

# Loop through each element and fetch matching records from the API
for el in element_list:
    query = f"elements HAS ANY {el}"
    print("Scanning:", el)
    results = jarvis_optimade_query(query)
    entries.extend(results)

# Remove duplicate entries using the unique material ID as the dictionary key
unique_entries = {e["id"]: e for e in entries}
entries = list(unique_entries.values())
print("Found number of unique materials:", len(entries))


# -----------------------------------------------------------------
# Extract and parse material properties
# -----------------------------------------------------------------
materials_data = []

for entry in entries:
    attr = entry["attributes"]

    # Map general OPTIMADE fields and JARVIS-specific custom attributes
    mat_dict = {
        "material_id": entry["id"],
        "formula_pretty": attr.get("chemical_formula_reduced"),
        "natoms": attr.get("nsites"),
        "formula_anonymous": attr.get("chemical_formula_anonymous"),
        "chemical_formula_descriptive": attr.get(
            "chemical_formula_descriptive"
        ),
        "bulk_voigt (GPa)": attr.get("_jarvis_bulk_modulus_kv"),
        "shear_voigt (GPa)": attr.get("_jarvis_shear_modulus_gv"),
        "poisson_ratio": attr.get("_jarvis_poisson"),
        "crystal_system": attr.get("_jarvis_crys"),
        "spacegroup_symbol": attr.get("_jarvis_spg_symbol"),
        "spacegroup_number": attr.get("_jarvis_spg_number"),
        "density (g/cm^3)": attr.get("_jarvis_density"),
        "nelements": attr.get("nelements"),
        "Material Type": attr.get("_jarvis_typ"),
        "band_gap (eV)": attr.get("_jarvis_mbj_bandgap"),
        "dimensionality": attr.get("_jarvis_dimensionality"),
    }

    # If the entry contains lattice vectors, compute and append lattice parameters
    lattice_vectors = attr.get("lattice_vectors")
    if lattice_vectors:
        mat_dict.update(lattice_vectors_to_parameters(lattice_vectors))

    materials_data.append(mat_dict)


# -----------------------------------------------------------------
# Create DataFrame and export dataset
# -----------------------------------------------------------------
df = pd.DataFrame(materials_data)
print(df.shape)
print(df.head())

# Set up storage directory and ensure it exists locally
base_folder = "Data_Jarvis"
os.makedirs(base_folder, exist_ok=True)

# Sanitize file name to prevent OS naming conflicts
name = "Jarvis_Refractory_Raw"
safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)
csv_filepath = os.path.join(base_folder, f"{safe_name}.csv")

# Save processed structural and elastic properties data to CSV
df.to_csv(csv_filepath, index=False)

print("Done. Dataframe contains all formulas and their properties.")
