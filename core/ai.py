"""Local AI (lightweight mode for PCs with little RAM):
BioCLIP zero-shot over the short lists in labels.py + Ollama LLM with vision."""
import base64
import io
import json
import logging
import threading

import requests
from django.conf import settings
from PIL import Image, ImageOps

from .labels import ANIMALS, PLANTS

log = logging.getLogger(__name__)
_lock = threading.Lock()
_model = _preprocess = _tok = None
_text_cache = {}


def _load():
    global _model, _preprocess, _tok
    if _model is None:
        import open_clip

        _model, _, _preprocess = open_clip.create_model_and_transforms("hf-hub:imageomics/bioclip")
        _model.eval()
        _tok = open_clip.get_tokenizer("hf-hub:imageomics/bioclip")


def _text_features(kind, labels):
    import torch

    if kind not in _text_cache:
        tokens = _tok([f"a photo of {latin}." for latin, _ in labels])
        with torch.no_grad():
            f = _model.encode_text(tokens)
            f = f / f.norm(dim=-1, keepdim=True)
        _text_cache[kind] = f
    return _text_cache[kind]


def identify(path, kind="plant"):
    """Return the top 3 matches as [{'species','common_name','score'(percent)}]."""
    labels = PLANTS if kind == "plant" else ANIMALS
    try:
        import torch

        with _lock:
            _load()
            txt = _text_features(kind, labels)
            img = _preprocess(ImageOps.exif_transpose(Image.open(path)).convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                f = _model.encode_image(img)
                f = f / f.norm(dim=-1, keepdim=True)
                probs = (100.0 * f @ txt.T).softmax(dim=-1)[0]
            top = probs.topk(min(3, len(labels)))
        return [
            {"species": labels[i][0], "common_name": labels[i][1], "score": round(float(p) * 100, 1)}
            for p, i in zip(top.values.tolist(), top.indices.tolist())
        ]
    except Exception:
        log.exception("BioCLIP failed")
        return []


def _img_b64(path, max_side=768):
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def _chat(prompt, image_b64=None, timeout=600):
    msg = {"role": "user", "content": prompt}
    if image_b64:
        msg["images"] = [image_b64]
    r = requests.post(
        f"{settings.OLLAMA_URL}/api/chat",
        json={
            "model": settings.OLLAMA_MODEL,
            "messages": [msg],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3},
        },
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def _text(v):
    if isinstance(v, list):
        return "\n".join(f"• {x}" for x in v)
    return str(v or "")


def _vision_report(prompt, path):
    try:
        raw = _chat(prompt, _img_b64(path))
    except Exception:
        log.exception("Ollama failed")
        return {
            "health": "", "advice": "", "confidence": "",
            "diagnosis": "Analiza AI nu este disponibilă acum. Verifică dacă serviciul Ollama rulează "
                         "și dacă modelul a fost descărcat (vezi README).",
        }
    try:
        d = json.loads(raw)
    except ValueError:
        return {"health": "", "diagnosis": raw, "advice": "", "confidence": ""}
    return {
        "health": _text(d.get("stare")),
        "diagnosis": _text(d.get("diagnostic")),
        "advice": _text(d.get("sfat")),
        "confidence": _text(d.get("incredere")),
    }


_FORMAT = (
    'Răspunde DOAR cu JSON valid, în limba română, cu cheile: '
    '"stare" (un singur cuvânt sau expresie scurtă), '
    '"diagnostic" (ce vezi în poză, 2-4 propoziții), '
    '"sfat" (listă de 3-5 sfaturi concrete și scurte), '
    '"incredere" ("mică", "medie" sau "mare"). '
    'Dacă nu ești sigur de ceva, spune asta clar.'
)


def diagnose_plant(path, species, common):
    guess = f"{species} ({common})" if species else "necunoscută"
    prompt = (
        f"Ești un expert în îngrijirea plantelor. Planta din poză a fost identificată probabil ca: {guess}. "
        "Analizează frunzele, tulpina și pământul: pete, îngălbenire, uscare, dăunători, exces sau lipsă de apă. "
        'La "stare" folosește: sănătoasă / probleme minore / probleme serioase. ' + _FORMAT
    )
    return _vision_report(prompt, path)


def pet_advice(path, species, common):
    guess = f"{species} ({common})" if species else "necunoscut"
    prompt = (
        f"Ești un expert în îngrijirea animalelor de companie. Animalul din poză a fost identificat probabil ca: {guess}. "
        'La "stare" descrie aspectul general vizibil. La "sfat" dă sfaturi de îngrijire pentru această specie '
        "(hrană, mișcare, igienă, sănătate). Nu pune diagnostice medicale; recomandă medicul veterinar pentru orice îngrijorare. "
        + _FORMAT
    )
    return _vision_report(prompt, path)


def moderate(text):
    """Return (ok, reason). Fails open: if the AI is unavailable, the post is allowed."""
    if not settings.MODERATE_FORUM:
        return True, ""
    prompt = (
        "Ești moderator pe un forum despre plante și animale de companie. Decide dacă mesajul de mai jos este acceptabil "
        "(nu conține insulte, ură, spam, reclame sau conținut ilegal/periculos, de exemplu sfaturi de a face rău animalelor). "
        'Răspunde DOAR cu JSON: {"ok": true sau false, "motiv": "scurt, în română, gol dacă ok"}.\n\nMesaj:\n' + text[:3000]
    )
    try:
        d = json.loads(_chat(prompt, timeout=40))
        return bool(d.get("ok", True)), str(d.get("motiv", ""))
    except Exception:
        log.warning("Moderation unavailable - allowing post")
        return True, ""
