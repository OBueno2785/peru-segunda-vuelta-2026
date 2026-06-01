"""Genera informe.html: dashboard interactivo (mapa + panel por departamento) autocontenido.

El mapa y los gráficos se dibujan en el navegador con Plotly (embebido inline). Al
seleccionar un departamento el mapa se enfoca en su forma; los % de trasvase son
editables por departamento y todo se recalcula en vivo.
"""
import json
from pathlib import Path

from plotly.offline import get_plotlyjs

from src.cargar_datos import DATA_DIR, norm, FINALISTAS
from src.transferencia import ESCENARIOS, shares

_FINAL_NORM = {norm(p) for p in FINALISTAS}

CAT_LABEL = {
    "ancla_keiko": "Ancla Keiko", "inclina_keiko": "Inclina Keiko",
    "bisagra": "Bisagra", "inclina_sanchez": "Inclina Sánchez",
    "ancla_sanchez": "Ancla Sánchez",
}
CAT_COLOR = {
    "Ancla Keiko": "#C2410C", "Inclina Keiko": "#FDBA74",
    "Bisagra": "#FCD34D", "Inclina Sánchez": "#FCA5A5", "Ancla Sánchez": "#B91C1C",
}


def _tabla(headers, filas) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in fila) + "</tr>" for fila in filas)
    return f"<table class='full'><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def _fmt_g(g):
    return "Keiko" if g == "keiko" else "Sánchez"


def _detalle_partidos(depto_norm, partidos: dict, resolver, top: int = 10) -> list:
    """Lista por partido con trasvase RESUELTO para el departamento (incluye overrides)."""
    filas = []
    for pnorm, info in partidos.items():
        t = resolver(depto_norm, pnorm)
        k, s = shares(t, "base")
        v = info["votos"]
        es_base = pnorm in _FINAL_NORM   # FP→Keiko, JxP→Sánchez: base propia, no se ajusta
        filas.append({
            "partido": info["partido"], "bloque": t["bloque"], "votos": v,
            "k": round(k * 100, 1), "s": round(s * 100, 1),
            "n": round(max(0.0, 1 - k - s) * 100, 1),
            "aporteK": round(v * k), "aporteS": round(v * s),
            "override": t.get("fuente", "").startswith("override"),
            "editable": not es_base, "base": es_base,
        })
    filas.sort(key=lambda x: -x["votos"])
    if len(filas) > top:
        resto = filas[top:]
        vr = sum(r["votos"] for r in resto) or 1
        ak = sum(r["aporteK"] for r in resto); as_ = sum(r["aporteS"] for r in resto)
        filas = filas[:top] + [{
            "partido": f"+{len(resto)} partidos menores", "bloque": "otros",
            "votos": vr, "k": round(ak / vr * 100, 1), "s": round(as_ / vr * 100, 1),
            "n": round(max(0.0, 1 - ak / vr - as_ / vr) * 100, 1),
            "aporteK": ak, "aporteS": as_, "override": False, "editable": False, "base": False,
        }]
    return filas


def _entrada(nombre, prj_esc, cat_key, peso, depto_norm, partidos, resolver):
    return {
        "nombre": nombre,
        "catKey": cat_key,
        "peso": peso,
        "partidos": _detalle_partidos(depto_norm, partidos, resolver),
    }


def construir_informe(proyeccion, clasif, pv, transf, vertientes, resolver, indice, historial,
                      peso_iar, salida: Path):
    nac = proyeccion["nacional"]
    base = nac["base"]

    # GeoJSON con clave normalizada para casar con las ubicaciones del mapa
    geo = json.loads((DATA_DIR / "peru-departamentos.geojson").read_text(encoding="utf-8"))
    for f in geo["features"]:
        f["properties"]["KEY"] = norm(f["properties"]["NOMBDEP"])

    # Datos embebidos para el panel + mapa interactivos
    nac_part = {}
    for parts in pv.values():
        for pn, info in parts.items():
            d = nac_part.setdefault(pn, {"partido": info["partido"], "votos": 0})
            d["votos"] += info["votos"]

    embed = {"nacional": _entrada("PERÚ — resultado proyectado", nac, None,
                                  sum(p["votos"] for p in nac_part.values()), None, nac_part, resolver),
             "departamentos": {},
             "meta": {"nBisagra": len(clasif["bisagra"])}}
    for depto, prj_esc in proyeccion["departamentos"].items():
        cl = clasif["por_departamento"][depto]
        ent = _entrada(depto, prj_esc, cl["categoria"], cl["peso"], norm(depto), pv[depto], resolver)
        ix = indice.get(norm(depto), {})
        ent["net"] = ix.get("net", 0.0)
        ent["iarK"] = ix.get("iar_keiko", 50); ent["iarS"] = ix.get("iar_sanchez", 50)
        serie = historial.get(norm(depto), [])
        ent["hist"] = [{"f": h["fecha"], "net": h["net"]} for h in serie]
        ent["tend"] = round(serie[-1]["net"] - serie[-2]["net"], 3) if len(serie) >= 2 else 0.0
        embed["departamentos"][norm(depto)] = ent
    # Nacional ya ajustado por IAR (no se recalcula en vivo): se embebe precomputado
    embed["nacional"]["escNac"] = {
        e: {"k": nac[e]["pct_keiko"], "s": nac[e]["pct_sanchez"],
            "margen": nac[e]["margen"], "ganador": nac[e]["ganador"]} for e in ESCENARIOS}
    # Serie nacional del IAR (promedio ponderado por peso electoral) = indicador adelantado
    pesos = {norm(d): clasif["por_departamento"][d]["peso"] for d in clasif["por_departamento"]}
    fechas = sorted({h["fecha"] for s in historial.values() for h in s})
    nac_hist = []
    for f in fechas:
        num = den = 0.0
        for dk, serie in historial.items():
            pt = next((x for x in serie if x["fecha"] == f), None)
            if pt:
                num += pt["net"] * pesos.get(dk, 0); den += pesos.get(dk, 0)
        nac_hist.append({"f": f, "net": round(num / den, 3) if den else 0.0})
    embed["nacional"]["hist"] = nac_hist
    embed["nacional"]["tend"] = round(nac_hist[-1]["net"] - nac_hist[-2]["net"], 3) if len(nac_hist) >= 2 else 0.0
    # IAR Nacional = agregación (ponderada por peso electoral) de los IAR departamentales.
    # De este agregado bottom-up sale el resultado proyectado nacional.
    net_nac = nac_hist[-1]["net"] if nac_hist else 0.0
    embed["nacional"]["net"] = net_nac
    embed["nacional"]["iarK"] = round(50 + net_nac * 50)
    embed["nacional"]["iarS"] = round(50 - net_nac * 50)

    bisagra_tbl = _tabla(
        ["#", "Departamento", "Margen proyectado", "favK", "favS"],
        [[i + 1, d["departamento"], f"{d['margen_base']:+.1f}",
          f"{d['margenes']['favK']:+.1f}", f"{d['margenes']['favS']:+.1f}"]
         for i, d in enumerate(clasif["bisagra"])])

    filas_t = []
    for t in sorted(transf.values(), key=lambda x: -(x["keiko"] - x["sanchez"])):
        if t["fuente"] == "finalista":
            continue
        filas_t.append([t["partido"], t["bloque"],
                        vertientes.get(t["bloque"], {}).get("favorece", "—"),
                        f"{t['keiko']*100:.0f}%", f"{t['sanchez']*100:.0f}%",
                        f"{t['null']*100:.0f}%", t["fuente"]])
    transf_tbl = _tabla(
        ["Partido", "Bloque", "Favorece", "→Keiko", "→Sánchez", "→Blanco/Nulo", "Fuente"],
        filas_t)

    iar_filas = sorted(
        [(d, indice.get(norm(d), {})) for d in proyeccion["departamentos"]],
        key=lambda x: x[1].get("net", 0))
    iar_tbl = _tabla(
        ["Departamento", "IAR Keiko", "IAR Sánchez", "Neto", "Cobertura", "Fuente"],
        [[d, ix.get("iar_keiko", "—"), ix.get("iar_sanchez", "—"),
          f"{ix.get('net', 0):+.2f}", ix.get("cobertura", "—"), ix.get("fuente", "")]
         for d, ix in iar_filas])

    html = (_PLANTILLA
            .replace("__BASE_K__", f"{base['pct_keiko']:.1f}")
            .replace("__BASE_S__", f"{base['pct_sanchez']:.1f}")
            .replace("__GANADOR__", _fmt_g(base["ganador"]))
            .replace("__MARGEN__", f"{abs(base['margen']):.1f}")
            .replace("__N_BISAGRA__", str(len(clasif["bisagra"])))
            .replace("__BISAGRA_TBL__", bisagra_tbl)
            .replace("__TRANSF_TBL__", transf_tbl)
            .replace("__IAR_TBL__", iar_tbl)
            .replace("__PESOIAR__", str(peso_iar))
            .replace("__PLOTLYJS__", get_plotlyjs())
            .replace("__GEO__", json.dumps(geo, ensure_ascii=False))
            .replace("__DATA__", json.dumps(embed, ensure_ascii=False))
            .replace("__CATCOLOR__", json.dumps(CAT_COLOR, ensure_ascii=False)))

    salida.write_text(html, encoding="utf-8")


_PLANTILLA = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Segunda Vuelta Perú 2026 — Keiko vs Sánchez</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: system-ui,-apple-system,Segoe UI,Roboto,sans-serif; color:#1f2937; margin:0; background:#f3f4f6; }
  header { background:#fff; border-bottom:1px solid #e5e7eb; padding:10px 18px;
           display:flex; align-items:center; gap:18px; flex-wrap:wrap; position:sticky; top:0; z-index:5; }
  header h1 { font-size:1.05rem; margin:0; white-space:nowrap; }
  header .sub { color:#6b7280; font-size:.78rem; }
  .chips { margin-left:auto; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  .chip { font-size:.8rem; padding:4px 10px; border-radius:999px; color:#fff; font-weight:600; }
  .chip.k { background:#C2410C; } .chip.s { background:#B91C1C; } .chip.meta { background:#374151; }
  .wrap { display:grid; grid-template-columns: 1fr minmax(360px, 460px); gap:12px; padding:12px; height: calc(100vh - 52px); }
  .card { background:#fff; border:1px solid #e5e7eb; border-radius:10px; overflow:hidden; display:flex; flex-direction:column; }
  .card > .hd { padding:8px 12px; border-bottom:1px solid #f0f0f0; font-weight:600; font-size:.88rem; display:flex; gap:8px; align-items:center; }
  .card > .hd button { margin-left:auto; font-size:.72rem; padding:3px 8px; border:1px solid #d1d5db; border-radius:6px; background:#fff; cursor:pointer; }
  #mapa { flex:1; min-height:0; }
  #panel { padding:12px; overflow:auto; }
  .pnl-title { display:flex; align-items:center; gap:8px; margin:0 0 2px; font-size:1.1rem; }
  .badge { font-size:.72rem; padding:2px 8px; border-radius:6px; font-weight:600; }
  .pnl-sub { color:#6b7280; font-size:.8rem; margin-bottom:10px; }
  .takeaway { font-size:.92rem; line-height:1.35; background:#f1f5f9; border-left:4px solid #475569;
              padding:8px 11px; border-radius:6px; margin:8px 0; }
  .takeaway b.k { color:#C2410C; } .takeaway b.s { color:#B91C1C; }
  .tug { margin:10px 0 2px; }
  .tug-bar { position:relative; display:flex; height:34px; border-radius:7px; overflow:hidden;
             box-shadow:inset 0 0 0 1px rgba(0,0,0,.06); }
  .tug-seg { display:flex; align-items:center; color:#fff; font-weight:700; font-size:1rem;
             transition:width .25s ease; min-width:42px; }
  .tug-seg.k { background:#C2410C; justify-content:flex-start; padding-left:9px; }
  .tug-seg.s { background:#B91C1C; justify-content:flex-end; padding-right:9px; }
  .tug-50 { position:absolute; left:50%; top:-3px; bottom:-3px; width:0; border-left:2px dashed #1f2937; }
  .tug-50::after { content:"50%"; position:absolute; top:-14px; left:-11px; font-size:.6rem; color:#1f2937; }
  .tug-lbls { display:flex; justify-content:space-between; font-size:.72rem; color:#6b7280; margin-top:3px; }
  #panel-chart { height:230px; margin:6px 0 4px; }
  .toolbar { display:flex; align-items:center; gap:8px; margin:10px 0 4px; flex-wrap:wrap; }
  .toolbar .lbl { font-weight:600; font-size:.85rem; margin-right:auto; }
  .toolbar button { font-size:.75rem; padding:4px 9px; border:1px solid #d1d5db; border-radius:6px; background:#fff; cursor:pointer; }
  .toolbar button:hover { background:#f3f4f6; }
  .ptbl { width:100%; border-collapse:collapse; font-size:.78rem; }
  .ptbl th, .ptbl td { padding:5px 6px; border-bottom:1px solid #f0f0f0; text-align:right; vertical-align:middle; }
  .ptbl th:first-child, .ptbl td:first-child { text-align:left; }
  .ptbl th { color:#6b7280; font-weight:600; }
  .ptbl td.edit { text-align:left; min-width:210px; }
  .kswrap { display:flex; align-items:center; gap:4px; font-size:.76rem; }
  .kswrap .kl { color:#C2410C; font-weight:700; } .kswrap .sl { color:#B91C1C; font-weight:700; margin-left:8px; }
  .kswrap .nulo { color:#9ca3af; margin-left:auto; }
  .ptbl input.pct { width:44px; padding:3px 5px; border:1px solid #d1d5db; border-radius:5px; font-size:.78rem; text-align:right; }
  .ptbl input.pct:focus { outline:none; border-color:#2563eb; }
  .ptbl input.pct.edited { border-color:#2563eb; background:#eff6ff; }
  .split { display:flex; height:8px; border-radius:3px; overflow:hidden; min-width:110px; margin-top:5px; }
  .split i { display:block; } .sk{background:#C2410C;} .ss{background:#B91C1C;} .sn{background:#d1d5db;}
  .hint { color:#9ca3af; font-size:.75rem; margin-top:10px; }
  .iar { background:#f8fafc; border:1px solid #e5e7eb; border-radius:8px; padding:8px 10px; margin:8px 0 4px; }
  .iar-hd { font-size:.82rem; }
  .iar-net { color:#6b7280; margin-left:6px; }
  .iar-sl { display:flex; align-items:center; gap:8px; margin-top:6px; font-size:.76rem; color:#374151; }
  .iar-sl input[type=range] { flex:1; max-width:160px; }
  .iar-hint { color:#9ca3af; }
  .iar .lead { background:#1e3a8a; color:#fff; font-size:.66rem; padding:1px 6px; border-radius:4px; }
  .iar-tend { font-size:.78rem; color:#374151; margin-top:4px; }
  #iar-spark { margin-top:2px; }
  details { background:#fff; border:1px solid #e5e7eb; border-radius:10px; margin:0 12px 12px; }
  details > summary { padding:10px 14px; cursor:pointer; font-weight:600; font-size:.9rem; }
  details .body { padding:0 14px 14px; overflow:auto; }
  table.full { border-collapse:collapse; width:100%; font-size:.82rem; }
  table.full th, table.full td { border:1px solid #e5e7eb; padding:5px 9px; text-align:left; }
  table.full th { background:#f9fafb; position:sticky; top:0; }
  .nota { background:#fffbeb; border-left:4px solid #f59e0b; padding:8px 12px; border-radius:6px; font-size:.82rem; color:#92400e; margin:0 12px 14px; }
  @media (max-width:860px){ .wrap{ grid-template-columns:1fr; height:auto; } #mapa{ height:58vh; } }
</style>
<script>__PLOTLYJS__</script>
</head><body>

<header>
  <div>
    <h1>Segunda Vuelta Presidencial — Perú 2026</h1>
    <div class="sub">Keiko Fujimori (FP) vs Roberto Sánchez (JxP) · balotaje 7-jun-2026</div>
  </div>
  <div class="chips">
    <span class="chip k">Keiko __BASE_K__%</span>
    <span class="chip s">Sánchez __BASE_S__%</span>
    <span class="chip meta">Gana __GANADOR__ · +__MARGEN__ pts (base)</span>
    <span class="chip meta">__N_BISAGRA__ bisagra</span>
  </div>
</header>

<div class="wrap">
  <div class="card">
    <div class="hd"><span id="map-hd">Mapa · 🟧 gana Keiko · 🟨 bisagra (se decide) · 🟥 gana Sánchez — clic en un departamento</span>
      <button id="map-back" style="display:none" onclick="render(null)">← Mapa nacional</button></div>
    <div id="mapa"></div>
  </div>
  <div class="card"><div id="panel"></div></div>
</div>

<details><summary>Departamentos bisagra (ordenados por peso electoral)</summary>
  <div class="body">__BISAGRA_TBL__</div></details>
<details><summary>Modelo de transferencia y vertientes (escenario base)</summary>
  <div class="body">__TRANSF_TBL__</div></details>
<details><summary>Índice de Aceptación en Redes por departamento (IAR)</summary>
  <div class="body">__IAR_TBL__</div></details>
<div class="nota">Trasvase de los partidos mayores (Renovación Popular, Buen Gobierno, Obras,
País para Todos, Ahora Nación) de cruces Ipsos may-2026; el resto, heurística por bloque. Ver FUENTES.md.</div>

<script>
const DATA = __DATA__;
const GEO = __GEO__;
const CATCOLOR = __CATCOLOR__;
const CATLABEL = {ancla_keiko:"Ancla Keiko", inclina_keiko:"Inclina Keiko", bisagra:"Bisagra",
                  inclina_sanchez:"Inclina Sánchez", ancla_sanchez:"Ancla Sánchez"};
const ORDEN = ["ancla_keiko","inclina_keiko","bisagra","inclina_sanchez","ancla_sanchez"];
const ESCN = {base:"Base", favK:"Favorable Keiko", favS:"Favorable Sánchez"};
const ALPHA = 0.5, U_ANCLA = 10, U_BIS = 5;
const fmt = n => (n==null?"—":Math.round(n).toLocaleString("es-PE"));
const STATE = {}; let CUR = null;
let PESO_IAR = __PESOIAR__;   // intensidad del Índice de Aceptación en Redes (slider)
const META = DATA.meta;
const clon = o => JSON.parse(JSON.stringify(o));
const textoDark = lab => (lab.includes("Inclina")||lab==="Bisagra");
const tendTxt = t => { const a=Math.round(Math.abs(t)*100);
  if(a<1) return "estable (sin cambio relevante)";
  return (t<0?"moviéndose hacia Sánchez ▼K":"moviéndose hacia Keiko ▲K")+` (${t<0?'−':'+'}${a} pts net)`; };
function drawSpark(serie){
  const el=document.getElementById("iar-spark"); if(!el||!serie||!serie.length) return;
  Plotly.react("iar-spark", [{x:serie.map(p=>p.f), y:serie.map(p=>p.net),
    type:"scatter", mode:"lines+markers", line:{color:"#374151",width:2}, marker:{size:6},
    hovertemplate:"%{x}: neto %{y}<extra></extra>"}],
   {height:96, margin:{l:26,r:6,t:6,b:20},
    yaxis:{range:[-1,1], zeroline:true, zerolinecolor:"#cbd5e1", tickvals:[-1,0,1]},
    xaxis:{type:"category"}, font:{size:9}, showlegend:false}, MAP_CFG);
}

function entrada(key){
  const id = key || "__nac__";
  if(!STATE[id]) STATE[id] = clon(key ? DATA.departamentos[key] : DATA.nacional);
  return STATE[id];
}
// Recalcula los 3 escenarios desde los shares de los partidos y aplica el IAR:
// rompe fraccion·U del pool indeciso (U = peso − vk − vs) hacia el candidato favorecido.
function calcEsc(d){
  const net = d.net || 0, frac = Math.min(1, Math.max(0, PESO_IAR*Math.abs(net)));
  const tally = scn => {
    let vk=0, vs=0;
    for(const p of d.partidos){
      let k=p.k/100, s=p.s/100, n=Math.max(0,1-k-s);
      if(scn==="favK") k+=ALPHA*n; else if(scn==="favS") s+=ALPHA*n;
      vk+=p.votos*k; vs+=p.votos*s;
    }
    const movidos = frac * Math.max(0, d.peso - vk - vs);
    if(net>0) vk+=movidos; else if(net<0) vs+=movidos;
    const dos=(vk+vs)||1;
    return {k:+(vk/dos*100).toFixed(2), s:+(vs/dos*100).toFixed(2),
            margen:+((vk-vs)/dos*100).toFixed(2), ganador: vk>=vs?"keiko":"sanchez"};
  };
  return {base:tally("base"), favK:tally("favK"), favS:tally("favS")};
}
const escDe = (d, key) => key ? calcEsc(d) : d.escNac;
function calcCat(esc){
  const g=new Set([esc.base.ganador,esc.favK.ganador,esc.favS.ganador]);
  const m=esc.base.margen, w=esc.base.ganador;
  if(g.size>1 || Math.abs(m)<U_BIS) return "bisagra";
  return (Math.abs(m)>=U_ANCLA ? "ancla_" : "inclina_")+w;
}
function badgeHTML(catKey){
  if(!catKey) return `<span class="badge" style="background:#374151;color:#fff">Nacional</span>`;
  const lab=CATLABEL[catKey];
  return `<span class="badge" id="badge" style="background:${CATCOLOR[lab]};color:${textoDark(lab)?'#1f2937':'#fff'}">${lab}</span>`;
}

// ── Mapa ───────────────────────────────────────────────────────────────────
const MAP_CFG = {displayModeBar:false, responsive:true};
function mapaNacional(){
  const grupos = {};
  for(const key in DATA.departamentos){
    const c = DATA.departamentos[key].catKey || "bisagra";
    (grupos[c] = grupos[c] || []).push(key);
  }
  const traces = ORDEN.filter(c=>grupos[c]).map(c=>({
    type:"choropleth", geojson:GEO, featureidkey:"properties.KEY",
    locations:grupos[c], z:grupos[c].map(()=>1), showscale:false,
    colorscale:[[0,CATCOLOR[CATLABEL[c]]],[1,CATCOLOR[CATLABEL[c]]]],
    name:`${CATLABEL[c]} (${grupos[c].length})`, showlegend:true, marker:{line:{width:.4,color:"#fff"}},
    hovertemplate:"<b>%{location}</b><br>"+CATLABEL[c]+" · clic para ver el detalle<extra></extra>"
  }));
  Plotly.react("mapa", traces, {
    geo:{fitbounds:"locations", visible:false, bgcolor:"rgba(0,0,0,0)"},
    margin:{l:0,r:0,t:0,b:0}, paper_bgcolor:"rgba(0,0,0,0)",
    legend:{orientation:"h", yanchor:"bottom", y:-0.04, xanchor:"center", x:0.5, font:{size:11}}
  }, MAP_CFG);
  const gd=document.getElementById("mapa");
  gd.removeAllListeners && gd.removeAllListeners("plotly_click");
  gd.on("plotly_click", e=>{ if(e.points&&e.points.length) render(e.points[0].location); });
  document.getElementById("map-hd").textContent =
    "Mapa · 🟧 gana Keiko · 🟨 bisagra (se decide) · 🟥 gana Sánchez — clic en un departamento";
  document.getElementById("map-back").style.display = "none";
}
function mapaDepto(key, catKey){
  const lab = CATLABEL[catKey], nombre = DATA.departamentos[key].nombre;
  const gj = {type:"FeatureCollection", features: GEO.features.filter(f=>f.properties.KEY===key)};
  Plotly.react("mapa", [{
    type:"choropleth", geojson:gj, featureidkey:"properties.KEY",
    locations:[key], z:[1], showscale:false,
    colorscale:[[0,CATCOLOR[lab]],[1,CATCOLOR[lab]]],
    marker:{line:{width:1.2,color:"#fff"}},
    hovertemplate:"<b>"+nombre+"</b><br>"+lab+"<extra></extra>"
  }], {
    geo:{fitbounds:"locations", visible:false, bgcolor:"rgba(0,0,0,0)"},
    margin:{l:0,r:0,t:30,b:0}, paper_bgcolor:"rgba(0,0,0,0)",
    title:{text:nombre+" — "+lab, x:.5, y:.97, font:{size:14}}
  }, MAP_CFG);
  document.getElementById("map-hd").textContent = "Departamento: " + nombre;
  document.getElementById("map-back").style.display = "";
}

// ── Panel ──────────────────────────────────────────────────────────────────
function pintarResultado(b, key, catKey){
  const k=b.k, s=b.s, gan=b.ganador==="keiko"?"Keiko":"Sánchez", cls=b.ganador==="keiko"?"k":"s";
  const tk=document.getElementById("tug-k"), ts=document.getElementById("tug-s");
  tk.style.width=k+"%"; tk.textContent=k.toFixed(1)+"%";
  ts.style.width=s+"%"; ts.textContent=s.toFixed(1)+"%";
  let txt;
  if(!key){
    txt = `<b class="${cls}">${gan}</b> lidera la proyección <b>${Math.max(k,s).toFixed(1)}–${Math.min(k,s).toFixed(1)}</b>. `
        + `Pero <b>${META.nBisagra} departamentos bisagra</b> (amarillos) aún pueden inclinar la elección.`;
  } else {
    const lab = catKey?CATLABEL[catKey]:"";
    txt = `Aquí gana <b class="${cls}">${gan}</b> por <b>${Math.abs(b.margen).toFixed(1)} pts</b> — ${lab}.`
        + (catKey==="bisagra" ? " <b>Puede voltear</b> según el escenario o las redes." : "");
  }
  document.getElementById("takeaway").innerHTML = txt;
}

function tablaPartidos(parts, editable){
  let hayOv = parts.some(p=>p.override);
  let rows = parts.map((p,i)=>{
    const splitBar = `<span class="split"><i class="sk" id="sk${i}" style="width:${p.k}%"></i><i class="ss" id="ss${i}" style="width:${p.s}%"></i><i class="sn" id="sn${i}" style="width:${p.n}%"></i></span>`;
    const mk = p.override ? ' <span title="ajuste propio del departamento" style="color:#2563eb;font-weight:700">▲</span>' : '';
    const baseTag = p.base ? ' <span title="base propia del candidato; no se ajusta" style="font-size:.66rem;color:#6b7280;border:1px solid #e5e7eb;border-radius:4px;padding:0 4px">base fija</span>' : '';
    let celda;
    if(editable && p.editable){
      celda = `<td class="edit">
        <div class="kswrap">
          <span class="kl">K</span><input class="pct" type="number" min="0" max="100" step="1" value="${p.k}" data-i="${i}" data-f="k">%
          <span class="sl">S</span><input class="pct" type="number" min="0" max="100" step="1" value="${p.s}" data-i="${i}" data-f="s">%
          <span class="nulo">Nulo <b id="nv${i}">${p.n}</b>%</span>
        </div>${splitBar}</td>`;
    } else {
      celda = `<td style="text-align:center">${splitBar}</td>`;
    }
    return `<tr><td>${p.partido}${mk}${baseTag}</td>${celda}
            <td id="ak${i}">${fmt(p.aporteK)}</td><td id="as${i}">${fmt(p.aporteS)}</td></tr>`;
  }).join("");
  if(hayOv) rows += `<tr><td colspan="4" style="color:#2563eb;font-size:.72rem;border:0">▲ trasvase ajustado a la idiosincrasia de este departamento</td></tr>`;
  const cab = editable ? "Reparto del voto (editable)" : "→K / →S / →Nulo";
  return `<table class="ptbl"><thead><tr><th>Partido</th>
          <th style="text-align:left">${cab}</th><th>→ Keiko</th><th>→ Sánchez</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function chart(esc){
  const escs=["base","favK","favS"];
  Plotly.react("panel-chart", [
    {x:escs.map(e=>ESCN[e]), y:escs.map(e=>esc[e].k), type:"bar", name:"Keiko",
     marker:{color:"#C2410C"}, text:escs.map(e=>esc[e].k+"%"), textposition:"outside"},
    {x:escs.map(e=>ESCN[e]), y:escs.map(e=>esc[e].s), type:"bar", name:"Sánchez",
     marker:{color:"#B91C1C"}, text:escs.map(e=>esc[e].s+"%"), textposition:"outside"}
  ], {barmode:"group", height:230, yaxis:{range:[0,72],ticksuffix:"%"},
      margin:{l:34,r:8,t:8,b:22}, legend:{orientation:"h",y:1.15}, font:{size:11}}, MAP_CFG);
}
function refrescar(){
  const d = entrada(CUR), esc = calcEsc(d), b = esc.base;
  const ck = CUR ? calcCat(esc) : null;
  document.getElementById("sub").textContent =
    "Proyección de segunda vuelta · escenario base";
  pintarResultado(b, CUR, ck);
  if(CUR){ const lab=CATLABEL[ck], bd=document.getElementById("badge");
           bd.textContent=lab; bd.style.background=CATCOLOR[lab]; bd.style.color=textoDark(lab)?"#1f2937":"#fff";
           mapaDepto(CUR, ck); }
  chart(esc);
}
function onEdit(inp){
  const d = entrada(CUR), i = +inp.dataset.i, f = inp.dataset.f, p = d.partidos[i];
  let val = Math.max(0, Math.min(100, +inp.value||0));
  const other = f==="k" ? p.s : p.k;
  if(val + other > 100){ val = 100 - other; inp.value = val; }
  p[f] = val; p.n = +(100 - p.k - p.s).toFixed(1);
  p.aporteK = Math.round(p.votos*p.k/100); p.aporteS = Math.round(p.votos*p.s/100);
  document.getElementById("nv"+i).textContent = p.n;
  document.getElementById("sk"+i).style.width = p.k+"%";
  document.getElementById("ss"+i).style.width = p.s+"%";
  document.getElementById("sn"+i).style.width = p.n+"%";
  document.getElementById("ak"+i).textContent = fmt(p.aporteK);
  document.getElementById("as"+i).textContent = fmt(p.aporteS);
  inp.classList.add("edited");
  refrescar();
}
function exportar(){
  const filas=[["departamento","tipo","clave","keiko","sanchez","null","nota"]];
  for(const id in STATE){
    if(id==="__nac__") continue;
    const cur=STATE[id], orig=DATA.departamentos[id]; if(!orig) continue;
    cur.partidos.forEach((p,i)=>{
      if(!p.editable) return;
      const o=orig.partidos[i];
      if(p.k!==o.k || p.s!==o.s)
        filas.push([cur.nombre,"partido",p.partido,p.k,p.s,+(100-p.k-p.s).toFixed(1),"ajuste manual dashboard"]);
    });
  }
  if(filas.length===1){ alert("No hay ajustes manuales para exportar."); return; }
  const csv=filas.map(r=>r.map(c=>{c=String(c);return c.includes(",")?'"'+c+'"':c;}).join(",")).join("\n");
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
  a.download="overrides_departamento.csv"; a.click();
}
function restablecer(){ if(CUR){ delete STATE[CUR]; render(CUR); } }

function render(key){
  CUR = key || null;
  const d = entrada(key), esc = escDe(d, key), b = esc.base;
  const catKey = key ? calcCat(esc) : null;
  const gan = b.ganador==="keiko" ? "Keiko" : "Sánchez";
  const toolbar = key ? `<div class="toolbar">
      <span class="lbl">Afinar reparto de este departamento</span>
      <button onclick="restablecer()">Restablecer</button>
      <button onclick="exportar()">Exportar ajustes CSV</button></div>` : "";
  const netTxt = !key ? "" : (d.net>0 ? "favorece a Keiko" : d.net<0 ? "favorece a Sánchez" : "neutro");
  const iarBlock = key ? `<div class="iar">
      <div class="iar-hd">Aceptación en redes (IAR) · <span class="lead">indicador adelantado</span>:
        <b style="color:#C2410C">Keiko ${d.iarK}</b> · <b style="color:#B91C1C">Sánchez ${d.iarS}</b>
        <span class="iar-net">${netTxt} (neto ${d.net>0?'+':''}${Math.round(d.net*100)})</span></div>
      <div class="iar-tend">Tendencia: ${tendTxt(d.tend)}</div>
      <div id="iar-spark"></div>
      <div class="iar-sl"><label>Peso del IAR: <b id="pesoval">${PESO_IAR.toFixed(2)}</b></label>
        <input type="range" id="pesoiar" min="0" max="1" step="0.05" value="${PESO_IAR}">
        <span class="iar-hint">0 = ignorar redes · rompe el voto indeciso hacia quien tiene mejor aceptación</span></div>
    </div>` : "";
  const iarNac = key ? "" : `<div class="iar">
      <div class="iar-hd">IAR Nacional · <span class="lead">indicador adelantado</span> —
        <b style="color:#C2410C">Keiko ${DATA.nacional.iarK}</b> · <b style="color:#B91C1C">Sánchez ${DATA.nacional.iarS}</b>
        <span class="iar-net">(neto ${DATA.nacional.net>0?'+':''}${Math.round(DATA.nacional.net*100)})</span></div>
      <div class="iar-tend">Agrega los 25 departamentos (ponderado por peso electoral) → <b>genera el resultado proyectado de arriba</b>. Tendencia: ${tendTxt(DATA.nacional.tend)}</div>
      <div id="iar-spark"></div></div>`;

  document.getElementById("panel").innerHTML = `
    <h2 class="pnl-title">${d.nombre} ${badgeHTML(catKey)}</h2>
    <div class="pnl-sub" id="sub">Proyección de segunda vuelta · escenario base</div>
    <div class="takeaway" id="takeaway"></div>
    <div class="tug">
      <div class="tug-bar"><div class="tug-seg k" id="tug-k"></div><div class="tug-seg s" id="tug-s"></div><div class="tug-50"></div></div>
      <div class="tug-lbls"><span>● Keiko (FP)</span><span>Sánchez (JxP) ●</span></div>
    </div>
    <div id="panel-chart"></div>
    ${iarBlock}${iarNac}
    <div style="font-weight:600;font-size:.85rem;margin:6px 0 2px">¿De dónde viene cada voto?
      ${key ? '<span style="font-weight:400;color:#6b7280">— mueve los % para afinar</span>' : '(escenario base)'}</div>
    ${toolbar}
    ${tablaPartidos(d.partidos, !!key)}
    ${key ? '<div class="hint" id="volver">↩ volver a la vista nacional</div>'
          : '<div class="hint">Vista nacional. Clic en un departamento del mapa para ver y afinar su detalle.</div>'}`;

  if(key){
    document.getElementById("volver").style.cursor="pointer";
    document.getElementById("volver").onclick=()=>render(null);
    document.querySelectorAll("#panel input.pct").forEach(inp=>inp.addEventListener("input",()=>onEdit(inp)));
    const sl=document.getElementById("pesoiar");
    sl.addEventListener("input", ()=>{ PESO_IAR=+sl.value;
      document.getElementById("pesoval").textContent=PESO_IAR.toFixed(2); refrescar(); });
    mapaDepto(key, catKey);
  } else {
    mapaNacional();
  }
  pintarResultado(b, key, catKey);
  chart(esc);
  drawSpark(key ? d.hist : DATA.nacional.hist);
}

window.addEventListener("load", ()=>{ render(null); });
</script>
</body></html>"""
