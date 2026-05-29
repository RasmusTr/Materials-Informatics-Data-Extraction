import os
import pandas as pd
import requests

# Base URL for the NOMAD Repository API (v1)
base_url = "http://nomad-lab.eu/prod/v1/api/v1"

# Define the search criteria payload for the initial API query
query = {
    "query": {
        # Match structures containing at least one of these target metals
        "results.material.elements": {
            "any": ["W", "Mo", "V", "Cr", "Ti", "Nb"]
        },
        "results.material.structural_type": "bulk",  # Only bulk materials (no surfaces/molecules)
        "results.properties.electronic.band_gap.value": {
            "lte": 0.1
        },  # Metallic/near-metallic systems
        "results.material.n_elements": {
            "lte": 4
        },  # Limit to quaternary systems or simpler
        # Target specific Bravais lattices (e.g., Body-Centered Cubic, Face-Centered Cubic, Hexagonal Primitive)
        "results.material.symmetry.bravais_lattice": {
            "any": ["cI", "cF", "hP"]
        },
        "results.material.topology.cell.mass_density": {
            "gte": 5000
        },  # Lower bound for mass density (kg/m^3)
    },
}


def get_all_entries():
    """Retrieves all matching entry IDs from NOMAD using server-side cursor-based

    pagination.
    """
    page_size = 500
    search_after = None  # Holds the pagination token/ID of the last item from the previous page
    all_entries = []
    first_page = True

    while True:
        # Define pagination rules; sorting by entry_id is required for search_after cursor functionality
        pagination = {
            "page_size": page_size,
            "order_by": "entry_id",
            "order": "asc",
        }

        # If we have a cursor from the previous page, inject it into the pagination object
        if search_after:
            pagination["search_after"] = [search_after]

        # Send POST request to find matching entry IDs
        response = requests.post(
            f"{base_url}/entries/query",
            json={
                "query": query["query"],
                "pagination": pagination,
                "required": {
                    "include": ["entry_id"]
                },  # Only request IDs to optimize network load
            },
        )

        response_json = response.json()
        entries = response_json.get("data", [])

        # On the first API call, extract and print the total expected hits
        if first_page:
            total_entries = response_json.get("pagination", {}).get("total")
            print(f"Total number of matches: {total_entries}")
            first_page = False

        # Break loop if the server returns no entries (end of dataset reached)
        if not entries:
            print("No more entries – end reached.")
            break

        all_entries.extend(entries)

        # Update the cursor token to the last entry ID fetched on this page
        search_after = entries[-1]["entry_id"]

        print(f"{len(all_entries)} entries loaded...")

        # Guard rail: Stop instantly if we hit or exceed the total record count
        if total_entries and len(all_entries) >= total_entries:
            print(f"All {total_entries} entries loaded – finished.")
            break

    # Flatten the list of dictionaries down to a pure list of string IDs
    all_entry_ids = [e["entry_id"] for e in all_entries]
    print(f"Finished! {len(all_entries)} total entries loaded.")

    return all_entries, all_entry_ids


# Run the pagination loop to fetch all material target IDs
all_entries, all_entry_ids = get_all_entries()
print(f"✅ Total number of entry_ids: {len(all_entry_ids)}")


# -----------------------------------------------------------------
# Setup Target Output Dataset Structure
# -----------------------------------------------------------------
output_file = "results_all.csv"
batch_size = 500

# Explicitly declare structural, electronic, and thermodynamic tracking features
columns = [
    "entry_id",
    "is_stable",
    "space_group_symbol",
    "space_group_number",
    "point_group",
    "final_displacement_maximum",
    "crystal_system",
    "bravais_lattice",
    "chemical_formula_reduced",
    "chemical_formula_iupac",
    "mass_fractions",
    "n_temperatures",
    "thermal_expansion",
    "thermal_conductivity",
    "a",
    "b",
    "c",
    "alpha",
    "beta",
    "gamma",
    "volume",
    "mass_density",
    "n_atoms",
    "n_values",
    "heat_capacity_c_v_specific",
    "n_elements",
    "elements",
    "energy_hulll",
]

# Initialize empty DataFrame with the specified columns
df = pd.DataFrame(columns=columns)

print("Starting archive query")

# Loop through each verified entry ID to request its detailed calculations archive
for entry in all_entries:
    entry_id = entry["entry_id"]

    # Request specialized raw archive metrics for this specific entry ID
    archive_response = requests.post(
        f"{base_url}/entries/{entry_id}/archive/query",
        json={
            "required": {
                # Request thermodynamic phase and stability trees
                "workflow": {
                    "convex_hull": {"energy_hulll": "*"},
                    "thermodynamics": {
                        "n_values": "*",
                        "heat_capacity_c_v_specific": "*",
                        "stability": {"is_stable": "*"},
                    },
                    # Request semi-empirical thermal calculations
                    "debye_model": {
                        "n_temperatures": "*",
                        "thermal_expansion": "*",
                        "thermal_conductivity": "*",
                    },
                },
                # Request material classifications, structural geometries, and optimization pathways
                "results": {
                    "material": {
                        "n_elements": "*",
                        "elements": "*",
                        "chemical_formula_reduced": "*",
                        "chemical_formula_iupac": "*",
                        "elemental_composition": {"mass_fraction": "*"},
                        "symmetry": {"crystal_system": "*", "bravais_lattice": "*"},
                        "topology": {
                            "n_atoms": "*",
                            "cell": "*",
                            "symmetry": {
                                "space_group_symbol": "*",
                                "space_group_number": "*",
                                "point_group": "*",
                            },
                        },
                    },
                    "properties": {
                        "geometry_optimization": {
                            "final_displacement_maximum": "*"
                        }
                    },
                },
            }
        },
    )

    archive_json = archive_response.json()
    archive_results = (
        archive_json.get("data", {})
        .get("archive", {})
        .get("results", {})
    )

    # --- 1. Deep Parse Topology and Spacegroups ---
    topologies = archive_results.get("material", {}).get("topology", [])

    space_group_symbol = None
    space_group_number = None
    point_group = None

    # Loop through structural subsystems to find valid spacegroup and symmetry tags
    for topo in topologies:
        sym = topo.get("symmetry")

        if sym and "space_group_number" in sym:
            space_group_number = sym["space_group_number"]

        if sym and "space_group_symbol" in sym:
            space_group_symbol = sym["space_group_symbol"]

        if sym and "point_group" in sym:
            point_group = sym["point_group"]
            break  # Break once primary structural system properties are secured

    # --- 2. Deep Parse Stability Workflows ---
    thermodynamics = (
        archive_json.get("workflow", {}).get("archive", {})
        .get("workflow", {})
        .get("thermodynamics", {})
    )
    is_stable = thermodynamics.get("stability", {}).get("is_stable")

    # --- 3. Deep Parse Cell Geometry Metrics ---
    lattice_parameters = {}
    n_atoms = None

    if topologies:
        lattice_parameters = topologies[0].get("cell", {})
        n_atoms = topologies[0].get("n_atoms")

    # Extract 1D cell lengths and internal angles
    a = lattice_parameters.get("a")
    b = lattice_parameters.get("b")
    c = lattice_parameters.get("c")

    alpha = lattice_parameters.get("alpha")
    beta = lattice_parameters.get("beta")
    gamma = lattice_parameters.get("gamma")

    volume = lattice_parameters.get("volume")
    mass_density = lattice_parameters.get("mass_density")

    # --- 4. Deep Parse General Material and Symmetry Attributes ---
    final_displacement_maximum = (
        archive_results.get("properties", {})
        .get("geometry_optimization", {})
        .get("final_displacement_maximum")
    )
    crystal_system = (
        archive_results.get("material", {})
        .get("symmetry", {})
        .get("crystal_system")
    )
    bravais_lattice = (
        archive_results.get("material", {})
        .get("symmetry", {})
        .get("bravais_lattice")
    )
    chemical_formula_reduced = archive_results.get("material", {}).get(
        "chemical_formula_reduced"
    )
    chemical_formula_iupac = archive_results.get("material", {}).get(
        "chemical_formula_iupac"
    )
    elements = archive_results.get("material", {}).get("elements", [])

    # Extract dynamic composition lists (mass fraction lists per element)
    elemental_composition = archive_results.get("material", {}).get(
        "elemental_composition", []
    )
    mass_fractions = [el.get("mass_fraction") for el in elemental_composition]

    # --- 5. Deep Parse Debye Model Properties ---
    debye_model = archive_results.get("workflow", {}).get("debye_model", [])
    n_temperatures = [n_temp.get("n_temperatures") for n_temp in debye_model]
    thermal_expansion = [
        therm_ex.get("thermal_expansion") for therm_ex in debye_model
    ]
    thermal_conductivity = [
        therm_conduc.get("thermal_conductivity") for therm_conduc in debye_model
    ]

    # --- 6. Deep Parse Energy Profiles ---
    n_values = [n_val.get("n_values") for n_val in debye_model]  # Fix reference context if needed
    heat_capacity_c_v_specific = [
        specific_heat.get("heat_capacity_c_v_specific")
        for specific_heat in debye_model
    ]
    energy_hulll = (
        archive_results.get("workflow", {})
        .get("convex_hull", {})
        .get("energy_hulll")
    )

    # Package parsed metadata into a unified row layout
    new_row = {
        "entry_id": entry_id,
        "is_stable": is_stable,
        "space_group_symbol": space_group_symbol,
        "space_group_number": space_group_number,
        "point_group": point_group,
        "final_displacement_maximum": final_displacement_maximum,
        "crystal_system": crystal_system,
        "bravais_lattice": bravais_lattice,
        "chemical_formula_reduced": chemical_formula_reduced,
        "chemical_formula_iupac": chemical_formula_iupac,
        "mass_fractions": mass_fractions,
        "n_temperatures": n_temperatures,
        "thermal_expansion": thermal_expansion,
        "thermal_conductivity": thermal_conductivity,
        "a": a,
        "b": b,
        "c": c,
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "volume": volume,
        "mass_density": mass_density,
        "n_atoms": n_atoms,
        "n_values": n_values,
        "heat_capacity_c_v_specific": heat_capacity_c_v_specific,
        "n_elements": len(elements),
        "elements": elements,
        "energy_hulll": energy_hulll,
    }

    # Append row directly to the bottom of the DataFrame
    df.loc[len(df)] = new_row

    # Periodic IO checkpoint flushing to avoid total data loss during long execution runs
    if len(df) % batch_size == 0:
        df.to_csv(output_file, index=False)
        print(f"{len(df)} entries saved.")

print(df)

# Final export step to write out all accumulated archive files
df.to_csv(output_file, index=False)
print("Final file saved.")
