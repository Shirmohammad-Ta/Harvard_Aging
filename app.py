import streamlit as st
import pandas as pd
import json
import requests
import time

# Page configuration
st.set_page_config(
    page_title="🧬 Aging Gene Annotation Tool",
    page_icon="🧬",
    layout="wide"
)

# Main title
st.title("🧬 Aging Gene Annotation Tool")
st.markdown("""
**📊 Based on real data from GenAge and trusted APIs**
- **Primary Source**: GenAge (Aging Gene Database)
- **Supporting APIs**: Ensembl, MyGene.info, NCBI
""")

# Load real data
@st.cache_data
def load_real_data():
    try:
        with open('data/real_aging_genes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ File data/real_aging_genes.json not found! Please run create_real_json.py first.")
        return {"total_genes": 0, "aging_genes": []}

real_data = load_real_data()

# Display statistics
if real_data["total_genes"] > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Genes", real_data["total_genes"])
    with col2:
        st.metric("📅 Last Updated", real_data["last_updated"])
    with col3:
        st.metric("📂 Data Source", real_data["source"].split()[0])

# Function to get live information from MyGene.info
def get_live_gene_info(symbol):
    """Retrieve live information from MyGene.info for a specific gene"""
    try:
        url = f"http://mygene.info/v3/query?q={symbol}&species=human&fields=all"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("hits"):
                hit = data["hits"][0]
                # Extract genomic position if available
                genomic_pos = hit.get("genomic_pos", {})
                return {
                    "symbol": hit.get("symbol"),
                    "name": hit.get("name"),
                    "summary": hit.get("summary", ""),
                    "entrez": hit.get("entrez"),
                    "ensembl": hit.get("ensembl", {}).get("gene"),
                    "chromosome": genomic_pos.get("chr"),
                    "start": genomic_pos.get("start"),
                    "end": genomic_pos.get("end")
                }
    except Exception as e:
        st.warning(f"⚠️ Error retrieving live information: {e}")
    return None

# Function to get information from Ensembl
def get_live_ensembl_info(symbol):
    """Retrieve live information from Ensembl API with better error handling"""
    try:
        # Search for Ensembl ID with increased timeout
        search_url = f"https://rest.ensembl.org/xrefs/symbol/human/{symbol}?content-type=application/json"
        response = requests.get(search_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                ensembl_id = data[0].get("id")
                if ensembl_id:
                    lookup_url = f"https://rest.ensembl.org/lookup/id/{ensembl_id}?content-type=application/json"
                    lookup_response = requests.get(lookup_url, timeout=30)
                    if lookup_response.status_code == 200:
                        return lookup_response.json()
                    else:
                        st.warning(f"⚠️ Ensembl lookup failed with status: {lookup_response.status_code}")
                else:
                    st.warning("⚠️ No Ensembl ID found for this gene")
            else:
                st.warning("⚠️ No data returned from Ensembl search")
        else:
            st.warning(f"⚠️ Ensembl search failed with status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        st.warning("⏰ Ensembl API timeout (server busy). Please try again later.")
    except requests.exceptions.ConnectionError:
        st.warning("🔌 Connection error to Ensembl. Please check your internet.")
    except Exception as e:
        st.warning(f"⚠️ Error retrieving Ensembl information: {str(e)[:100]}...")
    
    return None

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Search Gene",
    "📋 Full Gene List",
    "📊 Statistics & Analysis",
    "ℹ️ Information"
])

# ============ Tab 1: Gene Search ============
with tab1:
    st.subheader("🔍 Search for a Gene in GenAge Data")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "Enter gene symbol (e.g., FOXO3, TP53, SIRT1)",
            placeholder="Example: TP53"
        )
    with col2:
        st.write("")
        st.write("")
        live_search = st.checkbox("🌐 Fetch live data from API", value=True)
    
    if search_term:
        # Case-insensitive search
        search_upper = search_term.upper().strip()
        
        # Search in real data (case-insensitive)
        results = [g for g in real_data["aging_genes"] if search_upper == g["symbol"].upper()]
        
        # If no exact match, try partial match
        if not results:
            results = [g for g in real_data["aging_genes"] if search_upper in g["symbol"].upper()]
        
        if results:
            gene = results[0]
            st.success(f"✅ Gene **{gene['symbol']}** found in GenAge!")
            
            # Basic information
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🧬 Basic Information")
                base_info = {
                    "Symbol": gene["symbol"],
                    "Full Name": gene.get("name", "Unknown"),
                    "GenAge ID": gene.get("genage_id", "Unknown"),
                    "Ensembl ID": gene.get("ensembl_id", "Unknown"),
                    "NCBI ID": gene.get("entrez_id", "Unknown"),
                    "Chromosome": gene.get("chromosome", "Unknown"),
                    "Location": f"{gene.get('start', '')} - {gene.get('end', '')}" if gene.get('start') else "Unknown",
                    "Reason in GenAge": gene.get("why", "Unknown")
                }
                st.json(base_info)
            
            with col2:
                st.subheader("📝 Description")
                if gene.get("summary"):
                    st.info(gene["summary"])
                elif gene.get("description"):
                    st.info(gene["description"])
                else:
                    st.warning("No description available for this gene")
            
            # Live information from APIs
            if live_search:
                st.subheader("🌐 Live Data from APIs")
                with st.spinner("Fetching live information..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🔬 MyGene.info**")
                        live_data = get_live_gene_info(gene["symbol"])
                        if live_data:
                            st.json({
                                "symbol": live_data.get("symbol"),
                                "name": live_data.get("name"),
                                "summary": live_data.get("summary", "")[:200] + "..." if live_data.get("summary") else "",
                                "entrez": live_data.get("entrez"),
                                "ensembl": live_data.get("ensembl"),
                                "chromosome": live_data.get("chromosome"),
                                "start": live_data.get("start"),
                                "end": live_data.get("end")
                            })
                        else:
                            st.warning("Live information not available")
                    
                    with col2:
                        st.markdown("**🧬 Ensembl**")
                        # First show cached data
                        if gene.get("ensembl_id"):
                            st.info(f"**Cached Ensembl ID:** {gene['ensembl_id']}")
                            st.info(f"**Chromosome:** {gene.get('chromosome', 'Unknown')}")
                            st.info(f"**Location:** {gene.get('start', '')} - {gene.get('end', '')}")
                        else:
                            st.warning("No cached Ensembl data")
                        
                        # Then try live data
                        ensembl_data = get_live_ensembl_info(gene["symbol"])
                        if ensembl_data:
                            st.success("✅ Live data received!")
                            st.json({
                                "id": ensembl_data.get("id"),
                                "chromosome": ensembl_data.get("seq_region_name"),
                                "start": ensembl_data.get("start"),
                                "end": ensembl_data.get("end"),
                                "biotype": ensembl_data.get("biotype")
                            })
        else:
            st.error(f"❌ Gene '{search_term}' not found in GenAge data")
            
            # Show suggestions with case-insensitive matching
            suggestions = [g["symbol"] for g in real_data["aging_genes"] 
                          if search_upper in g["symbol"].upper() and search_upper != g["symbol"].upper()]
            if suggestions:
                st.info(f"💡 Did you mean: {', '.join(suggestions[:5])}?")
            else:
                # Show a few random genes as examples
                sample_genes = [g["symbol"] for g in real_data["aging_genes"][:10]]
                st.info(f"💡 Sample genes in database: {', '.join(sample_genes)}")

# ============ Tab 2: Full Gene List ============
with tab2:
    st.subheader("📋 Complete List of Aging Genes from GenAge")
    
    if real_data["total_genes"] > 0:
        # Convert to DataFrame
        df = pd.DataFrame(real_data["aging_genes"])
        
        # Select and configure columns
        display_columns = ["symbol", "name", "chromosome", "start", "end", "why"]
        available_columns = [col for col in display_columns if col in df.columns]
        display_df = df[available_columns].copy()
        display_df.columns = ["Symbol", "Name", "Chromosome", "Start", "End", "Reason"]
        
        # Display table
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            chromosomes = df["chromosome"].dropna().value_counts()
            st.bar_chart(chromosomes.head(10))
        
        # Download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download list as CSV",
            data=csv,
            file_name="aging_genes_from_genage.csv",
            mime="text/csv"
        )

# ============ Tab 3: Statistics & Analysis ============
with tab3:
    st.subheader("📊 Aging Gene Statistics & Analysis")
    
    if real_data["total_genes"] > 0:
        df = pd.DataFrame(real_data["aging_genes"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🧬 Total Genes", len(df))
            st.metric("🧭 Genes with Chromosome", df["chromosome"].notna().sum())
        
        with col2:
            st.metric("📝 Genes with Descriptions", df["summary"].notna().sum())
            st.metric("🏷️ Genes with Reason", df["why"].notna().sum())
        
        # Chromosome distribution
        st.subheader("🧬 Gene Distribution by Chromosome")
        chrom_counts = df["chromosome"].value_counts().head(15)
        st.bar_chart(chrom_counts)
        
        # Distribution table
        st.subheader("📋 Complete Chromosome Distribution")
        chrom_df = pd.DataFrame({
            "Chromosome": chrom_counts.index,
            "Gene Count": chrom_counts.values
        })
        st.dataframe(chrom_df, use_container_width=True)

# ============ Tab 4: Information ============
with tab4:
    st.subheader("ℹ️ Project Information")
    
    st.markdown("""
    ### 🎯 Objective
    This tool provides an integrated database of aging-related genes compiled from trusted sources.
    
    ### 📂 Data Sources
    
    | Source | Data Type | Documentation |
    |--------|-----------|---------------|
    | **GenAge** | Primary aging gene database | [genomics.senescence.info](https://genomics.senescence.info/genes/human.html) |
    | **Ensembl REST API** | Chromosomal information | [rest.ensembl.org](https://rest.ensembl.org) |
    | **MyGene.info API** | Integrated gene information | [mygene.info](https://mygene.info) |
    | **NCBI E-utilities** | Disease information | [ncbi.nlm.nih.gov](https://www.ncbi.nlm.nih.gov) |
    
    ### 📊 Current Statistics
    - **Total Genes**: {total}
    - **Last Updated**: {date}
    - **Data Source**: {source}
    
    ### 🛠️ How to Use
    1. In the **Search Gene** tab, enter the desired gene symbol
    2. Enable **Fetch live data from API** to see real-time information
    3. In the **Full Gene List** tab, view and download all genes
    4. In the **Statistics** tab, explore chromosome distribution
    
    ### 📝 Sample Genes for Testing
    - `TP53` - Tumor suppressor gene
    - `FOXO3` - Longevity-related gene
    - `SIRT1` - Aging-related gene
    - `BRCA1` - Breast cancer gene
    - `ATM` - DNA repair gene
    """.format(
        total=real_data["total_genes"] if real_data["total_genes"] > 0 else "Unknown",
        date=real_data.get("last_updated", "Unknown"),
        source=real_data.get("source", "Unknown")
    ))

# Footer
st.markdown("---")
st.caption("🧬 Aging Gene Annotation Tool | Supported by: GenAge, Ensembl, MyGene.info, NCBI")