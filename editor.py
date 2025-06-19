# No arquivo editor.py

from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt5.QtCore import QRegExp

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#000080")) # Azul escuro
        keyword_format.setFontWeight(QFont.Bold)

        keywords = ["False", "None", "True", "and", "as", "assert", "async",
                    "await", "break", "class", "continue", "def", "del",
                    "elif", "else", "except", "finally", "for", "from",
                    "global", "if", "import", "in", "is", "lambda", "nonlocal",
                    "not", "or", "pass", "raise", "return", "try", "while",
                    "with", "yield"]

        self.highlighting_rules = [(QRegExp(r"\b%s\b" % keyword), keyword_format)
                                   for keyword in keywords]

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000")) # Verde
        self.highlighting_rules.append((QRegExp(r"\".*\""), string_format))
        self.highlighting_rules.append((QRegExp(r"\'.*\'"), string_format))

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080")) # Cinza
        self.highlighting_rules.append((QRegExp(r"#.*"), comment_format))

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#0000FF")) # Azul
        self.highlighting_rules.append((QRegExp(r"\b[A-Za-z0-9_]+(?=\()"), function_format))


    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)


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
