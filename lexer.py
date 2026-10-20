"""Analizador léxico: convierte el código fuente en una lista de Tokens."""
from typing import List

from errores import ErrorLexico
from tokens import (
    Token, NUM_INT, NUM_REAL, BOOL, ID, TIPO, PRINT, ASIGNAR, MAS, MENOS,
    POR, DIV, PAR_IZQ, PAR_DER, PUNTO_COMA, EOF,
)

PALABRAS_RESERVADAS = {
    "int": TIPO,
    "real": TIPO,
    "bool": TIPO,
    "print": PRINT,
    "true": BOOL,
    "false": BOOL,
}

SIMBOLOS = {
    "=": ASIGNAR, "+": MAS, "-": MENOS, "*": POR, "/": DIV,
    "(": PAR_IZQ, ")": PAR_DER, ";": PUNTO_COMA,
}


class AnalizadorLexico:
    def __init__(self, codigo: str):
        self.codigo = codigo
        self.pos = 0
        self.linea = 1
        self.columna = 1

    def _actual(self) -> str:
        return self.codigo[self.pos] if self.pos < len(self.codigo) else ""

    def _avanzar(self) -> str:
        c = self.codigo[self.pos]
        self.pos += 1
        if c == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1
        return c

    def tokenizar(self) -> List[Token]:
        tokens: List[Token] = []
        while self.pos < len(self.codigo):
            c = self._actual()

            if c.isspace():
                self._avanzar()
                continue

            # Comentarios de línea: // ...
            if c == "/" and self.codigo[self.pos:self.pos + 2] == "//":
                while self._actual() not in ("", "\n"):
                    self._avanzar()
                continue

            linea, columna = self.linea, self.columna

            if c.isdigit():
                lexema = ""
                while self._actual().isdigit():
                    lexema += self._avanzar()
                if self._actual() == "." and self.codigo[self.pos + 1:self.pos + 2].isdigit():
                    lexema += self._avanzar()
                    while self._actual().isdigit():
                        lexema += self._avanzar()
                    tokens.append(Token(NUM_REAL, lexema, linea, columna))
                else:
                    tokens.append(Token(NUM_INT, lexema, linea, columna))
                continue

            if c.isalpha() or c == "_":
                lexema = ""
                while self._actual().isalnum() or self._actual() == "_":
                    lexema += self._avanzar()
                tipo = PALABRAS_RESERVADAS.get(lexema, ID)
                tokens.append(Token(tipo, lexema, linea, columna))
                continue

            if c in SIMBOLOS:
                self._avanzar()
                tokens.append(Token(SIMBOLOS[c], c, linea, columna))
                continue

            raise ErrorLexico(f"Carácter no reconocido '{c}'", linea, columna)

        tokens.append(Token(EOF, "", self.linea, self.columna))
        return tokens
