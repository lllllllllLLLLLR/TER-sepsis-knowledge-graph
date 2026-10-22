# Sepsis Knowledge Graph & Evidence Chain Analysis

Research project at Université Paris-Saclay: build a **knowledge graph of sepsis literature** by extracting logic/evidence chains from research papers using LLMs, then exploring them as an interactive evidence network.

## Highlights

- **LLM-based paper analysis pipeline** — prompts Gemma / OpenRouter-backed LLMs to extract structured claims (population, severity, type) and evidence chains from sepsis papers.
- **Data cleaning & structured extraction** — notebook-driven pipeline (`2.2_Data` → `2.10_Data_Processing`) that turns raw PDF text into cleaned, section-split records.
- **Knowledge graph artifacts** — `sepsis_knowledge_graph.ttl` (Turtle) plus interactive HTML visualizations (`sepsis_logic_network.html`, `sepsis_semantic_network.html`, `sepsis_clustered_graph.html`).
- **Clinical diagnosis demo (`app.py`)** — end-to-end flow: extract biomarker query parameters from a clinical case → query an external evidence hub → generate a final clinical assessment with RAG-style retrieval.

## Quick start

```bash
# 1. create environment (Python 3.10+)
conda create -n sepsis-ter python=3.10
conda activate sepsis-ter

# 2. install dependencies
pip install -r requirements.txt

# 3. run the notebooks (jupyter) in order
jupyter notebook
# 2.2_Data.ipynb → 2.10_Data_Processing.ipynb → OpenRouter.ipynb → 3.15.ipynb

# 4. try the clinical diagnosis demo
python app.py
```

> Note: `app.py` and the OpenRouter notebooks need API keys (`config.py` / environment variables) — see the notebooks for expected config.

## Repository layout

```
├── 2.2_Data.ipynb                    # per-paper logic chain extraction
├── 2.10_Data_Processing.ipynb        # data cleaning + prompt design (Gemma)
├── OpenRouter.ipynb                  # sepsis paper analysis pipeline (OpenRouter)
├── OpenRouter_Data Collection.ipynb  # data collection via OpenRouter
├── 3.15.ipynb                        # evidence chain construction
├── 3.22_improvement_on_automation.ipynb
├── app.py                            # clinical diagnosis demo (biomarker → evidence → report)
├── batch_processor.py                # PDF text extraction & cleaning (PyMuPDF)
├── sepsis_dataset.json               # processed dataset
├── sepsis_knowledge_graph.ttl        # knowledge graph (Turtle)
└── *.html                            # interactive visualizations
```

## Dependencies

See `requirements.txt`. Key libraries: `google-genai`, `openai` (OpenRouter), `pydantic`, `requests`, `PyMuPDF`.

## Notes

- Raw PDF collections, datasets and API secrets are **not** included in this repo (see `.gitignore`).
- Research output of the M1 TER (Travail d'Étude et de Recherche), 2025–2026.
