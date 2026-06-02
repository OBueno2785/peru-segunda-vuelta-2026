"""Carga el snapshot de 1ra vuelta y la matriz de transferencia, con nombres normalizados."""
import csv
import json
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FINALISTAS = {"FUERZA POPULAR": "keiko", "JUNTOS POR EL PERÚ": "sanchez"}
EXCLUIR = {"VOTOS NULOS", "VOTOS EN BLANCO", "VOTOS IMPUGNADOS"}


def norm(s: str) -> str:
    """Sin tildes, mayúsculas, espacios colapsados. Clave de unión robusta."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.upper().split())


def cargar_primera_vuelta() -> dict:
    """{ departamento: { partido_norm: {'partido':.., 'votos':int} } } + votos por depto."""
    raw = json.loads((DATA_DIR / "primera_vuelta_departamentos.json").read_text(encoding="utf-8"))
    out = {}
    for depto, data in raw.items():
        partidos = {}
        for p in data.get("participantes", []):
            nombre = p.get("nombreAgrupacionPolitica", "")
            if norm(nombre) in {norm(x) for x in EXCLUIR}:
                continue
            votos = int(p.get("totalVotosValidos", 0))
            if votos <= 0:
                continue
            partidos[norm(nombre)] = {"partido": nombre, "votos": votos}
        out[depto] = partidos
    return out


def cargar_transferencias() -> dict:
    """{ partido_norm: {'partido','bloque','keiko','sanchez','null','fuente'} } (shares en 0-1)."""
    out = {}
    with open(DATA_DIR / "transferencias.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            k = float(row["keiko_base"]); s = float(row["sanchez_base"]); n = float(row["null_base"])
            total = k + s + n
            if abs(total - 100) > 0.01:
                raise ValueError(f"Transferencia de '{row['partido']}' no suma 100 (suma {total})")
            out[norm(row["partido"])] = {
                "partido": row["partido"],
                "bloque": row["bloque"],
                "keiko": k / 100, "sanchez": s / 100, "null": n / 100,
                "fuente": row["fuente"],
            }
    return out


def cargar_vertientes() -> dict:
    """{ bloque: {'favorece','descripcion'} }."""
    out = {}
    with open(DATA_DIR / "vertientes.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["bloque"]] = {"favorece": row["favorece"], "descripcion": row["descripcion"]}
    return out


def cargar_mercados() -> dict:
    """Probabilidad de ganar según casas de apuestas / mercados de predicción.

    CSV: candidato,prob_ganar,fuente → {'keiko','sanchez','fuente'} (prob 0-1).
    """
    path = DATA_DIR / "mercados_apuestas.csv"
    if not path.exists():
        return {}
    out = {"fuente": ""}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cand = norm(row["candidato"])
            lado = "keiko" if "KEIKO" in cand or "FUJIMORI" in cand else "sanchez"
            out[lado] = float(row["prob_ganar"])
            out["fuente"] = out["fuente"] or row.get("fuente", "")
    return out


def cargar_overrides() -> dict:
    """Ajustes de trasvase por departamento (idiosincrasia local).

    Formato CSV: departamento,tipo,clave,keiko,sanchez,null,nota
      tipo = 'partido' (clave = nombre del partido) o 'bloque' (clave = bloque ideológico).
    Devuelve { depto_norm: {'partido': {partido_norm: shares}, 'bloque': {bloque: shares}} }.
    Archivo opcional: si no existe, no hay overrides (se usa la matriz nacional).
    """
    path = DATA_DIR / "overrides_departamento.csv"
    out: dict = {}
    if not path.exists():
        return out
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("departamento", "").strip():
                continue
            k = float(row["keiko"]); s = float(row["sanchez"]); n = float(row["null"])
            if abs(k + s + n - 100) > 0.01:
                raise ValueError(f"Override {row['departamento']}/{row['clave']} no suma 100")
            tipo = row["tipo"].strip().lower()
            if tipo not in ("partido", "bloque"):
                raise ValueError(f"tipo inválido '{tipo}' (usar 'partido' o 'bloque')")
            clave = norm(row["clave"]) if tipo == "partido" else row["clave"].strip().lower()
            d = out.setdefault(norm(row["departamento"]), {"partido": {}, "bloque": {}})
            d[tipo][clave] = {"keiko": k / 100, "sanchez": s / 100, "null": n / 100,
                              "nota": row.get("nota", "")}
    return out
