"""Punto de entrada: Lexer -> Parser -> Verificador semántico.

Uso:
    python main.py programa.txt
    python main.py            (lee el código desde la entrada estándar)
"""
import sys

from errores import ErrorCompilacion
from lexer import AnalizadorLexico
from parser import AnalizadorSintactico
from semantico import VerificadorSemantico


def compilar(codigo: str):
    """Ejecuta todas las fases. Devuelve (ast, tabla_de_simbolos).
    Lanza ErrorLexico / ErrorSintactico / ErrorSemantico ante fallos."""
    tokens = AnalizadorLexico(codigo).tokenizar()
    ast = AnalizadorSintactico(tokens).analizar()
    tabla = VerificadorSemantico().verificar(ast)
    return ast, tabla


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        with open(argv[0], encoding="utf-8") as f:
            codigo = f.read()
    else:
        codigo = sys.stdin.read()

    try:
        _, tabla = compilar(codigo)
    except ErrorCompilacion as e:
        print(e, file=sys.stderr)
        return 1

    print("Compilación exitosa. Tabla de símbolos:")
    for nombre, tipo in tabla.ambitos[0].items():
        print(f"  {nombre}: {tipo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
