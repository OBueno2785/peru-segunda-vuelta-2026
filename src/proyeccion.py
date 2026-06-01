"""Proyección de segunda vuelta por departamento y escenario.

El trasvase se resuelve con prioridad por especificidad geográfica:
  1. override depto+partido   (lo más específico)
  2. override depto+bloque
  3. matriz nacional (partido)
  4. trasvase neutral por defecto
Así cada departamento puede tener su propia idiosincrasia sin reescribir toda la matriz.
"""
from src.cargar_datos import norm
from src.transferencia import ESCENARIOS, shares

# Trasvase neutral para partidos del dato que no estén en la matriz (cola muy menor)
DEFAULT_TRANSF = {"partido": "(sin clasificar)", "bloque": "otros",
                  "keiko": 0.30, "sanchez": 0.30, "null": 0.40, "fuente": "default"}


def hacer_resolver(transf: dict, overrides: dict):
    """Devuelve resolver(depto_norm, partido_norm) -> dict tipo-transferencia.

    depto_norm=None ignora overrides (sirve para el agregado nacional).
    """
    def resolver(depto_norm, pnorm):
        base = transf.get(pnorm, DEFAULT_TRANSF)
        bloque = base["bloque"]
        ov = overrides.get(depto_norm) if depto_norm else None
        if ov:
            o = ov["partido"].get(pnorm) or ov["bloque"].get(bloque)
            if o:
                fuente = "override-partido" if pnorm in ov["partido"] else "override-bloque"
                return {"keiko": o["keiko"], "sanchez": o["sanchez"], "null": o["null"],
                        "bloque": bloque, "fuente": fuente}
        return base
    return resolver


def proyectar_departamento(depto_norm, partidos: dict, resolver, escenario: str) -> dict:
    """Suma votos proyectados a Keiko y Sánchez en un departamento."""
    vk = vs = 0.0
    for pnorm, info in partidos.items():
        sk, ss = shares(resolver(depto_norm, pnorm), escenario)
        vk += info["votos"] * sk
        vs += info["votos"] * ss
    dos = vk + vs
    return {
        "votos_keiko": round(vk),
        "votos_sanchez": round(vs),
        "pct_keiko": round(vk / dos * 100, 2) if dos else 0.0,
        "pct_sanchez": round(vs / dos * 100, 2) if dos else 0.0,
        "margen": round((vk - vs) / dos * 100, 2) if dos else 0.0,
        "ganador": "keiko" if vk >= vs else "sanchez",
    }


def proyectar(pv: dict, resolver) -> dict:
    """{ departamento: { escenario: proyeccion } } + total nacional por escenario."""
    por_depto = {}
    for depto, partidos in pv.items():
        dn = norm(depto)
        por_depto[depto] = {esc: proyectar_departamento(dn, partidos, resolver, esc)
                            for esc in ESCENARIOS}

    nacional = {}
    for esc in ESCENARIOS:
        vk = sum(por_depto[d][esc]["votos_keiko"] for d in por_depto)
        vs = sum(por_depto[d][esc]["votos_sanchez"] for d in por_depto)
        dos = vk + vs
        nacional[esc] = {
            "votos_keiko": vk, "votos_sanchez": vs,
            "pct_keiko": round(vk / dos * 100, 2) if dos else 0.0,
            "pct_sanchez": round(vs / dos * 100, 2) if dos else 0.0,
            "margen": round((vk - vs) / dos * 100, 2) if dos else 0.0,
            "ganador": "keiko" if vk >= vs else "sanchez",
        }
    return {"departamentos": por_depto, "nacional": nacional}
