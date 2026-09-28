# claude-notebooklm-research

**Investigación con fuentes para agentes de código: Claude Code + Google NotebookLM por MCP, con citas trazables y una persona en el circuito.**

[Read in English](README.md)

Un agente de IA que escribe código completa un hueco con un número plausible sin dudarlo. En la mayoría del software eso es un problema de estilo; en un simulador físico, un modelo de precios o cualquier cosa que alguien tenga que defender, es un problema de corrección. Este repositorio describe una arquitectura —y trae un kit que funciona— donde el agente responde desde un **corpus curado** (un notebook de NotebookLM), **cita** lo que encontró, **lo dice** cuando el corpus no lo tiene, y **pregunta antes** de modificar el corpus.

## Qué hay

| Carpeta | Qué es |
|---|---|
| [`spec/`](spec/architecture.md) | La arquitectura (v0.2): chat de decisiones → orquestador → agentes → herramienta de investigación, ocho reglas, contratos de tareas y resultados, y diagramas Mermaid. La spec está en inglés; el original se escribió en castellano. |
| [`kit/`](kit/README.md) | Lo que corre hoy: un bloque de `CLAUDE.md` y una skill `/research` que hacen que Claude Code siga la spec contra un notebook de NotebookLM. |
| [`case-study/`](case-study/galpon.md) | Cómo se usó en Galpón, un simulador de planta de procesos donde cada constante física lleva su fuente y una etiqueta de firmeza. |

## Las ideas que importan

- **Dos operaciones, dos decisiones.** Preguntarle al corpus (`chat`) y buscar fuentes nuevas (`research`) son movimientos distintos; el agente elige uno por paso.
- **Trazabilidad (R7).** Cada hallazgo apunta a una cita que devolvió NotebookLM. Si la herramienta no devuelve un campo, el agente lo omite en vez de inventarlo.
- **"No está en las fuentes" es una respuesta válida.** El agente separa lo que dice el corpus de lo que agrega por su cuenta.
- **El corpus cambia sólo con aprobación (R8).** Importar fuentes modifica el notebook del usuario; nunca es la continuación automática de una búsqueda.
- **La procedencia termina en el código.** Una constante investigada nombra su fuente; una elegida dice que fue elegida.

## Instalación

Los pasos están en el [README en inglés](README.md#quick-start) y en [kit/README.md](kit/README.md): instalar `notebooklm-py`, loguearse, registrar el MCP en Claude Code, y copiar el bloque de `CLAUDE.md` y la skill.

## Créditos

El servidor MCP es [notebooklm-py](https://github.com/teng-lin/notebooklm-py), de Teng Lin (MIT). Opera NotebookLM a través de su sesión web, no de una API oficial de Google; este repositorio no lo incluye ni lo modifica.
