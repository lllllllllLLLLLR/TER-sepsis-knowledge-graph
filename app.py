import os
import json
import urllib.parse
import requests
from typing import List, Optional, Dict
from pydantic import BaseModel
from google import genai
from google.genai import types

# ==========================================
# Module 1: Data Models for Structure Definition
# ==========================================
class ApiQueryParameters(BaseModel):
    name: str
    population: Optional[str] = None
    severity: Optional[str] = None
    type: Optional[str] = None

class ApiQueries(BaseModel):
    queries: List[ApiQueryParameters]

# ==========================================
# Module 2: Automated API URL Generation
# ==========================================
def get_extraction_instructions() -> str:
    return """
    You are an expert clinical data extraction assistant.
    Extract the required biomarkers from the clinical case to build query parameters based on the system rules.

    Rules:
    1. name: Extract all laboratory indicators and biomarkers mentioned.
    2. population: Infer from patient age. Allowed values: adult, children, neonatal.
    3. severity: Infer from clinical description. Allowed values: SIRS, sepsis, severe, shock, syndrome. Leave null if unsure.
    4. type: Infer if it is for diagnosis or prognosis. Initial cases are usually diagnosis. Leave null if unsure.
    """

def extract_parameters(client: genai.Client, clinical_case: str) -> ApiQueries:
    prompt = f"Analyze the following clinical case and extract the search parameters:\n\n{clinical_case}"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[get_extraction_instructions(), prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ApiQueries,
            temperature=0.0
        )
    )
    
    try:
        parsed_data = json.loads(response.text)
        return ApiQueries(**parsed_data)
    except Exception as e:
        print(f"Error parsing model extraction response: {e}")
        return ApiQueries(queries=[])

def build_urls(api_queries: ApiQueries) -> Dict[str, dict]:
    
    url_data = {}
    for query in api_queries.queries:
        if not query.name:
            continue
            
        params = {'name': query.name}
        if query.population:
            params['population'] = query.population
        if query.severity:
            params['severity'] = query.severity
        if query.type:
            params['type'] = query.type
            
        url_data[query.name] = params
        
    return url_data

# ==========================================
# Module 3: Data Visualization
# ==========================================
def print_terminal_table(biomarker: str, records: list):
    if not records or not isinstance(records, list) or len(records) == 0:
        return

    print(f"\n[Evidence Verification] Real-world Data: {biomarker} - Top {len(records)} records")

    print("-" * 105)
    header = f"{'ID':<6} | {'Year':<6} | {'Region':<10} | {'Cut-off':<15} | {'AUC':<6} | {'Sens/Spec':<11} | {'Trend':<6}"
    print(header)
    print("-" * 105)

    for r in records:
        r_id = str(r.get('ID', 'N/A'))[:6]
        year = str(r.get('Published_year', 'N/A'))[:6]
        region = str(r.get('Region', 'N/A'))[:10]
        cutoff = str(r.get('Cut_off_Value', 'N/A'))[:15]
        auc = str(r.get('AUC', 'N/A'))[:6]

        sens = str(r.get('Sensitivity', 'N/A'))
        spec = str(r.get('Specificity', 'N/A'))
        sens_spec = f"{sens}/{spec}"[:11]

        trend = str(r.get('Abundance_Change', 'N/A'))[:6]

        row = f"{r_id:<6} | {year:<6} | {region:<10} | {cutoff:<15} | {auc:<6} | {sens_spec:<11} | {trend:<6}"
        print(row)
    print("-" * 105)

    print("  Detailed Information:")
    for r in records:
        r_id = str(r.get('ID', 'N/A'))
        samples = str(r.get('Samples_information', 'N/A')).replace('\n', ' ')
        summary = str(r.get('Summary', 'N/A')).replace('\n', ' ')

        if len(samples) > 90:
            samples = samples[:87] + "..."
        if len(summary) > 90:
            summary = summary[:87] + "..."

        print(f"    - [{r_id}] Samples: {samples}")
        print(f"             Summary: {summary}")
    print("\n")

# ==========================================
# Module 4: Clinical Diagnosis Agent
# ==========================================
def fetch_database_records(url_params_dict: Dict[str, dict]) -> str:
    base_url = "http://sysbio.org.cn/SBD/api.php"
    reference_data = ""
    
    for biomarker, original_params in url_params_dict.items():
        #  URL
        full_query_string = urllib.parse.urlencode(original_params, quote_via=urllib.parse.quote)
        full_url = f"{base_url}?{full_query_string}"
        
        print(f"-> Trying full query for [{biomarker}]: {full_url}")
        
        success = False
        try:
            response = requests.get(full_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", []) if isinstance(data, dict) else data
                if not results:
                    results = data
                
                # URL result
                if results and len(results) > 0:
                    records_to_show = results[:5] # 提取前两条
                    reference_data += f"\n--- {biomarker} Database Records (Full Match) ---\n"
                    reference_data += json.dumps(records_to_show, indent=2, ensure_ascii=False)
                    success = True
                    print(f"   [SUCCESS] Data found for {biomarker}.")
                    
                    # 【核心修复点 1】：调用表格渲染函数在终端打印
                    print_terminal_table(biomarker, records_to_show)
                    
        except Exception as e:
            print(f"   [ERROR] Connection failed: {e}")

        # modification
        if not success:
            print(f"   [FALLBACK] No data found with strict parameters. Trying minimum requirements (name + population)...")
            
            fallback_params = {'name': original_params['name']}
            if 'population' in original_params:
                fallback_params['population'] = original_params['population']
                
            fallback_query_string = urllib.parse.urlencode(fallback_params, quote_via=urllib.parse.quote)
            fallback_url = f"{base_url}?{fallback_query_string}"
            
            print(f"-> Trying fallback query for [{biomarker}]: {fallback_url}")
            
            try:
                fallback_response = requests.get(fallback_url, timeout=10)
                if fallback_response.status_code == 200:
                    fallback_data = fallback_response.json()
                    fallback_results = fallback_data.get("results", []) if isinstance(fallback_data, dict) else fallback_data
                    if not fallback_results:
                        fallback_results = fallback_data
                    
                    if fallback_results and len(fallback_results) > 0:
                        records_to_show = fallback_results[:5] # 提取前两条
                        reference_data += f"\n--- {biomarker} Database Records (Fallback Match) ---\n"
                        reference_data += json.dumps(records_to_show, indent=2, ensure_ascii=False)
                        print(f"   [SUCCESS] Fallback data found for {biomarker}.")
                        
                        # 【核心修复点 2】：在降级查询成功时，也调用表格渲染函数
                        print_terminal_table(biomarker, records_to_show)
                        
                    else:
                        print(f"   [FAILED] Still no data found even with fallback parameters.")
                else:
                    print(f"   [FAILED] Fallback HTTP Status: {fallback_response.status_code}")
            except Exception as e:
                print(f"   [ERROR] Fallback connection failed: {e}")

    return reference_data

def generate_final_diagnosis(client: genai.Client, clinical_case: str, reference_data: str) -> str:
    prompt = f"""You are an expert clinical AI assistant.

    Here is some reference data retrieved automatically from a professional biomarker database regarding diagnostic standards:
    <reference_data>
    {reference_data}
    </reference_data>

    Based ON THE REFERENCE DATA ABOVE and your medical knowledge, please analyze the following clinical case:

    <clinical_case>
    {clinical_case}
    </clinical_case>

    Task:
    1. Compare the patient biomarker values with the cut-off values in the reference data.
    2. Can this patient be diagnosed with sepsis?
    3. Please provide the percentage of possibility that this patient is diagnosed with sepsis.
    4. What is the best treatment plan?
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2
        )
    )
    return response.text

# ==========================================
# Module 5: Interactive Terminal Interface
# ==========================================
def run_diagnostic_pipeline():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Fatal Error: Please set the GOOGLE_API_KEY environment variable before running.")
        return

    client = genai.Client(api_key=api_key)
    
    print("==================================================")
    print("Automated Sepsis Diagnostic Pipeline")
    print("Type QUIT to exit the application.")
    print("==================================================")
    
    while True:
        print("\nPlease enter the clinical case details:")
        
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
                
            if line.strip().upper() == "QUIT":
                print("Exiting application safely.")
                return
                
            if line.strip() == "</clinical_case>":
                lines.append(line)
                break
                
            if not line.strip() and len(lines) > 0 and not lines[0].startswith("<clinical_case>"):
                break
                
            lines.append(line)
            
        case_text = "\n".join(lines)
        if not case_text.strip():
            continue
            
        print("\n[Phase 1] Analyzing case and extracting parameters...")
        queries = extract_parameters(client, case_text)
        url_params_dict = build_urls(queries)
        
        if not url_params_dict:
            print("Warning: No relevant biomarkers found to query.")
            continue
            
        print("\n[Phase 2] Retrieving evidence from external knowledge hub (with auto-fallback)...")
        fetched_evidence = fetch_database_records(url_params_dict)
        
        if not fetched_evidence.strip():
            print("\nWarning: Retrieved data is empty. Relying solely on internal model weights.")
        else:
            print("\nSuccessfully retrieved reference data.")

        print("\n[Phase 3] Generating final clinical assessment...")
        final_report = generate_final_diagnosis(client, case_text, fetched_evidence)
        
        print("\n================ DIAGNOSTIC REPORT ================\n")
        print(final_report)
        print("\n===================================================\n")

if __name__ == "__main__":
    run_diagnostic_pipeline()