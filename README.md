# Taller: Analizador sintáctico y semántico

Arquitectura (cada fase solo conoce el AST de `ast_nodos.py`):

```
código ─► lexer.py ─► [Token] ─► parser.py ─► AST ─► semantico.py ─► tabla de símbolos
```

| Archivo | Contenido |
|---|---|
| `tokens.py` | `Token(tipo, lexema, linea, columna)` y constantes de tipos |
| `ast_nodos.py` | `Programa`, `Declaracion`, `Asignacion`, `Salida`, `Literal`, `Referencia`, `Binaria` |
| `errores.py` | `ErrorLexico`, `ErrorSintactico`, `ErrorSemantico` (mensaje, línea, columna) |
| `lexer.py` | `AnalizadorLexico` (soporta comentarios `//`) |
| `parser.py` | `AnalizadorSintactico` — descenso recursivo, asociatividad izquierda, EOF estricto |
| `semantico.py` | `VerificadorSemantico` + `TablaSimbolos` |
| `main.py` | Orquesta las fases y captura errores |
| `tests/test_taller.py` | 40 pruebas (categorías A, B y C) |

## Ejecutar

```bash
# Pruebas (desde esta carpeta)
python -m unittest discover tests -v

# Compilar un programa
python main.py ejemplo.txt
```

En Windows, si `python` no funciona, usa `py`.
