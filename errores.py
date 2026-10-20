"""Excepciones del compilador."""


class ErrorCompilacion(Exception):
    fase = "Error"

    def __init__(self, mensaje: str, linea: int, columna: int):
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna
        super().__init__(f"{self.fase} [{linea}:{columna}]: {mensaje}")


class ErrorLexico(ErrorCompilacion):
    fase = "Error léxico"


class ErrorSintactico(ErrorCompilacion):
    fase = "Error sintáctico"


class ErrorSemantico(ErrorCompilacion):
    fase = "Error semántico"
