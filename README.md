# Análisis Segunda Vuelta Presidencial — Perú 2026

Proyección departamental del balotaje del **7 de junio de 2026** entre
**Keiko Fujimori (Fuerza Popular)** y **Roberto Sánchez (Juntos por el Perú)**.

Parte del resultado real de 1ra vuelta de ONPE por departamento y modela hacia dónde se
mueve el voto de los partidos eliminados, para responder cuatro preguntas:

1. ¿De qué **vertiente** ideológica eran los partidos que perdieron?
2. ¿Hacia qué finalista se inclinan sus votantes?
3. ¿Cuáles son los **departamentos ancla** de cada candidato (ganados con holgura)?
4. ¿Cuáles son los **departamentos bisagra** (donde se decide la elección)?

> No es un pronóstico cerrado. Es un mapa de quién parte con ventaja y dónde está la disputa,
> con la incertidumbre hecha explícita mediante escenarios.

## Metodología

1. **Base** — votos por partido y departamento en 1ra vuelta (`data/primera_vuelta_departamentos.json`).
2. **Vertientes** — cada partido se asigna a un bloque ideológico (`data/vertientes.csv`).
3. **Transferencia** — % del voto de cada partido eliminado que va a Keiko / Sánchez /
   blanco-nulo (`data/transferencias.csv`). Los mayores usan cruces de **Ipsos (mayo 2026)**;
   la cola usa heurística por bloque. Ver [`FUENTES.md`](FUENTES.md). La base propia de los
   finalistas (Fuerza Popular→Keiko, Juntos por el Perú→Sánchez) es **fija**: solo se modela
   el trasvase de los partidos que perdieron.
4. **Overrides por departamento** — cada región tiene su idiosincrasia. `data/overrides_departamento.csv`
   permite ajustar el trasvase por `depto+partido` o `depto+bloque`. Resolución de más a menos
   específico: `depto+partido` → `depto+bloque` → matriz nacional → default neutral. Archivo
   opcional: si no existe, el trasvase es uniforme.
5. **Escenarios** — `base`, `favorable-Keiko`, `favorable-Sánchez`. Difieren solo en cómo se
   rompe el voto indeciso/blanco (la mitad se inclina al candidato favorecido). Transparente
   y conservador.
6. **Proyección** — por departamento y escenario: `votos = Σ partido × % trasvase`.
7. **Índice de Aceptación en Redes (IAR)** — señal de noticias/redes por departamento
   (`data/indice_redes.csv`, snapshot; `data/social_signals.csv` opcional). El IAR **rompe el
   voto indeciso** del departamento hacia el candidato con mejor aceptación, **acotado por el
   tamaño del pool de indecisos** (no inventa votos). Intensidad con peso configurable (`PESO_IAR`,
   def. 0.5; slider en el dashboard). Ver [`FUENTES.md`](FUENTES.md).
8. **Clasificación**:
   - **Ancla (de un candidato)**: gana en los 3 escenarios con margen base ≥ 10 pts.
   - **Bisagra**: el ganador cambia entre escenarios, o el margen base es < 5 pts.
   - **Inclina**: ganador estable con margen base entre 5 y 10 pts.

## Cómo correr

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (source venv/bin/activate en Unix)
pip install -r requirements.txt
python main.py
```

Genera dos salidas en la raíz:

- **`informe.html`** — dashboard interactivo y autocontenido (Plotly y GeoJSON embebidos,
  funciona offline). Ábrelo en el navegador.
- **`resultados.json`** — todos los números (proyección y clasificación por departamento).

## Dashboard interactivo (`informe.html`)

- **Mapa nacional** coloreado por categoría (Ancla Keiko / Inclina / Bisagra / Ancla Sánchez).
- **Clic en un departamento** → el mapa se enfoca en su forma y el panel muestra su
  distribución de voto: proyección base, los 3 escenarios y de qué partido de 1ra vuelta
  viene cada finalista.
- **Afinado en vivo** — en el panel del departamento puedes editar el reparto →Keiko/→Sánchez
  de cada partido eliminado; las tarjetas, los escenarios, la categoría y el color del mapa
  se recalculan al instante. La base de los finalistas queda fija ("base fija").
- **Índice de Aceptación en Redes (indicador adelantado)** — el panel muestra el IAR (Keiko vs
  Sánchez), su **tendencia** y un **sparkline** de la serie temporal, más un **slider de peso**
  que rompe el voto indeciso según las redes y recalcula todo en vivo (peso 0 = modelo puro).
  El IAR se monitorea de forma recurrente (ver [`MONITOREO.md`](MONITOREO.md)).
- **Exportar ajustes CSV** — descarga tus cambios en el formato de `overrides_departamento.csv`
  para pegarlos en `data/` y volverlos permanentes. **Restablecer** vuelve al modelo.

## Estructura

```
data/        snapshot 1ra vuelta, GeoJSON, vertientes, matriz de transferencia,
             overrides_departamento.csv, indice_redes.csv (IAR) e indice_historial.csv
             (serie temporal); social_signals.csv opcional (adaptador de redes)
src/         carga, transferencia, proyección, clasificación, índice de redes, reporte
main.py      pipeline completo + chequeos de integridad
MONITOREO.md cómo re-medir el IAR de forma recurrente (indicador adelantado)
FUENTES.md   encuestas, endosos, IAR y notas metodológicas (con URLs)
```

## Limitaciones

- El trasvase es el supuesto más sensible; por eso van 3 escenarios, overrides por departamento
  y se documentan fuentes.
- Salvo Lima, no hay encuestas departamentales de 2da vuelta: por defecto el trasvase es
  uniforme y la heterogeneidad geográfica proviene del **mix de partidos de 1ra vuelta de cada
  departamento** (dato duro). Los overrides permiten introducir idiosincrasia local conocida.
- El **IAR es un proxy de noticias** (snapshot fechado) + adaptador social opcional; no es
  escucha en vivo de X/Meta. El sentimiento es heurístico; reemplazable por datos medidos vía
  `social_signals.csv`.
- Datos de encuestas posteriores a abril-2026; sujetos a revisión si ONPE/encuestadoras actualizan.
