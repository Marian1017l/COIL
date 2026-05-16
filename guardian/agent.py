from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
from pathlib import Path

# Conexión con el modelo local (F·1)
llm = OllamaLLM(model="llama3:8b")

# Lee el código fuente entregado
codigo = Path("src/calculadora.py").read_text()

# Lee la matriz de casos (F·0)
casos = Path("docs/casos.md").read_text()

prompt = ChatPromptTemplate.from_template("""
Eres un QA Engineer experto. Analiza este código:

{codigo}

Y los casos de prueba críticos:
{casos}

Genera un archivo test_generated.py con pytest
que cubra los 10 casos. Devuelve SOLO código.
""")

cadena = prompt | llm
tests = cadena.invoke({
    "codigo": codigo,
    "casos": casos,
})

Path("test_generated.py").write_text(tests)