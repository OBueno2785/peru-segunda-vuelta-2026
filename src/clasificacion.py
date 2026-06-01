"""Clasifica cada departamento en Ancla / Inclinado / Bisagra a partir de los 3 escenarios."""
from src.transferencia import ESCENARIOS

UMBRAL_ANCLA = 10.0    # margen base (pts) para considerar el depto "seguro"
UMBRAL_BISAGRA = 5.0   # margen base por debajo del cual el depto es disputado


def clasificar_departamento(prj_esc: dict, peso: int) -> dict:
    ganadores = {prj_esc[e]["ganador"] for e in ESCENARIOS}
    margen_base = prj_esc["base"]["margen"]
    g = prj_esc["base"]["ganador"]

    if len(ganadores) > 1:
        categoria = "bisagra"          # el ganador cambia según el escenario
    elif abs(margen_base) < UMBRAL_BISAGRA:
        categoria = "bisagra"          # ganador estable pero margen muy estrecho
    elif abs(margen_base) >= UMBRAL_ANCLA:
        categoria = f"ancla_{g}"
    else:
        categoria = f"inclina_{g}"

    return {
        "categoria": categoria,
        "ganador_base": g,
        "margen_base": margen_base,
        "margenes": {e: prj_esc[e]["margen"] for e in ESCENARIOS},
        "peso": peso,
    }


def clasificar(proyeccion: dict, pv: dict) -> dict:
    deptos = {}
    for depto, prj_esc in proyeccion["departamentos"].items():
        peso = sum(p["votos"] for p in pv[depto].values())
        deptos[depto] = clasificar_departamento(prj_esc, peso)

    def lista(cat_prefix):
        items = [{"departamento": d, **v} for d, v in deptos.items()
                 if v["categoria"].startswith(cat_prefix)]
        return sorted(items, key=lambda x: -x["peso"])

    return {
        "por_departamento": deptos,
        "ancla_keiko": lista("ancla_keiko"),
        "ancla_sanchez": lista("ancla_sanchez"),
        "inclina_keiko": lista("inclina_keiko"),
        "inclina_sanchez": lista("inclina_sanchez"),
        "bisagra": lista("bisagra"),
    }
