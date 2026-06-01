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
   la cola usa heurística por bloque. Ver [`FUENTES.md`](FUENTES.md).
4. **Escenarios** — `base`, `favorable-Keiko`, `favorable-Sánchez`. Difieren solo en cómo se
   rompe el voto indeciso/blanco (la mitad se inclina al candidato favorecido). Transparente
   y conservador.
5. **Proyección** — por departamento y escenario: `votos = Σ partido × % trasvase`.
6. **Clasificación**:
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

- **`informe.html`** — informe autocontenido: mapa Ancla/Bisagra, proyección nacional por
  escenario, ranking de departamentos bisagra y tabla de transferencia. Ábrelo en el navegador.
- **`resultados.json`** — todos los números (proyección y clasificación por departamento).

## Estructura

```
data/      snapshot 1ra vuelta, GeoJSON, vertientes y matriz de transferencia
src/       carga, transferencia, proyección, clasificación, reporte
main.py    pipeline completo + chequeos de integridad
FUENTES.md encuestas, endosos y notas metodológicas (con URLs)
```

## Limitaciones

- El trasvase es el supuesto más sensible; por eso van 3 escenarios y se documentan fuentes.
- Salvo Lima, no hay encuestas departamentales de 2da vuelta: el trasvase se aplica uniforme
  a nivel nacional y la heterogeneidad geográfica proviene del **mix de partidos de 1ra vuelta
  de cada departamento**, que sí es dato duro.
- Datos de encuestas posteriores a abril-2026; sujetos a revisión si ONPE/encuestadoras actualizan.
