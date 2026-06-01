"""Agrega un snapshot del IAR al histórico (para el monitoreo recurrente).

Flujo del monitor recurrente:
  1. Investigar noticias/redes por departamento (búsqueda web) y actualizar la columna
     `net` de data/indice_redes.csv (−1..1, positivo favorece a Keiko).
  2. Ejecutar:  python -m src.agregar_snapshot
     → re-deriva iar_keiko/iar_sanchez desde net, y agrega la fila de HOY (una por
       departamento) a data/indice_historial.csv. Si ya hay filas de hoy, las reemplaza.
  3. python main.py  → regenera informe.html / resultados.json con la nueva tendencia.
"""
import csv
from datetime import date
from pathlib import Path

from src.cargar_datos import DATA_DIR

CAMPOS = ["departamento", "iar_keiko", "iar_sanchez", "net", "cobertura", "fuente"]


def main():
    redes = DATA_DIR / "indice_redes.csv"
    rows = list(csv.DictReader(open(redes, encoding="utf-8")))
    for r in rows:                      # re-derivar IAR display desde net
        net = float(r["net"])
        r["iar_keiko"] = round(50 + net * 50)
        r["iar_sanchez"] = round(50 - net * 50)
    with open(redes, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(rows)

    hist = DATA_DIR / "indice_historial.csv"
    hoy = date.today().isoformat()
    previas = []
    if hist.exists():
        previas = [r for r in csv.reader(open(hist, encoding="utf-8"))]
        cab, previas = previas[0], [r for r in previas[1:] if r and r[0] != hoy]
    else:
        cab = ["fecha", "departamento", "net", "iar_keiko", "iar_sanchez"]
    with open(hist, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(cab); w.writerows(previas)
        for r in rows:
            w.writerow([hoy, r["departamento"], r["net"], r["iar_keiko"], r["iar_sanchez"]])
    print(f"Snapshot {hoy} agregado: {len(rows)} departamentos")


if __name__ == "__main__":
    main()
