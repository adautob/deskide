# No arquivo editor.py

from PyQt5.QtWidgets import QTextEdit, QWidget
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor, QPainter, QTextBlock
from PyQt5.QtCore import QRegExp, QSize, QRect, Qt # Adicionada QSize, QRect, Qt

import re # Adicionada importação re para o destacador

# Classe para a área de numeração de linhas
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        # Sugere a largura necessária para a numeração
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        # Desenha os números das linhas
        painter = QPainter(self)
        painter.fillRect(event.rect(), Qt.lightGray) # Fundo da área de numeração

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        # Calcular a posição top usando a geometria do bloco e o deslocamento da barra de rolagem
        top = self.editor.blockBoundingGeometry(block).top() - self.editor.verticalScrollBar().sliderPosition()
        bottom = top + self.editor.blockBoundingRect(block).height()

        # Loop sobre os blocos visíveis
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, round(top), self.size().width(), self.editor.fontMetrics().height(), # Usar round() para posições y
                                 Qt.AlignRight | Qt.AlignVCenter, number)

            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            block_number += 1

# Classe para o destacador de sintaxe (mantida com as correções)
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

        # Regra para comentários (DEVE SER A PRIMEIRA)
        self.highlighting_rules.append((QRegExp(r"#.*"), comment_format))

        # Regras para palavras-chave (usando limites de palavra mais estritos)
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

        # Regra para operadores (alguns exemplos)
        operators = ["=", "==", "!=", "<", "<=", ">", ">=", "\\+", "-", "\\*", "/", "//", "%", "\\*\\*",
                     "\\+=", "-=", "\\*=", "/=", "//=", "%=", "\\*\\*=",
                     "&", "\\|", "\\^", "~", "<<", ">>"]

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
                index = expression.indexIn(text, index + max(1, expression.matchedLength()))


# Classe CodeEditor com numeração de linhas
class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        print(f"blockBoundingGeometry disponível? {'blockBoundingGeometry' in dir(self)}") # Linha de teste
        print(f"blockBoundingRect disponível? {'blockBoundingRect' in dir(self)}") # Linha de teste 2
        # Basic initialization for the editor
        self.setFontFamily('Courier New')
        self.setFontPointSize(10)
        self.setTabStopWidth(20) # Adjust tab width as needed

        # Adiciona o destacador de sintaxe
        self.highlighter = PythonHighlighter(self.document())

        # **Adiciona a área de numeração de linhas**
        self.lineNumberArea = LineNumberArea(self)
        self.verticalScrollBar().valueChanged.connect(self.lineNumberArea.update) # Sincroniza com a barra de rolagem
        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth) # Atualiza largura quando o número de blocos muda
        self.document().contentsChange.connect(self.updateLineNumberArea) # Atualiza numeração quando o conteúdo muda
        #self.updateRequest.connect(self.lineNumberArea.update) # Conecta updateRequest para garantir atualização

        self.updateLineNumberAreaWidth(0) # Define a largura inicial


    def lineNumberAreaWidth(self):
        # Calcula a largura necessária para a área de numeração
        digits = 1
        max_value = max(1, self.document().blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits # Ajuste para o preenchimento
        return space

    def resizeEvent(self, event):
        # Redimensiona a área de numeração quando o editor é redimensionado
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def paintEvent(self, event):
        # Chama o paintEvent original do QTextEdit
        super().paintEvent(event)
        # O paintEvent da área de numeração é chamado separadamente

    def firstVisibleBlock(self):
        # Retorna o primeiro bloco (linha) visível no editor
        # Iterar pelos blocos até encontrar um cuja geometria esteja dentro ou acima da viewport
        # considerando o deslocamento da barra de rolagem
        block = self.document().firstBlock()
        vscroll_pos = self.verticalScrollBar().sliderPosition()

        while block.isValid():
            block_geometry = self.blockBoundingGeometry(block)
            block_top_in_viewport = block_geometry.top() - vscroll_pos

            # Se o topo do bloco está dentro ou acima da área visível (>= 0), é o primeiro visível
            if block_top_in_viewport >= -block_geometry.height() and block.isVisible():
                 return block

            block = block.next()

        return self.document().firstBlock() # Retorna o primeiro bloco se nenhum visível for encontrado (improvável)


    def updateLineNumberAreaWidth(self, newBlockCount):
        # Slot para atualizar a largura da área de numeração
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0) # Define a margem para a área de numeração

    def updateLineNumberArea(self, position, charsRemoved, charsAdded):
        # Slot para atualizar a área de numeração quando o conteúdo muda
        # Precisamos solicitar uma atualização para o LineNumberArea
        self.lineNumberArea.update()
        self.updateLineNumberAreaWidth(0) # Recalcula a largura (opcional, mas útil para grandes mudanças)


# Restante do arquivo editor.py (se houver mais código)
