import json
import re
import os 
import pandas as pd

from json import JSONDecodeError
from urllib.request import urlopen

# Define API server endpoints
SERVER = "https://aflow.org"
API = "/API/aflux/?"

def aflux_request(matchbook, paging=1, no_directives=False):
    """
    Download an AFLUX API response and return it as a list of dictionaries.
    """
    request_url = SERVER + API + matchbook
    
    # Append pagination and format directives unless explicitly disabled
    if not no_directives:
        request_url += f",$paging({paging}),format(json)"
        
    server_response = urlopen(request_url)
    response_content = server_response.read().decode("utf-8")
    
    # Process response data if the HTTP request status is successful
    if server_response.getcode() == 200:
        try:
            return json.loads(response_content)
        except JSONDecodeError:
            pass
            
    print("AFLUX request failed!")
    print(f"  URL: {request_url}")
    print(f"  Response: {response_content}")
    return []

def aflux_help(keyword=None):
    """
    Print the built-in documentation and property keywords provided by the AFLUX API.
    """
    if keyword is None:
        # Fetch and display general API documentation overview
        help_data = aflux_request("", no_directives=True)
        print("\n".join(help_data))
    else:
        # Fetch metadata details for a specific database keyword
        help_data = aflux_request(f"help({keyword})")
        for key, entry in help_data.items():
            print(key)
            print(f"  description: {entry['description']}")
            print(f"  units: {entry['units']}")
            print(f"  status: {entry['status']}")
            comment = "\n    ".join(entry["__comment__"]).strip()
            if comment:
                print(f"  comment:\n    {comment}")

# Target list of refractory elements to systematically scan
elements = ["W", "Mo", "Ta", "Nb", "V", "Cr", "Hf", "Zr", "Ti", "Re"]
materials = []

# Ensure the local data directory exists on the system
os.makedirs("Data_Aflow", exist_ok=True)

for el in elements:
    print("Scanning for:", el)
    
    # Construct comma-separated property keywords string required for API response mapping
    query = (
        "auid,aurl,"  # Added to prevent key errors during data extraction
        "agl_bulk_modulus_isothermal_300K,agl_bulk_modulus_static_300K,"
        "ael_youngs_modulus_vrh,ael_bulk_modulus_vrh,ael_shear_modulus_vrh,"
        "agl_heat_capacity_Cp_300K,Wyckoff_letters,Wyckoff_multiplicities,Wyckoff_site_symmetries,ael_shear_modulus_reuss,ael_shear_modulus_voigt,"
        "ael_bulk_modulus_reuss,ael_debye_temperature,ael_bulk_modulus_voigt,positions_fractional,compound,"
        "ael_poisson_ratio,geometry,lattice_system_relax,nspecies,natoms,spacegroup_relax,"
        f"species({el}),composition,density,crystal_system,volume_cell,crystal_family,"
        "crystal_class,Bravais_lattice_lattice_system,agl_thermal_expansion_300K,"
        "agl_thermal_conductivity_300K,agl_heat_capacity_Cv_300K,catalog(icsd),"
        "Bravais_lattice_relax,Egap,Egap_type,species"
    )

    page = 1
    
    # Paginate through the server entries until no more matching materials are returned
    while True:
        data = aflux_request(query, paging=page)

        # Break loop when current result page returns empty data
        if len(data) == 0:
            break
        
        # Unpack JSON data into structured dictionary formats
        for material in data:      
            entry = {
                "formula_pretty": material["compound"],
                "material_id": material["auid"],
                "aurl": material["aurl"],
                
                # Elastic and Mechanical Properties
                "bulk_vrh (GPa)": material["ael_bulk_modulus_vrh"],  # Corrected duplicate key assignment
                "bulk_reuss (GPa)": material["ael_bulk_modulus_reuss"],
                "bulk_voigt (GPa)": material["ael_bulk_modulus_voigt"],
                "shear_vrh (GPa)": material["ael_shear_modulus_vrh"],
                "shear_reuss (GPa)": material["ael_shear_modulus_reuss"],
                "shear_voigt (GPa)": material["ael_shear_modulus_voigt"],   
                "poisson_ratio": material["ael_poisson_ratio"],
                "young_modulus_vrh (GPa)": material["ael_youngs_modulus_vrh"],
                "bulk_modulus_isothermal_300K (GPa)": material["agl_bulk_modulus_isothermal_300K"],
                "bulk_modulus_static_300K (GPa)": material["agl_bulk_modulus_static_300K"],
                
                # Lattice Parameter Vectors
                "a (A)": material["geometry"][0],
                "b (A)": material["geometry"][1],
                "c (A)": material["geometry"][2],
                "alpha (deg)": material["geometry"][3],
                "beta (deg)": material["geometry"][4],
                "gamma (deg)": material["geometry"][5],
                
                # Species Metrics
                "nelements": material["nspecies"],
                "natoms": material["natoms"],
                "elements": material["species"],
                "composition": material["composition"],
                
                # Volumetric and Crystal System Metadata
                "density (g/cm^3)": material["density"],
                "volume (A^3)": material["volume_cell"],
                "crystal_system": material["crystal_system"],
                "spacegroup_number": material["spacegroup_relax"],
                
                # Thermodynamic Properties
                "thermal_expansion_300K (K^-1)": material["agl_thermal_expansion_300K"],
                "thermal_conductivity_300K (W/mK)": material["agl_thermal_conductivity_300K"],
                "heat_capacity_Cv_300K (k_B/cell)": material["agl_heat_capacity_Cv_300K"],
                "heat_capacity_Cp_300K (k_B/cell)": material["agl_heat_capacity_Cp_300K"],
                "debye temperautre (K)": material["ael_debye_temperature"],
                
                # Electronic and Structural Symmetry Data
                "band_gap (eV)": material["Egap"],
                "Egap_type": material["Egap_type"],
                "Wyckoff_letters": material["Wyckoff_letters"],
                "Wyckoff_multiplicities": material["Wyckoff_multiplicities"],
                "Wyckoff_site_symmetries": material["Wyckoff_site_symmetries"],
                "species": material["species"],
                "positions_fractional": material["positions_fractional"]
            }
        
            materials.append(entry)
            
            # Construct DataFrame from accumulated entries list
            df = pd.DataFrame(materials)

            # Persist dataset modifications iteratively onto disk
            csv_path = "Data_Aflow/Aflow_Refractory_Raw.csv"
            df.to_csv(csv_path, index=False)
        
        print(f"{el} page {page}: {len(data)}")
        page += 1

# Display final diagnostics once queries finish execution
print(f"Saved: {csv_path}")
print(df.shape)
print(df)
