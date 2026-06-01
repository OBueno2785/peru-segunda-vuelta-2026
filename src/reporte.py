"""Genera informe.html autocontenido: mapa Ancla/Bisagra + tablas + escenarios."""
import json
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from src.cargar_datos import DATA_DIR, norm

CAT_LABEL = {
    "ancla_keiko": "Ancla Keiko", "inclina_keiko": "Inclina Keiko",
    "bisagra": "Bisagra", "inclina_sanchez": "Inclina Sánchez",
    "ancla_sanchez": "Ancla Sánchez",
}
CAT_COLOR = {
    "Ancla Keiko": "#C2410C", "Inclina Keiko": "#FDBA74",
    "Bisagra": "#FCD34D", "Inclina Sánchez": "#FCA5A5", "Ancla Sánchez": "#B91C1C",
}
ESC_LABEL = {"base": "Base", "favK": "Favorable Keiko", "favS": "Favorable Sánchez"}


def _mapa(clasif: dict) -> str:
    geo = json.loads((DATA_DIR / "peru-departamentos.geojson").read_text(encoding="utf-8"))
    for f in geo["features"]:
        f["properties"]["KEY"] = norm(f["properties"]["NOMBDEP"])

    deptos = clasif["por_departamento"]
    keys, cats, texto = [], [], []
    for depto, v in deptos.items():
        keys.append(norm(depto))
        cats.append(CAT_LABEL[v["categoria"]])
        g = "Keiko" if v["ganador_base"] == "keiko" else "Sánchez"
        texto.append(f"<b>{depto}</b><br>Gana (base): {g}<br>"
                     f"Margen base: {v['margen_base']:+.1f} pts<br>Votos válidos 1ra v.: {v['peso']:,}")

    fig = px.choropleth(
        geojson=geo, locations=keys, featureidkey="properties.KEY",
        color=cats, color_discrete_map=CAT_COLOR,
        category_orders={"color": list(CAT_COLOR)},
    )
    fig.update_traces(customdata=texto, hovertemplate="%{customdata}<extra></extra>")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        title="Mapa de segunda vuelta: departamentos Ancla y Bisagra",
        legend_title_text="Categoría", margin=dict(l=0, r=0, t=40, b=0), height=600,
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def _barras_nacional(nacional: dict) -> str:
    escs = list(ESC_LABEL)
    fig = go.Figure()
    fig.add_bar(name="Keiko (FP)", x=[ESC_LABEL[e] for e in escs],
                y=[nacional[e]["pct_keiko"] for e in escs], marker_color="#C2410C",
                text=[f"{nacional[e]['pct_keiko']:.1f}%" for e in escs], textposition="outside")
    fig.add_bar(name="Sánchez (JxP)", x=[ESC_LABEL[e] for e in escs],
                y=[nacional[e]["pct_sanchez"] for e in escs], marker_color="#B91C1C",
                text=[f"{nacional[e]['pct_sanchez']:.1f}%" for e in escs], textposition="outside")
    fig.update_layout(title="Proyección nacional por escenario (voto válido entre los dos)",
                      barmode="group", yaxis_range=[0, 70], height=400,
                      margin=dict(l=40, r=20, t=50, b=30))
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def _tabla(headers, filas, clases=None) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = []
    for fila in filas:
        tds = "".join(f"<td>{c}</td>" for c in fila)
        trs.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


def _fmt_ganador(g):
    return "Keiko" if g == "keiko" else "Sánchez"


def construir_informe(proyeccion, clasif, pv, transf, vertientes, salida: Path):
    nac = proyeccion["nacional"]
    base = nac["base"]
    ganador_nac = _fmt_ganador(base["ganador"])

    mapa_html = _mapa(clasif)
    barras_html = _barras_nacional(nac)

    # Resumen de categorías
    resumen = _tabla(
        ["Categoría", "N° deptos", "Departamentos"],
        [
            ["Ancla Keiko", len(clasif["ancla_keiko"]),
             ", ".join(d["departamento"] for d in clasif["ancla_keiko"]) or "—"],
            ["Inclina Keiko", len(clasif["inclina_keiko"]),
             ", ".join(d["departamento"] for d in clasif["inclina_keiko"]) or "—"],
            ["Bisagra", len(clasif["bisagra"]),
             ", ".join(d["departamento"] for d in clasif["bisagra"]) or "—"],
            ["Inclina Sánchez", len(clasif["inclina_sanchez"]),
             ", ".join(d["departamento"] for d in clasif["inclina_sanchez"]) or "—"],
            ["Ancla Sánchez", len(clasif["ancla_sanchez"]),
             ", ".join(d["departamento"] for d in clasif["ancla_sanchez"]) or "—"],
        ],
    )

    # Ranking de bisagra por peso electoral
    bisagra = _tabla(
        ["#", "Departamento", "Votos válidos 1ra v.", "Margen base", "Margen favK", "Margen favS"],
        [[i + 1, d["departamento"], f"{d['peso']:,}", f"{d['margen_base']:+.1f}",
          f"{d['margenes']['favK']:+.1f}", f"{d['margenes']['favS']:+.1f}"]
         for i, d in enumerate(clasif["bisagra"])],
    )

    # Tabla por departamento (ordenada por margen base, de más Sánchez a más Keiko)
    deptos_ord = sorted(clasif["por_departamento"].items(), key=lambda kv: kv[1]["margen_base"])
    detalle = _tabla(
        ["Departamento", "Gana (base)", "Margen base", "Categoría", "Votos válidos 1ra v."],
        [[d, _fmt_ganador(v["ganador_base"]), f"{v['margen_base']:+.1f}",
          CAT_LABEL[v["categoria"]], f"{v['peso']:,}"] for d, v in deptos_ord],
    )

    # Tabla de transferencia / vertientes (ordenada por trasvase neto a Keiko)
    filas_t = []
    for t in sorted(transf.values(), key=lambda x: -(x["keiko"] - x["sanchez"])):
        if t["fuente"] == "finalista":
            continue
        favorece = vertientes.get(t["bloque"], {}).get("favorece", "—")
        filas_t.append([t["partido"], t["bloque"], favorece,
                        f"{t['keiko']*100:.0f}%", f"{t['sanchez']*100:.0f}%",
                        f"{t['null']*100:.0f}%", t["fuente"]])
    transf_html = _tabla(
        ["Partido (1ra vuelta)", "Bloque", "Favorece", "→ Keiko", "→ Sánchez", "→ Blanco/Nulo", "Fuente"],
        filas_t,
    )

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Segunda Vuelta Perú 2026 — Keiko Fujimori vs Roberto Sánchez</title>
<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color:#1f2937;
         max-width: 1100px; margin: 0 auto; padding: 24px; line-height: 1.5; }}
  h1 {{ font-size: 1.7rem; margin-bottom: 0; }}
  h2 {{ margin-top: 2.2rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px; }}
  .sub {{ color:#6b7280; margin-top: 4px; }}
  .cards {{ display:flex; gap:16px; flex-wrap:wrap; margin: 16px 0; }}
  .card {{ flex:1; min-width:220px; border-radius:12px; padding:16px; color:#fff; }}
  .k {{ background:#C2410C; }} .s {{ background:#B91C1C; }}
  .card .big {{ font-size:2rem; font-weight:700; }}
  table {{ border-collapse: collapse; width:100%; margin:12px 0; font-size:0.9rem; }}
  th, td {{ border:1px solid #e5e7eb; padding:6px 10px; text-align:left; }}
  th {{ background:#f9fafb; }}
  td:nth-child(n+3) {{ font-variant-numeric: tabular-nums; }}
  .nota {{ background:#fffbeb; border-left:4px solid #f59e0b; padding:10px 14px; border-radius:6px;
          font-size:0.9rem; color:#92400e; }}
  footer {{ margin-top:3rem; color:#9ca3af; font-size:0.8rem; }}
</style></head><body>

<h1>Segunda Vuelta Presidencial — Perú 2026</h1>
<p class="sub">Keiko Fujimori (Fuerza Popular) vs Roberto Sánchez (Juntos por el Perú) · Balotaje del 7 de junio de 2026</p>

<p>Proyección departamental construida sobre el resultado de 1ra vuelta de ONPE y un modelo de
transferencia de votos de los partidos eliminados (cruces Ipsos mayo-2026 + heurística por bloque
ideológico), evaluado en tres escenarios. <strong>No es un pronóstico cerrado</strong>: identifica
quién parte con ventaja y dónde se define la elección.</p>

<div class="cards">
  <div class="card k"><div>Keiko Fujimori — escenario base</div>
    <div class="big">{base['pct_keiko']:.1f}%</div><div>{base['votos_keiko']:,} votos proyectados</div></div>
  <div class="card s"><div>Roberto Sánchez — escenario base</div>
    <div class="big">{base['pct_sanchez']:.1f}%</div><div>{base['votos_sanchez']:,} votos proyectados</div></div>
</div>
<p><strong>Ganador nacional (escenario base):</strong> {ganador_nac} · margen {base['margen']:+.1f} pts
(voto válido entre los dos candidatos).</p>

<h2>Proyección nacional por escenario</h2>
{barras_html}

<h2>Mapa: departamentos Ancla y Bisagra</h2>
<p class="sub"><b>Ancla</b>: el candidato gana en los 3 escenarios con ≥10 pts. <b>Bisagra</b>: el ganador
cambia entre escenarios o el margen base es &lt;5 pts. Naranja = Keiko, rojo = Sánchez, amarillo = bisagra.</p>
{mapa_html}

<h2>Resumen por categoría</h2>
{resumen}

<h2>Departamentos bisagra (ordenados por peso electoral)</h2>
<p class="sub">Donde se define la elección: el ranking prioriza los de mayor cantidad de votos.</p>
{bisagra}

<h2>Detalle por departamento</h2>
{detalle}

<h2>Modelo de transferencia y vertientes</h2>
<p class="sub">Cómo se reparte el voto de cada partido eliminado en el escenario base. "Favorece"
indica la inclinación del bloque ideológico.</p>
{transf_html}

<div class="nota">El trasvase es el supuesto más sensible. Los % de Renovación Popular, Buen Gobierno,
Obras, País para Todos y Ahora Nación provienen de cruces de Ipsos (mayo 2026); el resto usa
heurística por bloque. Ver <code>FUENTES.md</code>.</div>

<footer>Generado por el pipeline de <code>peru-segunda-vuelta-2026</code>. Datos base: ONPE 1ra vuelta.</footer>
</body></html>"""

    salida.write_text(html, encoding="utf-8")
