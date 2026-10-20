"""Definición del Token compartido entre el analizador léxico y el sintáctico."""
from dataclasses import dataclass

# Tipos de token
NUM_INT = "NUM_INT"
NUM_REAL = "NUM_REAL"
BOOL = "BOOL"
ID = "ID"
TIPO = "TIPO"          # int | real | bool
PRINT = "PRINT"
ASIGNAR = "ASIGNAR"    # =
MAS = "MAS"            # +
MENOS = "MENOS"        # -
POR = "POR"            # *
DIV = "DIV"            # /
PAR_IZQ = "PAR_IZQ"    # (
PAR_DER = "PAR_DER"    # )
PUNTO_COMA = "PUNTO_COMA"  # ;
EOF = "EOF"


@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int

    def __str__(self) -> str:
        return f"{self.tipo}('{self.lexema}') en {self.linea}:{self.columna}"
