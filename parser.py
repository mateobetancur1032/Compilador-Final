"""Analizador sintáctico por descenso recursivo.

Gramática:
    programa     -> sentencia* EOF
    sentencia    -> declaracion | asignacion | salida
    declaracion  -> TIPO ID '=' expresion ';'
    asignacion   -> ID '=' expresion ';'
    salida       -> 'print' '(' expresion ')' ';'
    expresion    -> termino (('+' | '-') termino)*      (asociatividad izquierda)
    termino      -> factor  (('*' | '/') factor)*       (asociatividad izquierda)
    factor       -> NUM_INT | NUM_REAL | BOOL | ID | '(' expresion ')'

No realiza ninguna verificación semántica: solo construye el AST.
"""
from typing import List

from ast_nodos import (
    Programa, Declaracion, Asignacion, Salida, Literal, Referencia, Binaria,
)
from errores import ErrorSintactico
from tokens import (
    Token, NUM_INT, NUM_REAL, BOOL, ID, TIPO, PRINT, ASIGNAR, MAS, MENOS,
    POR, DIV, PAR_IZQ, PAR_DER, PUNTO_COMA, EOF,
)


class AnalizadorSintactico:
    def __init__(self, tokens: List[Token]):
        if not tokens or tokens[-1].tipo != EOF:
            raise ValueError("La lista de tokens debe terminar en EOF")
        self.tokens = tokens
        self.pos = 0

    # ---------- utilidades ----------
    def _actual(self) -> Token:
        return self.tokens[self.pos]

    def _verificar(self, tipo: str) -> bool:
        return self._actual().tipo == tipo

    def _avanzar(self) -> Token:
        tok = self._actual()
        if tok.tipo != EOF:
            self.pos += 1
        return tok

    def _coincidir(self, tipo: str, esperado: str) -> Token:
        if self._verificar(tipo):
            return self._avanzar()
        tok = self._actual()
        encontrado = "fin de archivo" if tok.tipo == EOF else f"'{tok.lexema}'"
        raise ErrorSintactico(
            f"Se esperaba {esperado} pero se encontró {encontrado}",
            tok.linea, tok.columna,
        )

    # ---------- reglas ----------
    def analizar(self) -> Programa:
        inicio = self._actual()
        sentencias = []
        while not self._verificar(EOF):
            sentencias.append(self._sentencia())
        self._coincidir(EOF, "fin de archivo")
        # Tras EOF no puede quedar nada en el flujo de tokens.
        if self.pos != len(self.tokens) - 1:
            sobrante = self.tokens[self.pos + 1]
            raise ErrorSintactico(
                f"Token '{sobrante.lexema}' después del fin de archivo",
                sobrante.linea, sobrante.columna,
            )
        return Programa(inicio.linea, inicio.columna, sentencias)

    def _sentencia(self):
        tok = self._actual()
        if tok.tipo == TIPO:
            return self._declaracion()
        if tok.tipo == ID:
            return self._asignacion()
        if tok.tipo == PRINT:
            return self._salida()
        encontrado = "fin de archivo" if tok.tipo == EOF else f"'{tok.lexema}'"
        raise ErrorSintactico(
            f"Inicio de sentencia inválido: {encontrado}", tok.linea, tok.columna
        )

    def _declaracion(self) -> Declaracion:
        tipo = self._coincidir(TIPO, "un tipo (int, real, bool)")
        nombre = self._coincidir(ID, "un identificador")
        self._coincidir(ASIGNAR, "'='")
        valor = self._expresion()
        self._coincidir(PUNTO_COMA, "';'")
        return Declaracion(tipo.linea, tipo.columna, tipo.lexema, nombre.lexema, valor)

    def _asignacion(self) -> Asignacion:
        nombre = self._coincidir(ID, "un identificador")
        self._coincidir(ASIGNAR, "'='")
        valor = self._expresion()
        self._coincidir(PUNTO_COMA, "';'")
        return Asignacion(nombre.linea, nombre.columna, nombre.lexema, valor)

    def _salida(self) -> Salida:
        kw = self._coincidir(PRINT, "'print'")
        self._coincidir(PAR_IZQ, "'('")
        valor = self._expresion()
        self._coincidir(PAR_DER, "')'")
        self._coincidir(PUNTO_COMA, "';'")
        return Salida(kw.linea, kw.columna, valor)

    def _expresion(self):
        nodo = self._termino()
        while self._actual().tipo in (MAS, MENOS):
            op = self._avanzar()
            derecha = self._termino()
            nodo = Binaria(op.linea, op.columna, op.lexema, nodo, derecha)
        return nodo

    def _termino(self):
        nodo = self._factor()
        while self._actual().tipo in (POR, DIV):
            op = self._avanzar()
            derecha = self._factor()
            nodo = Binaria(op.linea, op.columna, op.lexema, nodo, derecha)
        return nodo

    def _factor(self):
        tok = self._actual()
        if tok.tipo == NUM_INT:
            self._avanzar()
            return Literal(tok.linea, tok.columna, int(tok.lexema), "int")
        if tok.tipo == NUM_REAL:
            self._avanzar()
            return Literal(tok.linea, tok.columna, float(tok.lexema), "real")
        if tok.tipo == BOOL:
            self._avanzar()
            return Literal(tok.linea, tok.columna, tok.lexema == "true", "bool")
        if tok.tipo == ID:
            self._avanzar()
            return Referencia(tok.linea, tok.columna, tok.lexema)
        if tok.tipo == PAR_IZQ:
            self._avanzar()
            nodo = self._expresion()
            self._coincidir(PAR_DER, "')'")
            return nodo
        encontrado = "fin de archivo" if tok.tipo == EOF else f"'{tok.lexema}'"
        raise ErrorSintactico(
            f"Se esperaba una expresión pero se encontró {encontrado}",
            tok.linea, tok.columna,
        )
