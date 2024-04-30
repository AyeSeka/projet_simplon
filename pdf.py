import pdfplumber
import pandas as pd

# Initialise une liste pour stocker les lignes du tableau
table_data = []

with pdfplumber.open("data/dataset_spm.pdf") as pdf:
    for page_number in range(len(pdf.pages)):
        page = pdf.pages[page_number]
        table = page.extract_table()
        if table:
            for row in table:
                table_data.append(row)

# Crée un DataFrame pandas à partir des données du tableau avec les noms de colonnes spécifiés
df = pd.DataFrame(table_data, columns=['id', 'Name', 'Gender', 'Produit', 'Type', 'Prix', 'Date'])

# Enregistre le DataFrame dans un fichier CSV
df.to_csv("spm.csv", index=False)
