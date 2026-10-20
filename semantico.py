"""Verificador semántico.

Recorre el AST (definido en ast_nodos.py) sin depender del parser.
Responsabilidades:
  * Tabla de símbolos (declaración única por ámbito, uso de no declaradas).
  * Inferencia y comprobación de tipos.
      +, -, * : int op int -> int ; si alguno es real -> real ; bool -> error
      /       : operandos numéricos, resultado SIEMPRE real
  * Compatibilidad de asignación: real <- int permitido (promoción),
    int <- real prohibido, bool solo con bool.
  * print: acepta expresiones de cualquier tipo bien formado (int, real, bool);
    si la expresión interna es incorrecta, el error se propaga.
"""
from typing import Dict, List, Optional

from ast_nodos import (
    Programa, Declaracion, Asignacion, Salida, Literal, Referencia, Binaria,
)
from errores import ErrorSemantico

NUMERICOS = {"int", "real"}
TIPOS_VALIDOS = {"int", "real", "bool"}


class TablaSimbolos:
    """Pila de ámbitos. El lenguaje actual usa un único ámbito global,
    pero la estructura permite extenderlo a bloques anidados."""

    def __init__(self):
        self.ambitos: List[Dict[str, str]] = [{}]

    def declarar(self, nombre: str, tipo: str, linea: int, columna: int) -> None:
        actual = self.ambitos[-1]
        if nombre in actual:
            raise ErrorSemantico(
                f"La variable '{nombre}' ya fue declarada en este ámbito",
                linea, columna,
            )
        actual[nombre] = tipo

    def buscar(self, nombre: str) -> Optional[str]:
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def entrar(self) -> None:
        self.ambitos.append({})

    def salir(self) -> None:
        self.ambitos.pop()


class VerificadorSemantico:
    def __init__(self):
        self.tabla = TablaSimbolos()
        # Tipo inferido de cada expresión (id(nodo) -> tipo), útil para depurar.
        self.tipos_inferidos: Dict[int, str] = {}

    # ---------- punto de entrada ----------
    def verificar(self, programa: Programa) -> TablaSimbolos:
        for sentencia in programa.sentencias:
            self._sentencia(sentencia)
        return self.tabla

    # ---------- sentencias ----------
    def _sentencia(self, nodo) -> None:
        if isinstance(nodo, Declaracion):
            self._declaracion(nodo)
        elif isinstance(nodo, Asignacion):
            self._asignacion(nodo)
        elif isinstance(nodo, Salida):
            self._salida(nodo)
        else:
            raise ErrorSemantico(
                f"Sentencia desconocida: {type(nodo).__name__}",
                nodo.linea, nodo.columna,
            )

    def _declaracion(self, nodo: Declaracion) -> None:
        if nodo.tipo not in TIPOS_VALIDOS:
            raise ErrorSemantico(f"Tipo desconocido '{nodo.tipo}'", nodo.linea, nodo.columna)
        # Se evalúa la expresión ANTES de declarar: 'int x = x;' es error.
        tipo_valor = self._expresion(nodo.valor)
        self._comprobar_asignable(nodo.tipo, tipo_valor, nodo.nombre, nodo)
        self.tabla.declarar(nodo.nombre, nodo.tipo, nodo.linea, nodo.columna)

    def _asignacion(self, nodo: Asignacion) -> None:
        tipo_destino = self.tabla.buscar(nodo.nombre)
        if tipo_destino is None:
            raise ErrorSemantico(
                f"La variable '{nodo.nombre}' no ha sido declarada",
                nodo.linea, nodo.columna,
            )
        tipo_valor = self._expresion(nodo.valor)
        self._comprobar_asignable(tipo_destino, tipo_valor, nodo.nombre, nodo)

    def _salida(self, nodo: Salida) -> None:
        tipo = self._expresion(nodo.valor)
        if tipo not in TIPOS_VALIDOS:
            raise ErrorSemantico(
                f"No se puede imprimir una expresión de tipo '{tipo}'",
                nodo.linea, nodo.columna,
            )

    @staticmethod
    def _comprobar_asignable(destino: str, origen: str, nombre: str, nodo) -> None:
        if destino == origen:
            return
        if destino == "real" and origen == "int":
            return  # promoción implícita int -> real
        raise ErrorSemantico(
            f"Tipos incompatibles: no se puede asignar '{origen}' a '{nombre}' de tipo '{destino}'",
            nodo.linea, nodo.columna,
        )

    # ---------- expresiones ----------
    def _expresion(self, nodo) -> str:
        if isinstance(nodo, Literal):
            tipo = nodo.tipo
        elif isinstance(nodo, Referencia):
            tipo = self.tabla.buscar(nodo.nombre)
            if tipo is None:
                raise ErrorSemantico(
                    f"La variable '{nodo.nombre}' no ha sido declarada",
                    nodo.linea, nodo.columna,
                )
        elif isinstance(nodo, Binaria):
            tipo = self._binaria(nodo)
        else:
            raise ErrorSemantico(
                f"Expresión desconocida: {type(nodo).__name__}",
                nodo.linea, nodo.columna,
            )
        self.tipos_inferidos[id(nodo)] = tipo
        return tipo

    def _binaria(self, nodo: Binaria) -> str:
        izq = self._expresion(nodo.izquierda)
        der = self._expresion(nodo.derecha)
        if izq not in NUMERICOS or der not in NUMERICOS:
            raise ErrorSemantico(
                f"El operador '{nodo.operador}' requiere operandos numéricos "
                f"(se recibió '{izq}' {nodo.operador} '{der}')",
                nodo.linea, nodo.columna,
            )
        if nodo.operador == "/":
            return "real"
        if izq == "int" and der == "int":
            return "int"
        return "real"


# ----------------------------------------------------------------------
# Ejecución independiente:  python semantico.py ejemplo.txt
# El lexer y el parser solo se importan aquí, para construir el AST de
# entrada; la clase VerificadorSemantico no depende de ellos.
# ----------------------------------------------------------------------
def _describir(nodo) -> str:
    if isinstance(nodo, Literal):
        return str(nodo.valor).lower() if nodo.tipo == "bool" else str(nodo.valor)
    if isinstance(nodo, Referencia):
        return nodo.nombre
    if isinstance(nodo, Binaria):
        return f"({_describir(nodo.izquierda)} {nodo.operador} {_describir(nodo.derecha)})"
    return "?"


def _ejecutar_desde_archivo(ruta: str) -> int:
    from errores import ErrorCompilacion
    from lexer import AnalizadorLexico
    from parser import AnalizadorSintactico

    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()

    try:
        ast = AnalizadorSintactico(AnalizadorLexico(codigo).tokenizar()).analizar()
    except ErrorCompilacion as e:
        print(f"No se pudo construir el AST -> {e}")
        return 1

    print(f"=== Análisis semántico de '{ruta}' ===\n")
    verificador = VerificadorSemantico()
    for s in ast.sentencias:
        try:
            verificador._sentencia(s)
        except ErrorSemantico as e:
            print(f"  [ERROR] línea {s.linea}: {e}")
            print("\nResultado: el programa tiene errores semánticos.")
            return 1
        tipo_expr = verificador.tipos_inferidos[id(s.valor)]
        expr = _describir(s.valor)
        if isinstance(s, Declaracion):
            detalle = f"declara {s.tipo} {s.nombre} = {expr}  -> expresión: {tipo_expr}"
        elif isinstance(s, Asignacion):
            destino = verificador.tabla.buscar(s.nombre)
            detalle = f"asigna {s.nombre} ({destino}) = {expr}  -> expresión: {tipo_expr}"
        else:
            detalle = f"print {expr}  -> expresión: {tipo_expr}"
        if tipo_expr == "int" and (
            (isinstance(s, Declaracion) and s.tipo == "real")
            or (isinstance(s, Asignacion) and verificador.tabla.buscar(s.nombre) == "real")
        ):
            detalle += "  (promoción int -> real)"
        print(f"  [OK] línea {s.linea}: {detalle}")

    print("\nTabla de símbolos:")
    for nombre, tipo in verificador.tabla.ambitos[0].items():
        print(f"  {nombre:<12} {tipo}")
    print("\nResultado: sin errores semánticos.")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(_ejecutar_desde_archivo(sys.argv[1] if len(sys.argv) > 1 else "ejemplo.txt"))
