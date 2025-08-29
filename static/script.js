let mediaRecorder;
let chunks = [];

document.getElementById("micBtn").onclick = async () => {
  if (!mediaRecorder || mediaRecorder.state === "inactive") {
    let stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = () => {
      let blob = new Blob(chunks, { type: "audio/webm" });
      let reader = new FileReader();
      reader.onloadend = () => {
        let b64 = reader.result.split(",")[1];
        ws.send(JSON.stringify({ type: "audio_input", b64: b64 }));
      };
      reader.readAsDataURL(blob);
      chunks = [];
    };

    mediaRecorder.start();
    console.log("🎙️ Recording started");
    document.getElementById("micBtn").innerText = "Stop Recording";
  } else {
    mediaRecorder.stop();
    console.log("🛑 Recording stopped");
    document.getElementById("micBtn").innerText = "Start Recording";
  }
};
