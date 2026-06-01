"""Proyección de segunda vuelta por departamento y escenario."""
from src.transferencia import ESCENARIOS, shares

# Trasvase neutral para partidos del dato que no estén en la matriz (cola muy menor)
DEFAULT_TRANSF = {"partido": "(sin clasificar)", "bloque": "otros",
                  "keiko": 0.30, "sanchez": 0.30, "null": 0.40, "fuente": "default"}


def proyectar_departamento(partidos: dict, transf: dict, escenario: str) -> dict:
    """Suma votos proyectados a Keiko y Sánchez en un departamento."""
    vk = vs = 0.0
    for pnorm, info in partidos.items():
        t = transf.get(pnorm, DEFAULT_TRANSF)
        sk, ss = shares(t, escenario)
        vk += info["votos"] * sk
        vs += info["votos"] * ss
    dos = vk + vs
    return {
        "votos_keiko": round(vk),
        "votos_sanchez": round(vs),
        "pct_keiko": round(vk / dos * 100, 2) if dos else 0.0,    # sobre voto a los dos
        "pct_sanchez": round(vs / dos * 100, 2) if dos else 0.0,
        "margen": round((vk - vs) / dos * 100, 2) if dos else 0.0,  # + = ventaja Keiko
        "ganador": "keiko" if vk >= vs else "sanchez",
    }


def proyectar(pv: dict, transf: dict) -> dict:
    """{ departamento: { escenario: proyeccion } } + total nacional por escenario."""
    por_depto = {}
    for depto, partidos in pv.items():
        por_depto[depto] = {esc: proyectar_departamento(partidos, transf, esc) for esc in ESCENARIOS}

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
