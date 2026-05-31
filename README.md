# 📊 Materials Data Extraction with Jupyter Notebook

## 📖 Overview

This project contains a Jupyter Notebook-based workflow designed to extract materials data from multiple online materials science databases. The goal is to collect, unify, and prepare data for further analysis in the field of Materials Informatics.

The notebook demonstrates how to programmatically access, query, and process structured and semi-structured materials data from various sources.

In the code ... Example request are given on the basis for Refractory Metals (Mo, W, Nb, Cr, Ta, ...) 

---

##  Purpose

The main objectives of this project are:

* Automate the extraction of materials data
* Access multiple databases through APIs or web scraping
* Standardize heterogeneous data formats
* Prepare datasets for further analysis (machine learning) 

---

##  Technologies Used

* Python
* Jupyter Notebook
* Libraries:

  * pandas
  * requests
  * selenium

---

##  Data Sources

The following materials databases are accessed:

* JARVIS (Joint Automated Repository for Various Integrated Simulations)
* AFLOW (Automatic Flow for Materials Discovery)
* NOMAD (Novel Materials Discovery Laboratory)
* Materials Project
* MatWeb
* Open Materials Database (OMDB)

---

##  Functionality

The notebook includes functionality to:

* Query APIs (where available)
* Extract structured data (e.g., JSON responses)
* Scrape tabular data from web pages (e.g., MatWeb)
* Clean and preprocess raw data
* Combine datasets from multiple sources

---

##  Example Use Cases

* Filtering materials by properties (e.g., band gap, density)
* Collecting datasets for machine learning models
* Comparing data across different databases
* Identifying candidate materials for specific applications

---

##  Getting Started

### 1. Clone the repository

```bash
git clone <[your-repo-url](https://github.com/RasmusTr/Materials-Informatics-Data-Extraction)>
```

### 2. Install dependencies

```bash
python 3.11
pip install pandas requests selenium aflow 
```

### 3. Run the notebook

```bash
jupyter notebook
```

---

##  Notes

* Some databases require API keys (e.g., Materials Project)
* Web scraping (e.g., MatWeb) may depend on website structure and can break if the site changes
* Please respect database usage policies and rate limits

---
## Explanation of the Code: 
### 1. AFLOW API Refractory Materials Extractor

This component automates data mining from the AFLOW Distributed Materials Database using the AFLUX search API. It targets specific refractory transition metals to compile an extensive raw dataset of elastic, structural, electronic, and thermodynamic properties.

### Key Capabilities

* **Targeted Material Scraping:** Systematically queries data for a defined suite of refractory elements (`W`, `Mo`, `Ta`, `Nb`, `V`, `Cr`, `Hf`, `Zr`, `Ti`, `Re`).
* **Comprehensive Feature Retrieval:** Extracts over 30 physical properties per crystal structure, including Voigt-Reuss-Hill (VRH) elastic moduli, lattice parameters, thermal conductivity, heat capacity, Debye temperatures, and electronic band gaps.
* **Auto-Pagination Loop:** Seamlessly handles multi-page API responses per element to ensure entire database catalogs (such as ICSD sub-inventories) are fully extracted.
* **Incremental Checkpoint Saves:** Converts raw JSON API responses into flat dictionary frames and streams data directly into a structured CSV file (`Data_Aflow/Aflow_Refractory_Raw.csv`) to prevent data loss during network execution.

### How it Connects to AFLUX

The script communicates directly with the AFLOW server over standard HTTP via the following workflow:
1. **Query Construction:** Builds a custom AFLUX query string matching structural properties with database keywords.
2. **REST Request Execution:** Submits requests using Python's native `urllib.request` layer, dynamically managing structural formats and token indexing (`$paging()`, `format(json)`).

### 2. Materials Project API Refractory Materials Extractor

This component automates data mining from the Materials Project (MP) Database using the official `mp-api` client. It extracts thermodynamic stability markers, electronic features, and detailed anisotropic elastic properties for target refractory alloys and elements.

### Key Capabilities

* **Multi-Stage API Orchestration:** Conducts a synchronized two-step data retrieval pipeline. It first searches the core `summary` endpoint to isolate qualifying crystal structures, then uses the extracted material IDs to pull specialized mechanical metrics from the `elasticity` endpoint.
* **Thermodynamic Stability Filtering:** Restricts searches using the `energy_above_hull` parameter (set to 0–0.05 eV/atom), ensuring that only stable or highly meta-stable crystal phases are captured for the feature dataset.
* **Detailed Mechanical Property Mapping:** Extracts Voigt, Reuss, and Voigt-Reuss-Hill (VRH) bounds for both bulk and shear moduli, along with isotropic Poisson ratios and universal elastic anisotropy indices.
* **Automated Data Consolidation:** Merges complex, nested crystal structural data (such as fractional lattice vectors and spacegroup symmetry metadata) into a flat, tabular format before exporting directly to a CSV file (`Data_Materials_Project/Mat_Project_Refractory_Raw.csv`).

### 3. OPTIMADE API Refractory Materials Extractor

This component interfaces with the Open Materials Database utilizing the standardized OPTIMADE (Open Databases Integration for Materials Design) REST API specification. It queries structural records containing specific refractory metals and translates raw vector matrices into canonical crystallographic lattice parameters.

### Key Capabilities

* **Standardized API Filtering:** Leverages the specialized OPTIMADE filter query syntax (`elements HAS "Metal"`) to efficiently target structure sub-groups across multi-element chemical profiles.
* **Vector-to-Parameter Reconstruction:** Contains an automated linear algebra engine that takes raw $3\times3$ `lattice_vectors` coordinate arrays and computes explicit unit cell lengths ($a$, $b$, $c$) via Euclidean norms, as well as interaxial angles ($\alpha$, $\beta$, $\gamma$) via normalized dot-product inversions.
* **Dimensionality & Periodicity Metadata Tracking:** Extracts structural metadata properties, including boundary dimensional boundaries (`dimension_types`) and periodic constraints (`nperiodic_dimensions`), ensuring accurate modeling contexts for low-dimensional systems or bulk phases.
* **Idempotent Data Sanitization:** Tracks unique entry keys to filter out duplicate material nodes fetched across overlapping multi-element query sets before saving down to a CSV file (`Data_Open_Materials_Database/Refractory_Metals_Data.csv`).

### How it Connects to OpenMaterialsDB

The execution pipeline standardizes query data transmission through the following workflow:
1. **Payload Specification:** Limits API data transport overloads by configuring explicit `response_fields` parameter restrictions within standard `requests.get` routines.
2. **Dynamic Crystal Expansion:** Programmatically updates row dictionaries on-the-fly, combining static string descriptors with dynamically derived physical metrics.
3. **Robust IO File Handling:** Verifies directory paths and automatically targets local file systems while preserving full file path compliance across differing host operating systems.

### 4. JARVIS-DFT OPTIMADE Data Harvester

This component interfaces with the NIST JARVIS-DFT database using the standardized OPTIMADE REST API specification. It programmatically crawls material structures containing advanced refractory and transition elements, automatically handles API pagination, and extracts both structural geometries and high-fidelity DFT-computed elastic and electronic properties.

### Key Capabilities

* **Automated Pagination & Cursor Traversal:** Implements a robust `while` loop that dynamically tracks the API's `next` pagination links, ensuring full dataset retrieval across large multi-page query responses without data loss.
* **Elastic & Electronic Property Mapping:** Extracts advanced quantum-mechanical properties calculated via density functional theory (DFT), including Voigt bulk/shear moduli (`bulk_voigt`, `shear_voigt`), Poisson’s ratio (`poisson_ratio`), Modified Becke-Johnson band gaps (`band_gap`), and structural dimensionality.
* **Symmetry & Spacegroup Resolution:** Captures localized crystallographic symmetry data, including explicit crystal systems, space group symbols, and international space group numbers for downstream material classification.
* **Crystallographic Matrix Transformation:** Integrates a vector reconstruction engine that converts raw $3\times3$ coordinate arrays into physical unit cell lengths ($a$, $b$, $c$ in Angstroms) and interaxial angles ($\alpha$, $\beta$, $\gamma$ in degrees).

### How it Connects to JARVIS-DFT

The execution pipeline standardizes query data transmission through the following workflow:
1. **Multi-Element Batch Scanning:** Executes sequential requests across an expanded transition-metal array using the `elements HAS ANY` filter syntax, accumulating raw structural data records.
2. **Key-Based Deduplication:** Eliminates overlapping dataset nodes from multi-component systems by mapping entries into a unique ID dictionary before converting them into a flat tabular format.
3. **Data Framing & Safe IO Persistence:** Compiles the heterogeneous property dictionaries into a structured Pandas DataFrame and saves the sanitized output to a secure local file path (`Data_Jarvis/Jarvis_Refractory_Raw.csv`).

### 5. NOMAD Repository Advanced Material Data Aggregator

This component interfaces with the NOMAD Laboratory infrastructure utilizing the server-side NOMAD REST API (v1) specification. It executes structural and thermodynamic queries to isolate low-bandgap bulk metallic systems containing target transition metals, traversing deep hierarchical archives via cursor-based pagination and extracting multi-property data frames.

### Key Capabilities

* **Multi-Criteria Archive Filtering:** Deploys nested payload queries restricting targets to specific chemistry subsets (containing `W`, `Mo`, `V`, `Cr`, `Ti`, `Nb`), bulk structural phases, narrow electronic bandwidth conditions ($\le$ 0.1 eV bandgap), targeted Bravais lattice settings (`cI`, `cF`, `hP`), and lower-bound mass densities ($\ge$ 5000 kg/m³).
* **Cursor-Driven Pagination (`search_after`):** Bypasses standard offset pagination memory limitations by capturing the final tracking key (`entry_id`) of each response page, establishing an efficient server-side cursor until target entry boundaries match local counts.
* **Hierarchical Metadata Extraction:** Navigates multi-tiered JSON response payload topologies to unify localized material properties (symmetry spacegroups, crystal networks, and volumetric metrics) with underlying mechanical data structures.
* **Thermodynamic & Phonon Property Retrieval:** Targets specialized computational properties embedded across advanced calculation workflows, parsing data points for thermodynamic phase stability (`is_stable`), convex hull energy limits (`energy_hulll`), and Debye model temperature/thermal performance vectors.

### 6. Mat-Web Data Extraction

The source code and repository for accessing real-world material data can be found here:
[Mat-Web-Data-Extraction on GitHub](https://github.com/RasmusTr/Mat-Web-Data-Extraction-)

## 👨‍🔬 Author

Rasmus Trommer
B.Sc. Materials Science Student
