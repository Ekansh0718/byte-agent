# 🎙️ Byte – AI Voice Agent  

Byte is an **AI-powered conversational voice agent** that lets you chat via **text or voice**.  
It supports **speech-to-text (STT)**, **LLM-powered responses**, and **text-to-speech (TTS)**, giving you a seamless chat experience like WhatsApp/iMessage but with AI.  

---

## 🚀 Features
- 💬 **Conversational Chat** – Type or speak to Byte and get instant responses.
- 🎤 **Voice Input** – Record your voice and send it directly.
- 🔊 **Voice Output** – AI replies back in natural speech using Murf TTS.
- 📰 **Tech News Skill** – Get the latest technology headlines.
- ☁️ **Weather Report Skill** – Check live weather for your city.
- 🖼️ **Modern UI** – Clean Apple-inspired chat interface with animations.
- 🔑 **Configurable API Keys** – Easily add your own API keys in the UI.

---

## 🛠️ Tech Stack
- **Frontend:** HTML, CSS, JavaScript (WebSocket, MediaRecorder API)
- **Backend:** FastAPI (Python)
- **APIs Used:**
  - [Google Gemini](https://ai.google.dev/) – LLM Responses  
  - [AssemblyAI](https://www.assemblyai.com/) – Speech-to-Text  
  - [Murf](https://murf.ai/) – Text-to-Speech  
  - [NewsAPI](https://newsapi.org/) – Tech Headlines  
  - [OpenWeather](https://openweathermap.org/) – Weather Data  

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repo
```bash
git clone https://github.com/<your-username>/byte-agent.git
cd byte-agent


2️⃣ Create virtual environment
  python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3️⃣ Install dependencies
  pip install -r requirements.txt

4️⃣ Run the server
  uvicorn main:app --reload

🔑 API Keys Required

  You need to generate and add these API keys in the Config section of UI:
  
  Google Gemini API Key
  
  AssemblyAI API Key
  
  Murf TTS API Key
  
  NewsAPI Key
  
  OpenWeather Key
