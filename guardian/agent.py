#!/usr/bin/env python3
"""
Agente Guardian — Verificador de Lógica de Despacho
qwen2.5-coder:7b (Ollama) → genera Pytest → ejecuta en Docker → veredicto auditable.

Nota: qwen2.5-coder:7b no emite structured tool calls vía Ollama; devuelve JSON como
texto plano. run_agent_loop intercepta ese JSON, ejecuta la herramienta y devuelve el
resultado al modelo para continuar con el siguiente paso.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

MODEL        = "qwen2.5-coder:7b"
BASE_DIR     = Path(__file__).parent          # guardian/
PROJECT_ROOT = BASE_DIR.parent                # raíz del proyecto

CASOS_FILE   = PROJECT_ROOT / "casos_prueba.md"
ENGINE_FILE  = PROJECT_ROOT / "engine.py"
TESTS_FILE   = PROJECT_ROOT / "test_generated.py"
VERDICT_FILE = BASE_DIR / "veredicto.json"
DOCKER_IMAGE = "guardian-sandbox"             # debe coincidir con guardian/sandbox.py

llm = ChatOllama(model=MODEL, temperature=0, num_ctx=8192)

# ─── TOOLS ────────────────────────────────────────────────────────────────────

@tool
def leer_engine() -> str:
    """Lee el código fuente de engine.py y devuelve su contenido completo."""
    if not ENGINE_FILE.exists():
        return "ERROR: engine.py no encontrado en la raíz del proyecto."
    return ENGINE_FILE.read_text(encoding="utf-8")


@tool
def leer_casos_prueba() -> str:
    """Lee el archivo casos_prueba.md y devuelve su contenido completo."""
    if not CASOS_FILE.exists():
        return "ERROR: casos_prueba.md no encontrado en la raíz del proyecto."
    return CASOS_FILE.read_text(encoding="utf-8")


@tool
def guardar_tests(codigo: str) -> str:
    """
    Escribe el código Python/Pytest recibido en test_generated.py en la raíz del proyecto.
    El código debe importar gestionar_despacho desde engine y cubrir los 10 escenarios de validación TC-01 a TC-10,
    verificando FEFO, bloqueo de seguridad (R2) y StockInsuficienteError (R3).
    """
    TESTS_FILE.write_text(codigo, encoding="utf-8")
    lineas = len(codigo.splitlines())
    return f"test_generated.py guardado ({lineas} líneas) en {TESTS_FILE}."


@tool
def construir_imagen_docker() -> str:
    """
    Construye la imagen Docker llamada 'guardian-sandbox' usando Dockerfile.guardian.
    Prerequisito: test_generated.py debe existir antes de llamar esta herramienta.
    """
    if not TESTS_FILE.exists():
        return "ERROR: test_generated.py no existe. Usa guardar_tests primero."

    resultado = subprocess.run(
        ["docker", "build", "-f", "Dockerfile.guardian", "-t", DOCKER_IMAGE, "."],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),   # contexto Docker = raíz del proyecto
        timeout=120,
    )
    if resultado.returncode != 0:
        return f"ERROR al construir entorno Docker de pruebas aislado:\n{resultado.stderr[-1000:]}"
    return f"Imagen '{DOCKER_IMAGE}' construida exitosamente."


@tool
def ejecutar_tests_docker() -> str:
    """
    Ejecuta pytest dentro del contenedor Docker aislado y devuelve la salida completa.
    Prerequisito: la imagen Docker guardian-sandbox debe estar construida.
    """
    resultado = subprocess.run(
        ["docker", "run", "--rm", "--name", "guardian-run", DOCKER_IMAGE],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(PROJECT_ROOT),
    )
    salida = (resultado.stdout + resultado.stderr).strip()
    return salida if salida else "Sin salida del contenedor Docker."


@tool
def guardar_veredicto(resumen: str) -> str:
    """
    Guarda el veredicto final en veredicto.json con metadatos de auditoría.
    Recibe un resumen en texto plano con: total tests, pasados, fallidos y conclusión.
    """
    payload = {
        "timestamp":        datetime.now().isoformat(),
        "modelo_ia":        MODEL,
        "origen_casos":     str(CASOS_FILE),
        "engine_auditado":  str(ENGINE_FILE),
        "tests_generados":  str(TESTS_FILE),
        "imagen_docker":    DOCKER_IMAGE,
        "resumen_agente":   resumen,
    }
    VERDICT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return f"Veredicto auditable guardado en {VERDICT_FILE.name}"


# ─── PROMPT DEL AGENTE ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres el Agente Guardian de la UMB, un auditor automatizado del motor de despacho de productos perecederos.

Tienes acceso a estas herramientas: leer_engine, leer_casos_prueba, guardar_tests, construir_imagen_docker, ejecutar_tests_docker, guardar_veredicto.

Para llamar una herramienta responde ÚNICAMENTE con un JSON válido en este formato exacto:
{"name": "nombre_herramienta", "arguments": {"param": "valor"}}

No agregues texto antes ni después del JSON. Cuando no necesites llamar más herramientas, responde en texto libre con el veredicto final.

Tu misión es ejecutar el siguiente flujo completo en orden estricto:

PASO 1 — Leer el motor de despacho
  Llama leer_engine para obtener el código fuente de engine.py.
  Identifica la firma de gestionar_despacho, las excepciones que lanza
  (StockInsuficienteError, FechaInvalidaError) y las cuatro reglas de negocio:
  R1 FEFO, R2 bloqueo de seguridad de 3 días, R3 validación de stock, R4 filtrado combinado.

PASO 2 — Leer casos de prueba
  Llama leer_casos_prueba para obtener los 10 escenarios documentados en casos_prueba.md (TC-01 a TC-10).

PASO 3 — Generar código Pytest
  Analiza el motor y los casos leídos. Genera un archivo Python con EXACTAMENTE 10 funciones test_
  (una por cada caso TC-01 a TC-10, sin omitir ninguna). El archivo debe empezar con:
    import pytest
    from engine import gestionar_despacho
    from domain.exceptions import StockInsuficienteError, FechaInvalidaError

  Reglas estrictas para cada test:
  - Casos de despacho exitoso (TC-01, TC-02, TC-03, TC-04, TC-07, TC-08, TC-10):
      resultado = gestionar_despacho([...], pedido, fecha)
      assert len(resultado) == <n_lotes_esperados>
      assert resultado[0]["id_lote"] == "..."
      assert resultado[0]["cantidad_utilizada"] == <valor>
      assert resultado[0]["saldo_restante"] == <valor>
  - Casos de error (TC-05, TC-06, TC-09): USA SIEMPRE pytest.raises, NUNCA try/except:
      with pytest.raises(StockInsuficienteError) as exc_info:
          gestionar_despacho([...], pedido, fecha)
      assert "Stock Insuficiente" in str(exc_info.value)

  Llama guardar_tests con el código completo como argumento "codigo".
  IMPORTANTE: genera los 10 tests completos antes de llamar guardar_tests.

PASO 4 — Construir imagen Docker
  Llama construir_imagen_docker para empaquetar el proyecto y los tests generados.

PASO 5 — Ejecutar tests en Docker
  Llama ejecutar_tests_docker para correr pytest en el contenedor aislado guardian-sandbox.
  Analiza la salida: cuántos pasaron, cuántos fallaron.

PASO 6 — Guardar veredicto auditable
  Llama guardar_veredicto con un resumen que incluya: total tests, pasados, fallidos, lista de fallidos y conclusión APROBADO/RECHAZADO.

Ejecuta una herramienta a la vez. Espera el resultado antes de continuar con el siguiente paso."""

# ─── LOOP MANUAL DE TOOL CALLING ─────────────────────────────────────────────

def _parsear_tool_call(texto: str) -> tuple[str, dict] | None:
    """Extrae nombre y argumentos del primer JSON de tool call en el texto del modelo."""
    # Elimina fences de Markdown (```json ... ``` o ``` ... ```)
    limpio = re.sub(r'```(?:json)?\s*', '', texto).strip()
    limpio = re.sub(r'```', '', limpio).strip()

    # Intenta parsear el texto limpio directamente como JSON
    try:
        data = json.loads(limpio)
        if isinstance(data, dict) and "name" in data:
            return data["name"], data.get("arguments", {})
    except (json.JSONDecodeError, ValueError):
        pass

    # Regex con soporte para un nivel de anidamiento en "arguments": {}
    for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', texto, re.DOTALL):
        try:
            data = json.loads(match.group())
            if isinstance(data, dict) and "name" in data:
                return data["name"], data.get("arguments", {})
        except (json.JSONDecodeError, ValueError):
            continue

    return None


def run_agent_loop(user_input: str, max_iterations: int = 15) -> str:
    """
    Loop de ejecución que parsea tool calls desde texto plano y las ejecuta manualmente.
    Necesario porque qwen2.5-coder:7b no emite structured tool calls via Ollama.
    """
    mensajes = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_input)]

    for i in range(max_iterations):
        respuesta = llm.invoke(mensajes)
        contenido = respuesta.content.strip()

        parsed = _parsear_tool_call(contenido)
        if not parsed:
            # No hay tool call: el modelo emitió su respuesta final
            return contenido

        nombre, args = parsed
        print(f"\n> [{i+1}] Herramienta: {nombre}")

        if nombre not in _TOOLS_MAP:
            resultado = f"ERROR: herramienta '{nombre}' no registrada."
        else:
            try:
                resultado = str(_TOOLS_MAP[nombre].invoke(args))
            except Exception as exc:
                resultado = f"ERROR al ejecutar '{nombre}': {exc}"

        preview = resultado[:400] + ("..." if len(resultado) > 400 else "")
        print(f"    Resultado: {preview}")

        mensajes.append(AIMessage(content=contenido))
        mensajes.append(HumanMessage(content=f"Resultado de {nombre}: {resultado}"))

    return "Límite de iteraciones alcanzado sin respuesta final del agente."


# ─── CONSTRUCCIÓN DEL AGENTE ──────────────────────────────────────────────────

tools = [
    leer_engine,
    leer_casos_prueba,
    guardar_tests,
    construir_imagen_docker,
    ejecutar_tests_docker,
    guardar_veredicto,
]

_TOOLS_MAP = {t.name: t for t in tools}

# ─── PUNTO DE ENTRADA ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    separador = "=" * 65

    print(separador)
    print("  AGENTE GUARDIAN — UMB")
    print(f"  Modelo : {MODEL} via Ollama")
    print(f"  Fecha  : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(separador)

    try:
        veredicto = run_agent_loop(
            "Ejecuta el flujo completo: lee engine.py y casos_prueba.md, genera los tests "
            "Pytest cubriendo los 10 escenarios de validación (FEFO, bloqueo de seguridad y stock "
            "insuficiente), guárdalos, construye la imagen Docker, ejecuta los tests y "
            "guarda el veredicto auditable."
        )

        print(f"\n{separador}")
        print("VEREDICTO DEL AGENTE GUARDIAN:")
        print(separador)
        print(veredicto)
        print(separador)

        if VERDICT_FILE.exists():
            print(f"\nArchivo de auditoría generado: {VERDICT_FILE}")

    except KeyboardInterrupt:
        print("\nEjecución interrumpida por el usuario.")
        sys.exit(0)
    except Exception as exc:
        print(f"\nERROR en el Agente Guardian: {exc}", file=sys.stderr)
        sys.exit(1)
