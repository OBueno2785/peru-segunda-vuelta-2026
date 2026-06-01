"""Índice de Aceptación en Redes (IAR) departamental.

Combina un snapshot de noticias (data/indice_redes.csv) con señales sociales opcionales
(data/social_signals.csv). El IAR no inventa votos: solo orienta cómo se rompe el voto
indeciso (blanco/nulo) de cada departamento (ver proyeccion.aplicar_indice).
"""
import csv
from pathlib import Path

from src.cargar_datos import DATA_DIR, norm

PESO_IAR = 0.5  # intensidad por defecto (0 = ignorar redes, 1 = romper todo el indeciso)


def cargar_social() -> dict:
    """Adaptador opcional. CSV: departamento,candidato,menciones,sentimiento(-1..1).

    Devuelve { depto_norm: net_social ∈ [-1,1] } (positivo favorece a Keiko).
    """
    path = DATA_DIR / "social_signals.csv"
    if not path.exists():
        return {}
    acc = {}  # depto -> {'keiko':[sum_w_sent, sum_w], 'sanchez':[...]}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = norm(row["departamento"]); cand = norm(row["candidato"])
            m = float(row.get("menciones", 0) or 0)
            sent = float(row.get("sentimiento", 0) or 0)
            lado = "keiko" if "FUJIMORI" in cand or "KEIKO" in cand or "FUERZA POPULAR" in cand else "sanchez"
            slot = acc.setdefault(d, {"keiko": [0.0, 0.0], "sanchez": [0.0, 0.0]})[lado]
            slot[0] += m * sent; slot[1] += m
    out = {}
    for d, v in acc.items():
        ak = v["keiko"][0] / v["keiko"][1] if v["keiko"][1] else 0.0
        as_ = v["sanchez"][0] / v["sanchez"][1] if v["sanchez"][1] else 0.0
        out[d] = max(-1.0, min(1.0, (ak - as_) / 2))
    return out


def cargar_indice() -> dict:
    """{ depto_norm: {iar_keiko, iar_sanchez, net, cobertura, fuente} } (net ∈ [-1,1])."""
    path = DATA_DIR / "indice_redes.csv"
    out = {}
    if not path.exists():
        return out
    social = cargar_social()
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = norm(row["departamento"])
            net = float(row["net"])
            fuente = row.get("fuente", "")
            if d in social:                       # mezclar noticias + social a partes iguales
                net = round((net + social[d]) / 2, 3)
                fuente += " + social CSV"
            out[d] = {
                "iar_keiko": float(row["iar_keiko"]), "iar_sanchez": float(row["iar_sanchez"]),
                "net": net, "cobertura": row.get("cobertura", ""), "fuente": fuente,
            }
    return out
