import os
import re
import numpy as np
import pandas as pd
import requests


def lattice_vectors_to_parameters(lattice_vectors):
    """Calculate lattice parameters (a, b, c, alpha, beta, gamma)

    from three 3D lattice vectors.
    """

    # Convert incoming lattice vectors into NumPy arrays for vector operations
    a_vec = np.array(lattice_vectors[0])
    b_vec = np.array(lattice_vectors[1])
    c_vec = np.array(lattice_vectors[2])

    # Calculate the magnitude (length) of each lattice vector
    a = np.linalg.norm(a_vec)
    b = np.linalg.norm(b_vec)
    c = np.linalg.norm(c_vec)

    # Compute unit cell angles (alpha, beta, gamma) in degrees using the dot product formula
    alpha = np.degrees(np.arccos(np.dot(b_vec, c_vec) / (b * c)))
    beta = np.degrees(np.arccos(np.dot(a_vec, c_vec) / (a * c)))
    gamma = np.degrees(np.arccos(np.dot(a_vec, b_vec) / (a * b)))

    return {
        "a": a,
        "b": b,
        "c": c,
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
    }


# Base URL for the OPTIMADE API endpoint providing crystal structures
url = "http://optimade.openmaterialsdb.se/v1/structures"

# List of target refractory metals to query
refractory_metals = ["Nb", "Ta", "Cr", "Mo", "W"]
results = []

# -----------------------------------------------------------------
# Query OPTIMADE API
# -----------------------------------------------------------------

for metal in refractory_metals:
    print("Scanning for materials containing", metal)

    # Define API parameters: filter by element and specify required fields to minimize payload
    params = {
        "filter": f'elements HAS "{metal}"',
        "response_fields": "id,elements,chemical_formula_reduced,lattice_vectors,nelements,nperiodic_dimensions,structure_features,chemical_formula_anonymous,dimension_types,nsites",
    }

    # Execute the GET request and automatically throw an exception for HTTP errors
    response = requests.get(url, params=params)
    response.raise_for_status()

    # Parse JSON response and append retrieved structures to the main results list
    data = response.json()
    results.extend(data["data"])


# -----------------------------------------------------------------
# Remove duplicates
# -----------------------------------------------------------------

# Eliminate duplicate entries by mapping unique structure IDs to their corresponding data object
unique_materials = {entry["id"]: entry for entry in results}

print(f"Materials found: {len(unique_materials)}")


# -----------------------------------------------------------------
# Extract material properties
# -----------------------------------------------------------------

rows = []

for entry in unique_materials.values():
    attrs = entry["attributes"]
    lattice_vectors = attrs.get("lattice_vectors")

    # Map raw API attributes into a structured dictionary format for each entry
    mat_dict = {
        "material_id": entry.get("id"),
        "formula_reduced": attrs.get("chemical_formula_reduced"),
        "formula_anonymous": attrs.get("chemical_formula_anonymous"),
        "elements": attrs.get("elements"),
        "nelements": attrs.get("nelements"),
        "nsites": attrs.get("nsites"),
        "nperiodic_dimensions": attrs.get("nperiodic_dimensions"),
        "dimension_types": attrs.get("dimension_types"),
    }

    # If lattice vectors are available, calculate and merge structural parameters (a, b, c, etc.)
    if lattice_vectors:
        mat_dict.update(lattice_vectors_to_parameters(lattice_vectors))

    rows.append(mat_dict)


# -----------------------------------------------------------------
# Build DataFrame and export to CSV
# -----------------------------------------------------------------

# Convert the list of structured dictionaries into a Pandas DataFrame
df = pd.DataFrame(rows)

print(df.head())

# Define destination directory and ensure it exists locally
base_folder = "Data_Open_Materials_Database"
os.makedirs(base_folder, exist_ok=True)

# Sanitize the file name to replace any OS-unfriendly characters with underscores
name = "Refractory_Metals_Data"
safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)
csv_filepath = os.path.join(base_folder, f"{safe_name}.csv")

# Export the final dataset to a CSV file without writing row indices
df.to_csv(csv_filepath, index=False)

print("Finished.")
