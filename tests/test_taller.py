"""Suite de pruebas del taller.  Ejecutar desde la raíz del proyecto:

    python -m unittest discover tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodos import Binaria, Declaracion, Literal, Referencia  # noqa: E402
from errores import ErrorSemantico, ErrorSintactico  # noqa: E402
from lexer import AnalizadorLexico  # noqa: E402
from main import compilar  # noqa: E402
from parser import AnalizadorSintactico  # noqa: E402
from semantico import VerificadorSemantico  # noqa: E402
from tokens import EOF, Token  # noqa: E402


def parsear(codigo):
    return AnalizadorSintactico(AnalizadorLexico(codigo).tokenizar()).analizar()


def tipo_de(codigo, variable):
    _, tabla = compilar(codigo)
    return tabla.buscar(variable)


def tipo_expr(codigo_previo, expr):
    """Tipo inferido de `expr` en el contexto de `codigo_previo`."""
    ast = parsear(f"{codigo_previo} print({expr});")
    v = VerificadorSemantico()
    v.verificar(ast)
    return v.tipos_inferidos[id(ast.sentencias[-1].valor)]


# ======================================================================
# Categoría A: sintaxis válida y semántica correcta
# ======================================================================
class TestA_Validos(unittest.TestCase):

    def test_a1_declaraciones_basicas(self):
        _, tabla = compilar("int a = 5; real b = 2.5; bool c = true; print(a);")
        self.assertEqual(tabla.buscar("a"), "int")
        self.assertEqual(tabla.buscar("b"), "real")
        self.assertEqual(tabla.buscar("c"), "bool")

    def test_a1_asignacion_mismo_tipo(self):
        compilar("int a = 1; a = 2; bool f = false; f = true;")

    def test_a2_promocion_en_inicializacion(self):
        self.assertEqual(tipo_de("real r = 3;", "r"), "real")

    def test_a2_promocion_en_asignacion(self):
        compilar("int i = 4; real r = 1.0; r = i;")

    def test_a2_promocion_mixta_en_expresion(self):
        self.assertEqual(tipo_expr("int i = 1; real r = 2.0;", "i + r"), "real")
        self.assertEqual(tipo_expr("int i = 1;", "i * 2"), "int")

    def test_a3_precedencia(self):
        ast = parsear("int a = 1; int b = 2; int c = 3; int d = a + b * c;")
        expr = ast.sentencias[3].valor
        # a + (b * c)
        self.assertIsInstance(expr, Binaria)
        self.assertEqual(expr.operador, "+")
        self.assertIsInstance(expr.izquierda, Referencia)
        self.assertIsInstance(expr.derecha, Binaria)
        self.assertEqual(expr.derecha.operador, "*")
        compilar("int a = 1; int b = 2; int c = 3; int d = a + b * c;")

    def test_a3_parentesis_cambian_precedencia(self):
        expr = parsear("int d = (1 + 2) * 3;").sentencias[0].valor
        self.assertEqual(expr.operador, "*")
        self.assertEqual(expr.izquierda.operador, "+")

    def test_a4_asociatividad_izquierda_resta(self):
        expr = parsear("int x = 10 - 3 - 2;").sentencias[0].valor
        # (10 - 3) - 2
        self.assertEqual(expr.operador, "-")
        self.assertIsInstance(expr.izquierda, Binaria)
        self.assertEqual(expr.izquierda.izquierda.valor, 10)
        self.assertEqual(expr.izquierda.derecha.valor, 3)
        self.assertIsInstance(expr.derecha, Literal)
        self.assertEqual(expr.derecha.valor, 2)

    def test_a4_asociatividad_izquierda_division(self):
        expr = parsear("real x = 8 / 4 / 2;").sentencias[0].valor
        self.assertIsInstance(expr.izquierda, Binaria)
        self.assertEqual(expr.derecha.valor, 2)

    def test_a5_division_enteros_es_real(self):
        self.assertEqual(tipo_expr("", "10 / 2"), "real")
        compilar("real r = 10 / 2;")

    def test_nodos_conservan_posicion(self):
        ast = parsear("int a = 1;\n  real b = a * 2;")
        decl = ast.sentencias[1]
        self.assertIsInstance(decl, Declaracion)
        self.assertEqual((decl.linea, decl.columna), (2, 3))
        self.assertEqual((decl.valor.linea, decl.valor.columna), (2, 14))  # '*'

    def test_programa_vacio(self):
        self.assertEqual(parsear("").sentencias, [])


# ======================================================================
# Categoría B: errores sintácticos
# ======================================================================
class TestB_Sintacticos(unittest.TestCase):

    def assertSintactico(self, codigo):
        with self.assertRaises(ErrorSintactico) as ctx:
            parsear(codigo)
        return ctx.exception

    def test_b1_falta_punto_y_coma(self):
        e = self.assertSintactico("int a = 5\nint b = 3;")
        self.assertEqual(e.linea, 2)

    def test_b1_falta_punto_y_coma_al_final(self):
        self.assertSintactico("print(1)")

    def test_b2_parentesis_sin_cerrar(self):
        self.assertSintactico("int a = (1 + 2;")

    def test_b2_parentesis_de_mas(self):
        self.assertSintactico("int a = 1 + 2);")

    def test_b2_print_sin_cerrar(self):
        self.assertSintactico("print((1 + 2);")

    def test_b3_operador_sin_operando(self):
        self.assertSintactico("int a = 1 + ;")

    def test_b3_falta_igual(self):
        self.assertSintactico("int a 5;")

    def test_b3_tipo_sin_identificador(self):
        self.assertSintactico("real = 2.0;")

    def test_b3_sentencia_que_empieza_con_numero(self):
        self.assertSintactico("5 = a;")

    def test_b3_operadores_consecutivos(self):
        self.assertSintactico("int a = 2 * * 3;")

    def test_b4_tokens_tras_eof(self):
        tokens = AnalizadorLexico("int a = 1;").tokenizar()
        tokens.append(Token("ID", "basura", 1, 20))
        tokens.append(Token(EOF, "", 1, 26))
        with self.assertRaises(ErrorSintactico):
            AnalizadorSintactico(tokens).analizar()

    def test_parser_no_hace_semantica(self):
        # Sintácticamente válido aunque semánticamente incorrecto.
        parsear("int a = true + z;")


# ======================================================================
# Categoría C: errores semánticos
# ======================================================================
class TestC_Semanticos(unittest.TestCase):

    def assertSemantico(self, codigo):
        with self.assertRaises(ErrorSemantico) as ctx:
            compilar(codigo)
        return ctx.exception

    def test_c1_variable_no_declarada_en_expresion(self):
        e = self.assertSemantico("int a = b + 1;")
        self.assertEqual((e.linea, e.columna), (1, 9))

    def test_c1_asignacion_a_no_declarada(self):
        self.assertSemantico("x = 3;")

    def test_c1_autoreferencia_en_declaracion(self):
        self.assertSemantico("int x = x + 1;")

    def test_c2_redeclaracion(self):
        e = self.assertSemantico("int a = 1;\nint a = 2;")
        self.assertEqual(e.linea, 2)

    def test_c2_redeclaracion_otro_tipo(self):
        self.assertSemantico("int a = 1; real a = 2.0;")

    def test_c3_real_en_int_inicializacion(self):
        self.assertSemantico("int a = 3.5;")

    def test_c3_real_en_int_asignacion(self):
        self.assertSemantico("int a = 1; real r = 2.0; a = r;")

    def test_c3_division_en_int(self):
        self.assertSemantico("int a = 10 / 2;")

    def test_c3_numerico_en_bool(self):
        self.assertSemantico("bool b = 1;")

    def test_c3_bool_en_numerico(self):
        self.assertSemantico("real r = true;")

    def test_c4_bool_en_suma(self):
        self.assertSemantico("bool b = true; int a = b + 1;")

    def test_c4_bool_en_division(self):
        self.assertSemantico("real r = 4 / false;")

    def test_c4_bool_con_bool(self):
        self.assertSemantico("bool b = true * false;")

    def test_c5_print_con_operacion_invalida(self):
        self.assertSemantico("bool b = true; print(b - 1);")

    def test_c5_print_con_no_declarada(self):
        self.assertSemantico("print(z);")

    def test_c5_print_valido_de_cada_tipo(self):
        compilar("int i = 1; real r = 2.0; bool b = true; print(i); print(r); print(b); print(i / r);")


if __name__ == "__main__":
    unittest.main()
