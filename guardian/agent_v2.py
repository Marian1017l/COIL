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
ENGINE_FILE  = PROJECT_ROOT / "engine_v2.py"
TESTS_FILE   = PROJECT_ROOT / "test_generated.py"
VERDICT_FILE = BASE_DIR / "veredicto.json"
DOCKER_IMAGE = "guardian-sandbox"             # debe coincidir con guardian/sandbox.py

llm = ChatOllama(model=MODEL, temperature=0, num_ctx=8192)

# ─── TOOLS ────────────────────────────────────────────────────────────────────

@tool
def leer_engine() -> str:
    """Lee el código fuente de engine_v2.py y devuelve su contenido completo."""
    if not ENGINE_FILE.exists():
        return "ERROR: engine_v2.py no encontrado en la raíz del proyecto."
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
    El código debe importar gestionar_despacho desde engine_v2 y cubrir los 10 escenarios de validación TC-01 a TC-10,
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
    """Ejecuta los tests usando el sandbox del proyecto."""
    import json
    import sandbox  # Importación directa porque son archivos hermanos
    
    res = sandbox.ejecutar_en_sandbox()
    return json.dumps(res)


@tool
def guardar_veredicto(resumen: str, passed: int, failed: int, bugs_detectados: int) -> str:
    """
    Guarda el veredicto final en veredicto.json con metadatos de auditoría.
    Args:
        resumen: texto con lista de tests fallidos y conclusión.
        passed: número de tests que pasaron (tomado del resultado de ejecutar_tests_docker).
        failed: número de tests que fallaron.
        bugs_detectados: número de bugs detectados (= failed + errores de colección).
    """
    veredicto = "APROBADO" if bugs_detectados == 0 and passed > 0 else "RECHAZADO"
    payload = {
        "timestamp":        datetime.now().isoformat(),
        "modelo_ia":        MODEL,
        "origen_casos":     str(CASOS_FILE),
        "engine_auditado":  str(ENGINE_FILE),
        "tests_generados":  str(TESTS_FILE),
        "imagen_docker":    DOCKER_IMAGE,
        "passed":           passed,
        "failed":           failed,
        "bugs_detectados":  bugs_detectados,
        "veredicto":        veredicto,
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
  Llama leer_engine para obtener el código fuente de engine_v2.py.
  Identifica la firma de gestionar_despacho, las excepciones que lanza
  (StockInsuficienteError, FechaInvalidaError) y las cuatro reglas de negocio:
  R1 FEFO, R2 bloqueo de seguridad de 3 días, R3 validación de stock, R4 filtrado combinado.

PASO 2 — Leer casos de prueba
  Llama leer_casos_prueba para obtener los 10 escenarios documentados en casos_prueba.md (TC-01 a TC-10).

PASO 3 — Generar código Pytest
  Genera un archivo Python con EXACTAMENTE 10 funciones test_ (TC-01 a TC-10). Empieza con:
    import pytest
    from engine_v2 import gestionar_despacho
    from domain.exceptions import StockInsuficienteError, FechaInvalidaError

  REGLA DE ORO: pytest.raises SOLO cuando el stock de lotes NO BLOQUEADOS es menor que el pedido.
  Un lote bloqueado se OMITE — si los demás cubren el pedido, el despacho ES EXITOSO (usa assert).

  Instrucciones por caso (inventario, pedido → resultado esperado):
    TC-01 assert 1-lote  : [A:10u/2025-06-20, B:10u/2025-07-10], p=5  → A cant=5 saldo=5
    TC-02 assert 2-lotes : [A:5u/2025-06-15, B:10u/2025-07-01], p=10  → A:5/0, B:5/5
    TC-03 assert 1-lote  : [A:10u/2025-06-04(BLOQUEADO), B:10u/2025-06-20], p=5  → B cant=5 saldo=5
    TC-04 assert 1-lote  : [A:8u/2025-06-02(BLOQUEADO), B:8u/2025-06-25], p=3   → B cant=3 saldo=5
    TC-05 pytest.raises  : [A:5u/2025-06-20, B:5u/2025-07-10], p=20 → StockInsuficienteError
    TC-06 pytest.raises  : [A:10u/2025-06-02(BLOQUEADO), B:10u/2025-06-03(BLOQUEADO)], p=5 → StockInsuficienteError
    TC-07 assert 1-lote  : [A:10u/2025-06-03(BLOQUEADO), B:10u/2025-06-30], p=10 → B cant=10 saldo=0
    TC-08 assert 3-lotes : [A:3u/2025-06-10, B:4u/2025-06-18, C:10u/2025-07-05], p=12 → A:3/0, B:4/0, C:5/5
    TC-09 pytest.raises  : [], p=5 → StockInsuficienteError
    TC-10 assert 2-lotes : [A:10u/2025-06-04(BLOQUEADO), B:4u/2025-06-15, C:10u/2025-06-28], p=6 → B:4/0, C:2/8

  TC-03/04/07/10: el lote BLOQUEADO se salta, el siguiente cubre el pedido. NUNCA pytest.raises.
  TC-05: stock=5 por lote (total=10 < pedido=20). Con stock=10 la excepción NO se lanza (20<20 es False).

  Patrón assert:
      resultado = gestionar_despacho([...], pedido, fecha)
      assert len(resultado) == N
      assert resultado[i]["id_lote"] == "X"
      assert resultado[i]["cantidad_utilizada"] == VAL
      assert resultado[i]["saldo_restante"] == VAL

  Patrón pytest.raises:
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
  Llama guardar_veredicto con los valores exactos del resultado de ejecutar_tests_docker:
    - resumen: texto con lista de tests fallidos (o "ninguno") y conclusión APROBADO/RECHAZADO.
    - passed: el valor numérico de "passed" del resultado del sandbox.
    - failed: el valor numérico de "failed" del resultado del sandbox.
    - bugs_detectados: el valor numérico de "bugs_detectados" del resultado del sandbox.
    
CRÍTICO: NUNCA termines con texto libre después de ejecutar_tests_docker.
El ÚNICO camino válido es llamar guardar_veredicto como último paso.
Responde SOLO con el JSON de tool call hasta que guardar_veredicto haya sido ejecutado.    

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
            "Ejecuta el flujo completo: lee engine_v2.py y casos_prueba.md, genera los tests "
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