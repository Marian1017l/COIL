import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
REPORTE_PATH = PROJECT_ROOT / ".report.json"

def ejecutar_en_sandbox() -> dict:
    """Lanza el contenedor Docker, ejecuta pytest y evalúa el veredicto."""
    
    # 1. Asegurar que el reporte anterior no interfiera
    if REPORTE_PATH.exists():
        REPORTE_PATH.unlink()

    # 2. Lanzar el contenedor Docker
    try:
        proceso = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "PYTHONPATH=/app",  # <-- ESTO ARREGLA EL IMPORT
                "-v", f"{PROJECT_ROOT.resolve()}:/app",
                "-w", "/app",
                "guardian-sandbox",
                "pytest", "test_generated.py", "-c", "/dev/null", "--json-report", "--json-report-file=.report.json",
            ],
            capture_output=True,
            text=True,
            check=False
        )
        
        print("\n=== SALIDA REAL DE PYTEST EN DOCKER ===")
        print(proceso.stdout)
        if proceso.stderr:
            print("=== ERRORES DE SCRIPT DOCKER ===")
            print(proceso.stderr)
        print("=======================================\n")

    except Exception as e:
        return {
            "passed": 0,
            "failed": 0,
            "bugs_detectados": 1,
            "veredicto": "RECHAZADO",
            "error": f"Error al ejecutar Docker: {str(e)}"
        }

    # 3. Leer el archivo .report.json generado
    if not REPORTE_PATH.exists():
        return {
            "passed": 0,
            "failed": 0,
            "bugs_detectados": 1,
            "veredicto": "RECHAZADO",
            "error": "No se generó el archivo .report.json."
        }

    try:
        reporte = json.loads(REPORTE_PATH.read_text(encoding="utf-8"))
        summary = reporte.get("summary", {})
        
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        errores = summary.get("error", 0) 

        # Sumamos fallos de tests + errores del código
        total_bugs = failed + errores

        # 4. Determinar veredicto: Para aprobar, NO debe haber bugs y DEBE haber tests pasados
        if total_bugs == 0 and passed > 0:
            veredicto = "APROBADO"
        else:
            veredicto = "RECHAZADO"

        return {
            "passed": passed,
            "failed": failed,
            "bugs_detectados": total_bugs,
            "veredicto": veredicto
        }
    except Exception as e:
        return {
            "passed": 0,
            "failed": 0,
            "bugs_detectados": 1,
            "veredicto": "RECHAZADO",
            "error": f"Error al procesar el reporte JSON: {str(e)}"
        }

if __name__ == "__main__":
    print("Iniciando ejecución en Sandbox...")
    resultado = ejecutar_en_sandbox()
    print("RESULTADO FINAL DEL SANDBOX:")
    print(json.dumps(resultado, indent=2))