# No arquivo editor.py

from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt5.QtCore import QRegExp

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)

        # Formatos de texto
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#000080")) # Azul escuro
        keyword_format.setFontWeight(QFont.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000")) # Verde

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080")) # Cinza
        comment_format.setFontItalic(True) # Opcional: Comentários em itálico

        function_method_format = QTextCharFormat()
        function_method_format.setForeground(QColor("#0000FF")) # Azul

        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#800080")) # Roxo/Púrpura
        class_format.setFontWeight(QFont.Bold)

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#FF8000")) # Laranja
        decorator_format.setFontWeight(QFont.Bold)

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FF0000")) # Vermelho

        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor("#A020F0")) # Roxo


        # Palavras-chave Python
        keywords = ["False", "None", "True", "and", "as", "assert", "async",
                    "await", "break", "class", "continue", "def", "del",
                    "elif", "else", "except", "finally", "for", "from",
                    "global", "if", "import", "in", "is", "lambda", "nonlocal",
                    "not", "or", "pass", "raise", "return", "try", "while",
                    "with", "yield"]

        # Lista de regras de destaque
        self.highlighting_rules = []

        # Regras para palavras-chave
        self.highlighting_rules += [(QRegExp(r"\b%s\b" % keyword), keyword_format)
                                   for keyword in keywords]

        # Regra para classes (identifica palavras após 'class ')
        self.highlighting_rules.append((QRegExp(r"\bclass\s+([A-Za-z_]\w*)"), class_format))

        # Regra para funções e métodos (identifica palavras após 'def ')
        self.highlighting_rules.append((QRegExp(r"\bdef\s+([A-Za-z_]\w*)"), function_method_format))

        # Regra para strings (entre aspas duplas ou simples)
        self.highlighting_rules.append((QRegExp(r"\".*\""), string_format))
        self.highlighting_rules.append((QRegExp(r"\'.*\'"), string_format))

        # Regra para comentários
        self.highlighting_rules.append((QRegExp(r"#.*"), comment_format))

        # Regra para decoradores (@...)
        self.highlighting_rules.append((QRegExp(r"@\s*([A-Za-z_]\w*)"), decorator_format))

        # Regra para números (inteiros e de ponto flutuante)
        self.highlighting_rules.append((QRegExp(r"\b\d+(\.\d*)?|\.\d+\b"), number_format))

        # Regra para operadores (alguns exemplos)
        operators = ["=", "==", "!=", "<", "<=", ">", ">=", "\\+", "-", "\\*", "/", "//", "%", "\\*\\*",
                     "\\+=", "-=", "\\*=", "/=", "//=", "%=", "\\*\\*=",
                     "&", "\\|", "\\^", "~", "<<", ">>", "and", "or", "not", "is", "in"] # Incluindo operadores lógicos e de associação

        self.highlighting_rules += [(QRegExp(r"%s" % QRegExp.escape(operator)), operator_format)
                                   for operator in operators]


        # Regra para funções built-in (alguns exemplos comuns) - Opcional
        # builtin_functions = ["print", "len", "range", "int", "str", "list", "dict", "tuple", "set"]
        # builtin_format = QTextCharFormat()
        # builtin_format.setForeground(QColor("#4169E1")) # Azul Royal
        # self.highlighting_rules += [(QRegExp(r"\b%s\b(?=\()" % func), builtin_format)
        #                            for func in builtin_functions]



    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                # Para regras com grupos de captura (como classes e funções),
                # usamos capturedTexts() para aplicar o formato apenas ao nome
                if expression.captureCount() > 0:
                    # Encontra a posição do primeiro grupo de captura
                    group_index = expression.pos(1)
                    group_length = len(expression.capturedTexts()[1])
                    if group_index != -1:
                         self.setFormat(group_index, group_length, format)
                else:
                    # Para regras sem grupos de captura, aplica o formato a toda a correspondência
                    length = expression.matchedLength()
                    self.setFormat(index, length, format)

                index = expression.indexIn(text, index + expression.matchedLength()) # Continua a busca após a correspondência


        # Não definimos blockState para destaque simples por linha

class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Basic initialization for the editor
        self.setFontFamily('Courier New')
        self.setFontPointSize(10)
        self.setTabStopWidth(20) # Adjust tab width as needed

        # Adiciona o destacador de sintaxe
        self.highlighter = PythonHighlighter(self.document())

# Restante do arquivo editor.py (se houver mais código)
