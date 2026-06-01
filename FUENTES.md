# Fuentes

Datos y supuestos del análisis de segunda vuelta Perú 2026 (Keiko Fujimori vs Roberto Sánchez, 7-jun-2026).

## Resultado de primera vuelta (base de cálculo)

- **ONPE** — resultados presidenciales por departamento, capturados por el proyecto
  `peru-elecciones-2026`. Snapshot en `data/primera_vuelta_departamentos.json`.
- Confirmación de finalistas y márgenes:
  - [Al Jazeera — Peru confirms Fujimori and Sánchez advance to runoff](https://www.aljazeera.com/news/2026/5/17/peruvian-authorities-confirm-fujimori-and-sanchez-advance-to-runoff)
  - [Washington Post — June 7 runoff Fujimori vs Sánchez](https://www.washingtonpost.com/world/2026/05/17/peru-elections-results-second-round/09a67090-5200-11f1-9c40-7a0a12d9e745_story.html)
  - [2026 Peruvian general election — Wikipedia](https://en.wikipedia.org/wiki/2026_Peruvian_general_election)

## Transferencia de votos (cruces por voto de 1ra vuelta — Ipsos, mayo 2026)

Usados para el escenario base de los partidos mayores:

| Partido (candidato) | → Keiko | → Sánchez | Resto (blanco/nulo/no precisa) |
|---|---|---|---|
| Renovación Popular (López Aliaga) | 62% | 18% | 20% |
| Buen Gobierno (Nieto) | 33% | 31% | 36% |
| Cívico Obras (Belmont) | 14% | 52% | 34% |
| País para Todos (Álvarez) | 47% | 30% | 23% |
| Ahora Nación (López Chau) | 16% | 63% | 21% |

Fuentes:
- [Infobae — Ipsos: votantes de López Aliaga y de Nieto en 2da vuelta (31-may-2026)](https://www.infobae.com/peru/2026/05/31/los-votantes-de-rafael-lopez-aliaga-que-apoyaran-a-roberto-sanchez-y-los-de-jorge-nieto-que-respaldaran-a-keiko-fujimori-en-segunda-vuelta/)
- [Ipsos / Perú21 — Última encuesta publicable segunda vuelta (mayo 2026)](https://www.ipsos.com/es-pe/ultima-encuesta-publicable-segunda-vuelta-encuesta-peru-21-ipsos-mayo-2026)
- [Infobae — Ipsos: Keiko gana en Lima 52,2%, Sánchez domina el Perú rural 53,9% (31-may-2026)](https://www.infobae.com/peru/2026/05/31/ultima-encuesta-ipsos-keiko-fujimori-gana-en-lima-con-522-pero-roberto-sanchez-domina-el-peru-rural-con-539/)

## Endosos y alineamientos

- **Ahora Nación (López Chau)**: endosó a **Sánchez**.
- **Renovación Popular (López Aliaga)**: pidió no votar por Sánchez ni en blanco → señal pro **Keiko**.
- **País para Todos (Álvarez)**: el partido **no endosa** a ninguno.
- **Primero la Gente (Pérez Tello)**: llamó a votar **nulo**.
  - [Gestión — Partidos que apoyan a Keiko y a Sánchez](https://gestion.pe/peru/politica/elecciones-2026-los-partidos-que-apoyan-a-keiko-fujimori-y-roberto-sanchez-noticia/)

## Geografía electoral / regiones bisagra

- [Infobae — Las regiones que definirán la presidencia el 7 de junio (15-may-2026)](https://www.infobae.com/peru/2026/05/15/segunda-vuelta-2026-las-regiones-que-definiran-la-presidencia-el-7-de-junio/)
- [Infobae — El rol clave de Lima y Arequipa (20-may-2026)](https://www.infobae.com/peru/2026/05/20/quienes-definiran-la-segunda-vuelta-en-peru-el-rol-clave-de-lima-y-arequipa-en-estas-elecciones-2026-segun-analista/)

## Encuestas nacionales de balotaje (para sanity check)

- CPI (29-may): Keiko 32,5% vs Sánchez 29,1% (empate técnico). [RPP](https://rpp.pe/politica/elecciones/encuesta-cpi-segunda-vuelta-2026-keiko-fujimori-325-vs-roberto-sanchez-291-intencion-de-voto-por-regiones-noticia-1690615) · [Infobae](https://www.infobae.com/peru/2026/05/29/cpi-a-nueve-dias-de-la-segunda-vuelta-keiko-fujimori-con-ligera-ventaja-sobre-roberto-sanchez-con-un-226-dispuesto-a-votar-en-blanco/)
- Ipsos (31-may): en votos válidos **Keiko 51,4% vs Sánchez 48,6%**.
- Datum (30-may): **Keiko 52,9% vs Sánchez 47,1%** (válidos). [Infobae](https://www.infobae.com/peru/2026/05/22/ultima-encuesta-datum-keiko-fujimori-lidera-con-395-frente-a-roberto-sanchez-con-361-a-dos-semanas-del-balotaje/)

## Índice de Aceptación en Redes (IAR) — snapshot 1-jun-2026

El IAR por departamento (`data/indice_redes.csv`) combina patrón regional (Ipsos) con noticias
recientes. Señales usadas:

- **Debate 31-may-2026**: Sánchez con mejor desempeño → momentum reciente a su favor.
  [La República](https://larepublica.pe/politica/2026/05/31/debate-presidencial-2026-en-vivo-a-que-hora-y-por-donde-ver-el-keiko-fujimori-vs-roberto-sanchez-hnews-2425531) · [Infobae](https://www.infobae.com/peru/2026/05/31/debate-presidencial-2026-hoy-en-vivo-minuto-a-minuto-del-ultimo-cara-a-cara-de-keiko-fujimori-y-roberto-sanchez-este-31-de-mayo/)
- **Antivoto/rechazo a Keiko** (~48%, marchas, colectivos): alta carga negativa en redes.
  [Infobae — rechazo LGBTI](https://www.infobae.com/peru/2026/06/01/colectivo-lgbti-declara-su-rechazo-a-keiko-fujimori-en-segunda-vuelta-y-llama-a-un-voto-critico-y-vigilante/)
- **Gira de cierre de Sánchez en el sur** (Arequipa 1-jun, Cusco 2-jun, Puno 3-jun "Cierre Sur Andino"):
  refuerza su aceptación en el sur andino.
  [Infobae — cierre de campaña](https://www.infobae.com/peru/2026/05/29/cierre-de-campana-de-roberto-sanchez-fecha-hora-y-lugar/) · [La República](https://larepublica.pe/politica/2026/05/29/roberto-sanchez-alista-cierre-de-campana-en-el-sur-del-pais-y-en-lima-hnews-2097744)
- **Distribución regional** (Ipsos): Keiko fuerte en Lima/Callao y costa norte/oriente; Sánchez
  domina sur andino y rural. [Infobae](https://www.infobae.com/peru/2026/05/31/ultima-encuesta-ipsos-keiko-fujimori-gana-en-lima-con-522-pero-roberto-sanchez-domina-el-peru-rural-con-539/)

El `net` por departamento es juicio del autor a partir de esa evidencia (no medición directa de
redes). El adaptador `data/social_signals.csv` permite sustituirlo por métricas reales de social
listening. El IAR solo **rompe el voto indeciso** del departamento, acotado por su tamaño.

## Nota metodológica sobre la cola de partidos

Los partidos menores (<3%) sin cruce de encuesta se clasificaron por **bloque ideológico**
(`data/vertientes.csv`) y se les asignó un trasvase heurístico. Su peso combinado es bajo y
tiende a compensarse, por lo que no altera el panorama departamental. Las filas marcadas
`heurística por bloque` en `data/transferencias.csv` son juicio del autor, no dato de encuesta.
