from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, base64, json, logging, requests
import httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)

# ---------------- HELPERS ---------------- #
def get_latest_news(api_key: str):
    if not api_key:
        return "❗ No NewsAPI key provided."
    url = f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={api_key}"
    try:
        res = requests.get(url, timeout=8).json()
        arts = res.get("articles", [])[:5]
        if not arts:
            return "⚠️ No tech headlines."
        return "📰 Tech News:\n" + "\n".join(f"- {a['title']}" for a in arts if a.get("title"))
    except Exception as e:
        return f"⚠️ News API error: {e}"


def get_weather(api_key: str, city: str = "Lucknow"):
    if not api_key:
        return "❗ No Weather key provided."
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        res = requests.get(url, timeout=8).json()
        if res.get("main"):
            return f"☁️ {city}: {res['main']['temp']}°C, {res['weather'][0]['description']}"
        return f"❌ Could not fetch weather."
    except Exception as e:
        return f"⚠️ Weather API error: {e}"


# ---------------- ROUTES ---------------- #
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    logging.info("✅ WebSocket client connected")

    conn_keys = {"assembly": "", "gemini": "", "news": "", "weather": "", "murf": ""}

    try:
        while True:
            msg = await ws.receive_json()

            # 🔑 Save API Keys
            if msg.get("type") == "config":
                for k in conn_keys:
                    if k in msg["keys"]:
                        conn_keys[k] = msg["keys"][k]
                await ws.send_json({"type": "system", "text": "✅ Config saved."})

            # 📡 Special Skills
            elif msg.get("type") == "skill":
                if msg["name"] == "news":
                    await ws.send_json({"type": "assistant", "text": get_latest_news(conn_keys["news"])})
                elif msg["name"] == "weather":
                    await ws.send_json({"type": "assistant", "text": get_weather(conn_keys["weather"], "Lucknow")})

            # 📝 Text Input
            elif msg.get("type") == "final":
                user_text = msg["text"]
                await ws.send_json({"type": "user", "text": user_text})

                # Gemini Reply
                async with httpx.AsyncClient(timeout=20) as client:
                    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                    r = await client.post(
                        gemini_url,
                        params={"key": conn_keys["gemini"]},
                        json={"contents": [{"parts": [{"text": user_text}]}]},
                    )
                try:
                    reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                except Exception:
                    reply = "⚠️ Gemini response error."

                await ws.send_json({"type": "assistant", "text": reply})

                # Murf TTS
                if conn_keys["murf"]:
                    try:
                        async with httpx.AsyncClient(timeout=30) as client:
                            r = await client.post(
                                "https://api.murf.ai/v1/speech/generate",
                                headers={
                                    "api-key": conn_keys["murf"],  # ✅ Correct header
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "voiceId": "en-US-natalie",  # ✅ valid Murf voice
                                    "text": reply,
                                    "format": "MP3",
                                },
                            )
                        if r.status_code == 200:
                            audio_b64 = base64.b64encode(r.content).decode()
                            await ws.send_json({"type": "audio", "b64": audio_b64})
                        else:
                            logging.error(f"Murf error {r.status_code}: {r.text}")
                    except Exception as e:
                        logging.error(f"TTS error: {e}")

            # 🎙️ Audio Input
            elif msg.get("type") == "audio_input":
                b64 = msg["b64"]
                audio_bytes = base64.b64decode(b64)

                # Upload to AssemblyAI
                headers = {"authorization": conn_keys["assembly"]}
                upload_res = requests.post(
                    "https://api.assemblyai.com/v2/upload", headers=headers, data=audio_bytes
                )
                if upload_res.status_code != 200:
                    await ws.send_json({"type": "system", "text": "⚠️ STT upload failed"})
                    continue

                upload_url = upload_res.json()["upload_url"]
                transcript_res = requests.post(
                    "https://api.assemblyai.com/v2/transcript",
                    headers=headers,
                    json={"audio_url": upload_url},
                ).json()
                transcript_id = transcript_res["id"]

                # Poll transcript
                while True:
                    r = requests.get(
                        f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                        headers=headers,
                    ).json()
                    if r["status"] == "completed":
                        user_text = r["text"]
                        await ws.send_json({"type": "user", "text": user_text})
                        # Forward to Gemini
                        async with httpx.AsyncClient(timeout=20) as client:
                            gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                            gr = await client.post(
                                gemini_url,
                                params={"key": conn_keys["gemini"]},
                                json={"contents": [{"parts": [{"text": user_text}]}]},
                            )
                        try:
                            reply = gr.json()["candidates"][0]["content"]["parts"][0]["text"]
                        except Exception:
                            reply = "⚠️ Gemini error."

                        await ws.send_json({"type": "assistant", "text": reply})

                        # Murf TTS for voice reply
                        if conn_keys["murf"]:
                            try:
                                async with httpx.AsyncClient(timeout=30) as client:
                                    r = await client.post(
                                        "https://api.murf.ai/v1/speech/generate",
                                        headers={
                                            "api-key": conn_keys["murf"],
                                            "Content-Type": "application/json",
                                        },
                                        json={
                                            "voiceId": "en-US-natalie",
                                            "text": reply,
                                            "format": "MP3",
                                        },
                                    )
                                if r.status_code == 200:
                                    audio_b64 = base64.b64encode(r.content).decode()
                                    await ws.send_json({"type": "audio", "b64": audio_b64})
                                else:
                                    logging.error(f"Murf error {r.status_code}: {r.text}")
                            except Exception as e:
                                logging.error(f"TTS error: {e}")
                        break
                    elif r["status"] == "error":
                        await ws.send_json({"type": "system", "text": "⚠️ STT failed"})
                        break
                    await asyncio.sleep(2)

    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        await ws.close()
