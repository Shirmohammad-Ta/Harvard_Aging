import pandas as pd
import requests
import json
import time

def get_ensembl_info(symbol):
    """Retrieve chromosomal information from Ensembl API with extended timeout"""
    try:
        # Search for Ensembl ID
        search_url = f"https://rest.ensembl.org/xrefs/symbol/human/{symbol}?content-type=application/json"
        response = requests.get(search_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                ensembl_id = data[0].get("id")
                if ensembl_id:
                    # Retrieve full information
                    lookup_url = f"https://rest.ensembl.org/lookup/id/{ensembl_id}?content-type=application/json"
                    lookup_response = requests.get(lookup_url, timeout=30)
                    if lookup_response.status_code == 200:
                        lookup_data = lookup_response.json()
                        return {
                            "ensembl_id": ensembl_id,
                            "chromosome": lookup_data.get("seq_region_name", ""),
                            "start": str(lookup_data.get("start", "")),
                            "end": str(lookup_data.get("end", "")),
                            "description": lookup_data.get("description", "")
                        }
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout for gene {symbol} (continuing...)")
    except Exception as e:
        print(f"⚠️ Error for {symbol}: {e}")
    return {
        "ensembl_id": None,
        "chromosome": None,
        "start": None,
        "end": None,
        "description": None
    }

def get_mygene_info(symbol):
    """Retrieve information from MyGene.info"""
    try:
        url = f"http://mygene.info/v3/query?q={symbol}&species=human&fields=all"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("hits"):
                hit = data["hits"][0]
                return {
                    "summary": hit.get("summary", ""),
                    "name": hit.get("name", ""),
                    "ncbi_id": str(hit.get("entrez", ""))
                }
    except Exception as e:
        print(f"⚠️ MyGene.info error for {symbol}: {e}")
    return {
        "summary": None,
        "name": None,
        "ncbi_id": None
    }

# Read CSV file
df = pd.read_csv('genage_human.csv')
print(f"✅ CSV file loaded with {len(df)} rows!")

# Filtering
df = df.dropna(subset=['symbol'])
df = df[df['symbol'].str.strip() != '']
print(f"✅ {len(df)} valid genes remain")

# Build gene list - ALL 307 GENES
aging_genes = []
limit = 307  # 🔥 ALL GENES - changed from 20 to 307

for idx, row in df.head(limit).iterrows():
    symbol = str(row['symbol']).strip()
    entrez_id = str(row['entrez gene id']).strip() if pd.notna(row['entrez gene id']) else None
    genage_id = str(row['GenAge ID']).strip()
    name = str(row['name']).strip() if pd.notna(row['name']) else None
    why = str(row['why']).strip() if pd.notna(row['why']) else None
    
    print(f"📊 Retrieving information for gene {symbol}...")
    
    # Information from Ensembl
    ensembl_info = get_ensembl_info(symbol)
    
    # Information from MyGene.info
    mygene_info = get_mygene_info(symbol)
    
    # Final information
    gene_info = {
        "symbol": symbol,
        "genage_id": genage_id,
        "name": name,
        "entrez_id": entrez_id or mygene_info.get("ncbi_id"),
        "ensembl_id": ensembl_info.get("ensembl_id"),
        "chromosome": ensembl_info.get("chromosome"),
        "start": ensembl_info.get("start"),
        "end": ensembl_info.get("end"),
        "description": ensembl_info.get("description"),
        "summary": mygene_info.get("summary"),
        "why": why
    }
    
    aging_genes.append(gene_info)
    
    # Increased delay between requests
    time.sleep(1)  # increased to 1 second

# Build final JSON file
final_json = {
    "source": "GenAge (genage_human.csv)",
    "total_genes": len(aging_genes),
    "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    "aging_genes": aging_genes
}

# Save file
import os
if not os.path.exists('data'):
    os.makedirs('data')

with open('data/real_aging_genes.json', 'w', encoding='utf-8') as f:
    json.dump(final_json, f, indent=4, ensure_ascii=False)

print(f"\n✅ JSON file created with {len(aging_genes)} real genes!")
print(f"📁 Path: data/real_aging_genes.json")