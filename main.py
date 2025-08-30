from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging, base64, requests, httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)


# ---------------- SPECIAL SKILLS ---------------- #
def get_latest_news(api_key: str):
    if not api_key:
        return "❗ No NewsAPI key provided in Config."
    url = f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={api_key}"
    try:
        res = requests.get(url, timeout=8).json()
        arts = res.get("articles", [])[:5]
        if not arts:
            return "⚠️ No tech headlines returned."
        headlines = [a.get("title", "Untitled") for a in arts]
        return "📰 Tech Headlines:\n" + "\n".join(f"- {h}" for h in headlines)
    except Exception as e:
        return f"⚠️ News API error: {e}"


def get_weather(api_key: str, city: str = "Lucknow"):
    if not api_key:
        return "❗ No OpenWeather key provided in Config."
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        res = requests.get(url, timeout=8).json()
        if res.get("main"):
            temp = res["main"]["temp"]
            cond = res["weather"][0]["description"]
            return f"☁️ Weather in {city}: {temp}°C — {cond}"
        return f"❌ Could not fetch weather for {city}."
    except Exception as e:
        return f"⚠️ Weather API error: {e}"


# ---------------- ROUTES ---------------- #
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    logging.info("WebSocket client connected")

    conn_keys = {"assembly": "", "gemini": "", "news": "", "weather": "", "murf": ""}

    try:
        while True:
            msg = await ws.receive_json()

            if msg.get("type") == "config":
                for k in conn_keys:
                    if k in msg["keys"]:
                        conn_keys[k] = msg["keys"][k]
                await ws.send_json({"type": "system", "text": "✅ Config saved."})

            elif msg.get("type") == "skill":
                if msg["name"] == "news":
                    resp = get_latest_news(conn_keys["news"])
                    await ws.send_json({"type": "assistant", "text": resp})
                elif msg["name"] == "weather":
                    resp = get_weather(conn_keys["weather"], "Lucknow")
                    await ws.send_json({"type": "assistant", "text": resp})

            elif msg.get("type") == "final":  # user text
                user_text = msg["text"]

                # Gemini LLM response
                async with httpx.AsyncClient(timeout=20) as client:
                    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                    r = await client.post(
                        gemini_url,
                        params={"key": conn_keys["gemini"]},
                        json={"contents": [{"parts": [{"text": user_text}]}]},
                    )
                    resp = r.json()
                try:
                    reply = resp["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as e:
                    reply = f"⚠️ Gemini response error: {e}"

                await ws.send_json({"type": "assistant", "text": reply})

                # Murf TTS
                if conn_keys["murf"]:
                    try:
                        tts_url = "https://api.murf.ai/v1/speech/generate"
                        async with httpx.AsyncClient(timeout=30) as client:
                            r = await client.post(
                                tts_url,
                                headers={
                                    "api-key": conn_keys["murf"],  # ✅ correct header
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "voiceId": "en-US-michelle",  # ✅ voice
                                    "text": reply,
                                    "format": "MP3",
                                },
                            )
                        if r.status_code == 200:
                            resp_json = r.json()
                            audio_url = resp_json.get("audioFile")
                            if audio_url:
                                await ws.send_json({"type": "audio", "url": audio_url})
                        else:
                            logging.error(f"Murf error {r.status_code}: {r.text}")
                    except Exception as e:
                        logging.error(f"TTS error: {e}")

    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        await ws.close()
