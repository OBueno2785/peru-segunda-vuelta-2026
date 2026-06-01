"""Modelo de transferencia: deriva 3 escenarios reasignando el voto indeciso/blanco.

El supuesto base proviene de los cruces de Ipsos (mayo 2026) y heurística por bloque.
La incertidumbre se concentra en el ~20-55% que va a blanco/nulo/no-precisa ('null').
Los escenarios difieren SOLO en cómo se rompe ese bloque indeciso:

  base : el indeciso se queda en blanco/nulo (no suma a ningún candidato).
  favK : la mitad del indeciso (ALPHA) se inclina a Keiko.
  favS : la mitad del indeciso (ALPHA) se inclina a Sánchez.

Es transparente y conservador: no inventa trasvase entre candidatos, solo reparte
el margen real de incertidumbre. Cada escenario sigue sumando 100%.
"""
ALPHA = 0.5
ESCENARIOS = ("base", "favK", "favS")


def shares(transf: dict, escenario: str) -> tuple[float, float]:
    """Devuelve (share_keiko, share_sanchez) del partido en el escenario dado."""
    k, s, n = transf["keiko"], transf["sanchez"], transf["null"]
    if escenario == "favK":
        return k + ALPHA * n, s
    if escenario == "favS":
        return k, s + ALPHA * n
    return k, s  # base
