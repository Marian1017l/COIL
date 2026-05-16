import subprocess
import json
from pathlib import Path

def ejecutar_en_sandbox():
    # Lanza el contenedor Docker (F·1)
    resultado = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", "./:/app",
            "-w", "/app",
            "guardian-sandbox",
            "pytest", "--json-report",
        ],
        capture_output=True,
        text=True,
    )

    # Captura Pass / Fail
    reporte = json.loads(
        Path(".report.json").read_text()
    )

    passed = reporte["summary"]["passed"]
    failed = reporte["summary"]["failed"]

    return {
        "passed": passed,
        "failed": failed,
        "bugs_detectados": failed,
        "veredicto": (
            "APROBADO" if failed == 0
            else "RECHAZADO"
        ),
    }