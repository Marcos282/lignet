"""Fixed ComfyUI SD 1.x workflow; no uploaded workflows or remote model endpoints."""
import json
import secrets
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Photo


def endpoint():
    url = urlsplit(settings.BLOG_COMFY_URL)
    if (url.scheme != "http" or url.hostname not in ("localhost", "127.0.0.1", "::1")
            or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment):
        raise ValueError("BLOG_COMFY_URL deve apontar para HTTP local, sem caminho ou credenciais.")
    if not settings.BLOG_IMAGE_CHECKPOINT or not settings.BLOG_IMAGE_LICENSE_CONFIRMED:
        raise ValueError("Configure o checkpoint SD 1.x e confirme sua licença antes de gerar imagens.")
    if len(settings.BLOG_IMAGE_CHECKPOINT) > 200:
        raise ValueError("O nome do checkpoint excede 200 caracteres.")
    return settings.BLOG_COMFY_URL.rstrip("/")


def local_request(method, path, *, payload=None, params=None, image=False):
    with requests.Session() as session:
        session.trust_env = False
        with session.request(method, endpoint() + path, json=payload, params=params,
                             timeout=(3, 30), stream=True, allow_redirects=False) as response:
            if response.status_code != 200:
                raise ValueError(f"ComfyUI retornou HTTP {response.status_code}.")
            parts, length = [], 0
            limit = 8 * 1024 * 1024 if image else 1024 * 1024
            for chunk in response.iter_content(65536):
                length += len(chunk)
                if length > limit:
                    raise ValueError("Resposta do ComfyUI excede o limite permitido.")
                parts.append(chunk)
    data = b"".join(parts)
    return data if image else json.loads(data)


def submit_image(article):
    checkpoint = settings.BLOG_IMAGE_CHECKPOINT
    if any(c in checkpoint for c in ("/", "\\", "\x00")):
        raise ValueError("Use apenas o nome do checkpoint instalado no ComfyUI.")
    workflow = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": article.image_prompt}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {
            "clip": ["1", 1], "text": "text, watermark, logo, photorealistic evidence, fake news photograph"}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 512, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0],
            "seed": secrets.randbits(48), "steps": 20, "cfg": 7, "sampler_name": "euler",
            "scheduler": "normal", "denoise": 1}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": f"lignet-{article.pk}"}},
    }
    result = local_request("POST", "/prompt", payload={"prompt": workflow})
    job = result.get("prompt_id") if isinstance(result, dict) else None
    if not isinstance(job, str) or not job or len(job) > 100 or any(c not in "0123456789abcdef-" for c in job.lower()):
        raise ValueError("ComfyUI não retornou um identificador de tarefa válido.")
    article.image_job = job
    article.image_model = checkpoint
    article.image_requested_at = timezone.now()
    article.save(update_fields=["image_job", "image_model", "image_requested_at", "updated_at"])


def receive_image(article):
    result = local_request("GET", "/history/" + article.image_job)
    if not isinstance(result, dict):
        raise ValueError("Histórico inválido do ComfyUI.")
    history = result.get(article.image_job)
    if history is None:
        return False
    if not isinstance(history, dict):
        raise ValueError("Registro inválido no histórico ComfyUI.")
    status = history.get("status", {})
    if not isinstance(status, dict):
        raise ValueError("Status inválido no histórico ComfyUI.")
    if status.get("status_str") == "error":
        raise ValueError("ComfyUI registrou falha na geração da ilustração.")
    if not status.get("completed"):
        return False
    outputs = history.get("outputs")
    if not isinstance(outputs, dict) or not isinstance(outputs.get("7"), dict):
        raise ValueError("ComfyUI não retornou a saída do workflow configurado.")
    images = outputs["7"].get("images", [])
    if not isinstance(images, list) or len(images) != 1:
        raise ValueError("ComfyUI concluiu sem retornar uma imagem.")
    info = images[0]
    if (not isinstance(info, dict) or info.get("type") != "output"
            or not isinstance(info.get("filename"), str) or "/" in info["filename"] or "\\" in info["filename"]
            or info.get("subfolder", "") not in ("",)):
        raise ValueError("A saída da imagem não corresponde ao diretório esperado.")
    raw = local_request("GET", "/view", params={"filename": info["filename"], "type": "output"}, image=True)
    photo = Photo(title=article.title[:120], category=article.category,
                  image=ContentFile(raw, name="local.png"),
                  alt=f"Ilustração conceitual gerada por IA sobre {article.category.name}"[:240],
                  credit="Lignet Brasil — ilustração gerada com IA local",
                  rights_confirmed=True, allow_automatic=False, generated=True,
                  model_name=article.image_model)
    photo.save()
    try:
        article.cover = photo
        article.image_job = ""
        article.image_retry_at = None
        article.save(update_fields=["cover", "image_job", "image_retry_at", "updated_at"])
    except Exception:
        photo.image.delete(save=False)
        photo.delete()
        raise
    return True
