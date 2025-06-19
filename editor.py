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

        # Lista de regras de destaque - Ordem importa!
        self.highlighting_rules = []

        # **Regra para comentários (DEVE SER A PRIMEIRA)**
        self.highlighting_rules.append((QRegExp(r"#.*"), comment_format))

        # Regras para palavras-chave (usando limites de palavra mais estritos)
        # Garante que a palavra inteira seja correspondida
        for keyword in keywords:
             pattern = QRegExp(r"\b" + QRegExp.escape(keyword) + r"\b")
             self.highlighting_rules.append((pattern, keyword_format))


        # Regra para classes (identifica palavras após 'class ' com limite de palavra)
        self.highlighting_rules.append((QRegExp(r"\bclass\s+([A-Za-z_]\w*)\b"), class_format))

        # Regra para funções e métodos (identifica palavras após 'def ' com limite de palavra)
        self.highlighting_rules.append((QRegExp(r"\bdef\s+([A-Za-z_]\w*)\b"), function_method_format))

        # Regra para strings (entre aspas duplas ou simples)
        self.highlighting_rules.append((QRegExp(r"\".*\""), string_format))
        self.highlighting_rules.append((QRegExp(r"\'.*\'"), string_format))

        # Regra para decoradores (@...)
        self.highlighting_rules.append((QRegExp(r"@\s*([A-Za-z_]\w*)\b"), decorator_format))

        # Regra para números (inteiros e de ponto flutuante com limites de palavra)
        self.highlighting_rules.append((QRegExp(r"\b\d+(\.\d*)?|\.\d+\b"), number_format))

        # Regra para operadores (alguns exemplos) - Mantido, mas a regra de comentário vem antes
        operators = ["=", "==", "!=", "<", "<=", ">", ">=", "\\+", "-", "\\*", "/", "//", "%", "\\*\\*",
                     "\\+=", "-=", "\\*=", "/=", "//=", "%=", "\\*\\*=",
                     "&", "\\|", "\\^", "~", "<<", ">>"] # Removido 'and', 'or', 'not', 'is', 'in' daqui

        for operator in operators:
            pattern = QRegExp(QRegExp.escape(operator))
            self.highlighting_rules.append((pattern, operator_format))


        # Regra para funções built-in (alguns exemplos comuns) - Opcional e com limite de palavra
        # builtin_functions = ["print", "len", "range", "int", "str", "list", "dict", "tuple", "set"]
        # builtin_format = QTextCharFormat()
        # builtin_format.setForeground(QColor("#4169E1")) # Azul Royal
        # for func in builtin_functions:
        #     pattern = QRegExp(r"\b" + QRegExp.escape(func) + r"\b(?=\()") # Verifica se é seguido por '('
        #     self.highlighting_rules.append((pattern, builtin_format))


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

                # Continua a busca após a correspondência encontrada
                # Usamos index + 1 para avançar pelo menos um caractere e evitar loops infinitos
                # para padrões de comprimento zero (que não devem ocorrer aqui, mas é uma prática segura)
                index = expression.indexIn(text, index + max(1, expression.matchedLength()))


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
