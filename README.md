<div align="center">

<br/>

```
██╗     ██╗████████╗███████╗██╗      ██████╗ ██╗    ██╗
██║     ██║╚══██╔══╝██╔════╝██║     ██╔═══██╗██║    ██║
██║     ██║   ██║   █████╗  ██║     ██║   ██║██║ █╗ ██║
██║     ██║   ██║   ██╔══╝  ██║     ██║   ██║██║███╗██║
███████╗██║   ██║   ██║     ███████╗╚██████╔╝╚███╔███╔╝
╚══════╝╚═╝   ╚═╝   ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝
```

### Research Reading & Insight Management System

<br/>

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/SQLite-Persistent-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Plotly](https://img.shields.io/badge/Plotly-Analytics-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](LICENSE)

<br/>

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

<br/>

---

</div>

## What is LitFlow?

**LitFlow** transforms the way researchers engage with academic literature. Instead of passive reading, every paper becomes a **structured analytical record** — encoding aims, methods, techniques, findings, and personal insights into a searchable, visual knowledge base.

Built for PhD students, researchers, and academics who want to read with **depth**, write with **evidence**, and think with **clarity**.

---

## Modules

<div align="center">

| Module | Description |
|:---:|:---|
| 🏠 **Dashboard** | KPI metrics, 7 interactive charts — status, methodology, year, techniques, tags, cumulative progress, weekly cadence |
| ➕ **Add Paper** | Structured entry form with 14 analytical fields — from aim and RQs to insights and reflection |
| 📖 **Paper Library** | Full-text search, filter by status, sort, edit inline, delete with confirmation |
| 🔍 **Insight Explorer** | Multi-filter discovery — methodology × technique × tag × year × status |
| 📝 **Weekly Diary** | Auto-populated from logged papers — themes, ideas, challenges, next steps |
| 🧩 **Argument Builder** | Select 2–6 papers → synthesise common themes, agreements, tensions, and gaps |
| 📊 **Gap Analysis** | Methodology dominance, technique frequency, tag co-occurrence network, temporal coverage |
| 📤 **Export** | Full database + filtered subsets → `.xlsx` and `.csv` |

</div>

---

## Data Structure

Each paper is encoded as a **structured analytical record**:

```
Papers Table
├── Identity      → title, authors, year
├── Research      → aim, research questions, dataset used
├── Method        → methodology, analytical techniques
├── Output        → key findings, your insights, critical reflection
└── Metadata      → status, tags, date added

Weekly Diary Table
├── Auto-filled   → papers count, top tags, methods this week
└── Manual        → key themes, new ideas, challenges, next steps
```

---

## Innovative Features

### Auto Research Gap Hints
Frequency analysis across your entire library surfaces methodological dominance and underrepresented approaches — no NLP required.

### Argument Builder
Rule-based synthesis engine: select papers → get common themes, agreement pairs, methodological tensions, and a draft argument frame. Exportable as `.txt`.

### Insight Density Metric
`Insight Density = total insight characters ÷ completed papers`  
A proxy for analytical depth, tracked on the dashboard.

### Reading Streak Tracker
Consecutive weeks with logged papers — behavioural nudge to stay consistent.

### Tag Co-occurrence Network
Co-occurring tags reveal your thematic clusters (e.g., *XAI + Supply Chain* appearing 8×).

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/chaqBD/LitFlow.git
cd LitFlow

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

App opens at **http://localhost:8501**

---

## Deploy on Railway

LitFlow is Railway-ready out of the box.

### One-click deploy

1. Fork this repo
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select `LitFlow` → Railway detects `Procfile` + `requirements.txt` automatically
4. Click **Deploy**

### Persistent Database (Required)

SQLite data is stored on a Railway Volume — without it, data resets on redeploy.

```
Railway Dashboard → Your Service → Volumes → Add Volume
Mount path: /data
```

The app reads `RAILWAY_VOLUME_MOUNT_PATH` automatically. No extra env vars needed.

---

## Tech Stack

<div align="center">

| Layer | Technology |
|:---:|:---:|
| Frontend | Streamlit |
| Database | SQLite (via `sqlite3`) |
| Charts | Plotly Express |
| Data | Pandas |
| Export | OpenPyXL |
| Deployment | Railway |

</div>

---

## File Structure

```
LitFlow/
├── app.py                   ← Main app + sidebar navigation
├── database.py              ← All SQLite operations (CRUD)
├── requirements.txt
├── Procfile                 ← Railway start command
├── railway.json             ← Volume mount config
└── modules/
    ├── dashboard.py         ← KPI metrics + 7 charts
    ├── paper_entry.py       ← Add / edit paper form
    ├── paper_library.py     ← Browse, search, delete
    ├── insight_explorer.py  ← Multi-filter discovery
    ├── weekly_diary.py      ← Weekly reflection + history
    ├── argument_builder.py  ← Rule-based synthesis engine
    ├── gap_analysis.py      ← Methodology + tag gap analysis
    └── export_module.py     ← Excel + CSV export
```

---

## Export Outputs

| Output | Format |
|---|---|
| Full literature database | `.xlsx` (Papers + Summary sheets) |
| Filtered subset | `.xlsx` / `.csv` |
| Weekly diary history | `.xlsx` / `.csv` |
| Argument Builder report | `.txt` |

---

<div align="center">

Built by **Shakir** · Powered by Streamlit + SQLite · Deployed on Railway

</div>
