# DataBuff

A modern, AI-powered, interactive data preprocessing and visualization web app built with Flask, React, Google Cloud, and OpenRouter AI. Created for the Big Data Architecture course at University of Colorado Boulder.

⸻

## 🚀 Features

- 🔐 **Authentication** (email + Google OAuth)
- 📁 **Upload/Replace** tabular datasets (CSV, TSV)
- 💬 **Chat-based AI Assistant** (BuffBot)
- 🔄 **Natural language to pandas** code conversion
- 🧪 **Execute AI-generated code** with editable Python code cell
- 📊 **Live preview** of dataset (MUI DataGrid)
- 📉 **AI-generated visualizations** (matplotlib)
- 🧠 **Captioning for plots** using LLMs
- ✅ **Secure cloud storage** (GCS) + metadata (Firestore)

⸻

## 🏗️ Tech Stack

### Frontend
- ⚛️ React + TypeScript
- 💅 Material-UI (MUI)
- 🎨 Framer Motion
- ✨ Monaco Editor (Python cell)

### Backend
- 🐍 Flask (REST API)
- 🧠 OpenRouter (Claude/Mixtral/Quasar-Alpha)
- ☁️ Google Cloud Storage & Firestore
- 🔐 JWT-based Auth
- 📈 matplotlib + pandas

⸻

## 🛠️ Setup Instructions

### 🔧 Prerequisites
- Node.js + npm
- Python 3.10+
- GCP project with Firestore & Cloud Storage enabled
- OpenRouter API key

### ⚙️ Backend Setup

```bash
cd Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Place your gcp-key.json in Backend/
# Add .env file with:
# SECRET_KEY=...
# OPENROUTER_API_KEY=...

python app.py
```

### 🌐 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Access at: `http://localhost:5173`

⸻

## ☁️ GKE Deployment

1. Dockerize frontend & backend
2. Push to GCR
3. Create K8s manifests for both
4. Setup GKE cluster
5. Deploy with `kubectl apply -f ...`
6. Access app via external LoadBalancer IP

⸻

## 🧠 Credits

**Built by:**
- Abdul Rafay Ahmed Khan
- Samiksha Patil
- Harsh Chaudhari
- Mohit Gupta

⸻

## 📜 License

MIT License

