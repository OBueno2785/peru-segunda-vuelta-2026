"""Pipeline de análisis de segunda vuelta Perú 2026.

Uso: python main.py
Genera resultados.json e informe.html en la raíz del proyecto.
"""
import json
from pathlib import Path

from src.cargar_datos import (cargar_primera_vuelta, cargar_transferencias,
                              cargar_vertientes, cargar_overrides, norm, FINALISTAS)
from src.proyeccion import proyectar, hacer_resolver, aplicar_indice
from src.transferencia import ESCENARIOS
from src.clasificacion import clasificar
from src.reporte import construir_informe
from src.indice_redes import cargar_indice, PESO_IAR

RAIZ = Path(__file__).resolve().parent


def verificar(pv, transf, proyeccion):
    """Chequeos de integridad; lanza AssertionError si algo no cuadra."""
    assert len(pv) == 25, f"Se esperaban 25 departamentos, hay {len(pv)}"

    # Cada partido del dato debería tener fila de transferencia (avisar de la cola sin clasificar)
    en_data = {p for parts in pv.values() for p in parts}
    faltan = en_data - set(transf)
    if faltan:
        print(f"  aviso: {len(faltan)} partido(s) sin fila de transferencia (trasvase neutral): "
              + ", ".join(sorted(pv[d][p]['partido'] for d in pv for p in pv[d] if p in faltan)[:5]))

    # Votos del finalista ⊆ votos proyectados al candidato, en todos los escenarios
    fp = norm("FUERZA POPULAR"); jxp = norm("JUNTOS POR EL PERÚ")
    for depto, parts in pv.items():
        vfp = parts.get(fp, {}).get("votos", 0)
        vjxp = parts.get(jxp, {}).get("votos", 0)
        for esc in ESCENARIOS:
            pr = proyeccion["departamentos"][depto][esc]
            assert pr["votos_keiko"] >= vfp - 1, f"{depto}/{esc}: Keiko<FP"
            assert pr["votos_sanchez"] >= vjxp - 1, f"{depto}/{esc}: Sánchez<JxP"

    # Nacional = suma de departamentos
    for esc in ESCENARIOS:
        vk = sum(proyeccion["departamentos"][d][esc]["votos_keiko"] for d in pv)
        assert abs(vk - proyeccion["nacional"][esc]["votos_keiko"]) <= 1, "nacional != suma deptos"
    print("  chequeos de integridad: OK")


def main():
    print("Cargando datos...")
    pv = cargar_primera_vuelta()
    transf = cargar_transferencias()
    vertientes = cargar_vertientes()
    overrides = cargar_overrides()
    if overrides:
        n = sum(len(v["partido"]) + len(v["bloque"]) for v in overrides.values())
        print(f"  {n} override(s) de trasvase en {len(overrides)} departamento(s)")
    resolver = hacer_resolver(transf, overrides)

    print("Proyectando segunda vuelta (3 escenarios)...")
    proyeccion = proyectar(pv, resolver)

    indice = cargar_indice()
    if indice:
        print(f"  Índice de aceptación en redes: {len(indice)} departamento(s), peso={PESO_IAR}")
        aplicar_indice(proyeccion, pv, indice, PESO_IAR)

    print("Clasificando departamentos (Ancla / Bisagra)...")
    clasif = clasificar(proyeccion, pv)

    print("Verificando...")
    verificar(pv, transf, proyeccion)

    resultados = {
        "finalistas": FINALISTAS,
        "peso_iar": PESO_IAR,
        "nacional": proyeccion["nacional"],
        "departamentos": {
            d: {"proyeccion": proyeccion["departamentos"][d],
                "clasificacion": clasif["por_departamento"][d],
                "indice_redes": indice.get(norm(d), {})}
            for d in pv
        },
        "anclas": {
            "keiko": clasif["ancla_keiko"], "sanchez": clasif["ancla_sanchez"],
        },
        "inclinados": {
            "keiko": clasif["inclina_keiko"], "sanchez": clasif["inclina_sanchez"],
        },
        "bisagra": clasif["bisagra"],
    }
    (RAIZ / "resultados.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  -> resultados.json")

    print("Generando informe.html...")
    construir_informe(proyeccion, clasif, pv, transf, vertientes, resolver, indice, PESO_IAR,
                      RAIZ / "informe.html")
    print("  -> informe.html")

    nac = proyeccion["nacional"]["base"]
    g = "Keiko" if nac["ganador"] == "keiko" else "Sánchez"
    print(f"\nResumen (base): {g} {max(nac['pct_keiko'], nac['pct_sanchez']):.1f}% · "
          f"margen {abs(nac['margen']):.1f} pts · "
          f"{len(clasif['bisagra'])} departamentos bisagra")


if __name__ == "__main__":
    main()
