"""Hornet Check NL: photo of an insect -> Asian hornet or a look-alike, with advice.

The Roboflow model (classification, 5 classes) does the recognition; this app adds the
confidence check, the advice per species and the report link.
"""
import base64
import csv
import io
import os
from pathlib import Path

import requests
import streamlit as st
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
API_URL = "https://serverless.roboflow.com"
SURE = 0.70    # from here on, a clear answer
UNSURE = 0.45  # below this: "I don't know"


def setting(name, default=""):
    try:
        return st.secrets.get(name, os.environ.get(name, default))
    except Exception:
        return os.environ.get(name, default)


@st.cache_data
def load_species():
    with open(ROOT / "species.csv", newline="", encoding="utf-8") as f:
        return {r["class"]: r for r in csv.DictReader(f)}


def classify(image, model_id, api_key):
    """Send the photo to the Roboflow model; return [(class, confidence), ...], high to low."""
    img = image.convert("RGB")
    img.thumbnail((640, 640))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    resp = requests.post(
        f"{API_URL}/{model_id}",
        params={"api_key": api_key},
        data=base64.b64encode(buf.getvalue()).decode("ascii"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    resp.raise_for_status()
    preds = resp.json().get("predictions", [])
    if isinstance(preds, dict):  # multi-label format
        preds = [{"class": k, "confidence": v["confidence"]} for k, v in preds.items()]
    return sorted(((p["class"], p["confidence"]) for p in preds), key=lambda x: -x[1])


st.set_page_config(page_title="Hornet Check NL", page_icon="🐝")
st.title("🐝 Hornet Check NL")
st.write("Seen a big wasp or hornet in the Netherlands? Take a photo. The app tells you whether it is the "
         "**invasive Asian hornet**, which you should report, or one of its native look-alikes.")

api_key = setting("ROBOFLOW_API_KEY")
model_id = setting("ROBOFLOW_MODEL", "hornet-checkv2/1")
if not api_key:
    with st.sidebar:
        api_key = st.text_input("Roboflow API key", type="password")
        model_id = st.text_input("Model ID", value=model_id)

species = load_species()
tab_upload, tab_camera = st.tabs(["📁 Upload photo", "📷 Camera"])
with tab_upload:
    uploaded = st.file_uploader("Choose a photo", type=["jpg", "jpeg", "png"])
with tab_camera:
    camera = st.camera_input("Take a photo")
source = uploaded or camera

if source and not api_key:
    st.warning("Enter your Roboflow API key first (in the sidebar on the left).")
elif source:
    image = ImageOps.exif_transpose(Image.open(source))
    with st.spinner("Recognising the insect..."):
        try:
            ranked = classify(image, model_id, api_key)
        except Exception as e:
            st.error(f"The model returned an error: {e}")
            st.stop()
    st.image(image, width="stretch")

    if not ranked or ranked[0][1] < UNSURE:
        st.info("❓ **I don't know.** It may not be one of the 5 insects I know, or the photo is not "
                "sharp enough. Try a close-up from above or from the side. "
                "Think it might be an Asian hornet? Report it anyway: an expert will check it.")
        st.link_button("Report on waarneming.nl", "https://waarneming.nl")
    else:
        cls, conf = ranked[0]
        info = species.get(cls, {"name": cls, "latin": "", "invasive": "no", "why": "", "advice": ""})
        pct = f"{conf:.0%}"
        if conf < SURE:
            st.warning(f"🤔 Probably **{info['name']}** ({pct} sure), but I'm not certain. "
                       "Check it yourself before you act.")
        elif info["invasive"] == "yes":
            st.error(f"⚠️ **{info['name']}** (*{info['latin']}*), {pct} sure. This is an invasive alien species!")
        else:
            st.success(f"✅ **{info['name']}** (*{info['latin']}*), {pct} sure. Native species.")

        st.write(f"**Why it matters:** {info['why']}")
        st.write(f"**What to do:** {info['advice']}")
        if info["invasive"] == "yes":
            st.link_button("⚠️ Report this Asian hornet on waarneming.nl", "https://waarneming.nl",
                           type="primary")

        if len(ranked) > 1 and ranked[1][1] >= 0.15:
            alt = species.get(ranked[1][0], {}).get("name", ranked[1][0])
            st.caption(f"The model's second guess: {alt} ({ranked[1][1]:.0%}).")

    with st.expander("All model scores"):
        for c, p in ranked:
            st.progress(min(max(p, 0.0), 1.0), text=f"{species.get(c, {}).get('name', c)}: {p:.0%}")

st.divider()
st.caption("The app only knows these 5 insects: Asian hornet, European hornet, wasp, "
           "hornet hoverfly and honeybee. It is a helper, not an official identification. "
           "When unsure, the model misses about half of Asian hornets, so always report when in doubt. "
           "Trained in Roboflow on Dutch iNaturalist photos (see the README and data card).")
