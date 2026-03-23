# 📊 Materials Data Extraction with Jupyter Notebook

## 📖 Overview

This project contains a Jupyter Notebook-based workflow designed to extract materials data from multiple online materials science databases. The goal is to collect, unify, and prepare data for further analysis in the field of Materials Informatics.

The notebook demonstrates how to programmatically access, query, and process structured and semi-structured materials data from various sources.

---

## 🎯 Purpose

The main objectives of this project are:

* Automate the extraction of materials data
* Access multiple databases through APIs or web scraping
* Standardize heterogeneous data formats
* Prepare datasets for further analysis (e.g., machine learning, screening)

---

## 🧰 Technologies Used

* Python
* Jupyter Notebook
* Libraries:

  * pandas
  * requests
  * selenium

---

## 🌐 Data Sources

The following materials databases are accessed:

* JARVIS (Joint Automated Repository for Various Integrated Simulations)
* AFLOW (Automatic Flow for Materials Discovery)
* NOMAD (Novel Materials Discovery Laboratory)
* Materials Project
* MatWeb
* Open Materials Database (OMDB)

---

## ⚙️ Functionality

The notebook includes functionality to:

* Query APIs (where available)
* Extract structured data (e.g., JSON responses)
* Scrape tabular data from web pages (e.g., MatWeb)
* Clean and preprocess raw data
* Combine datasets from multiple sources

---

## 🧪 Example Use Cases

* Filtering materials by properties (e.g., band gap, density)
* Collecting datasets for machine learning models
* Comparing data across different databases
* Identifying candidate materials for specific applications

---

## 🚀 Getting Started

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

## ⚠️ Notes

* Some databases require API keys (e.g., Materials Project)
* Web scraping (e.g., MatWeb) may depend on website structure and can break if the site changes
* Please respect database usage policies and rate limits

---

## 📌 Future Improvements

* Add unified schema for all databases
* Improve error handling and logging
* Integrate additional materials databases
* Build automated pipelines for continuous data updates

---

## 👨‍🔬 Author

Rasmus Trommer
M.Sc. Materials Science Student
