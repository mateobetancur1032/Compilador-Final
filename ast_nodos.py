"""Nodos del Árbol de Sintaxis Abstracta (AST).

Es el ÚNICO contrato compartido entre el analizador sintáctico y el
verificador semántico. Cada nodo conserva su línea y columna de origen.
"""
from dataclasses import dataclass, field
from typing import List, Union


@dataclass
class Nodo:
    linea: int
    columna: int


# ---------- Expresiones ----------
@dataclass
class Literal(Nodo):
    valor: Union[int, float, bool]
    tipo: str  # "int" | "real" | "bool"


@dataclass
class Referencia(Nodo):
    nombre: str


@dataclass
class Binaria(Nodo):
    operador: str  # "+", "-", "*", "/"
    izquierda: "Expresion"
    derecha: "Expresion"


Expresion = Union[Literal, Referencia, Binaria]


# ---------- Sentencias ----------
@dataclass
class Declaracion(Nodo):
    tipo: str
    nombre: str
    valor: Expresion


@dataclass
class Asignacion(Nodo):
    nombre: str
    valor: Expresion


@dataclass
class Salida(Nodo):
    valor: Expresion


Sentencia = Union[Declaracion, Asignacion, Salida]


@dataclass
class Programa(Nodo):
    sentencias: List[Sentencia] = field(default_factory=list)
