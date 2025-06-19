from PyQt5.QtWidgets import QTextEdit

class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Basic initialization for the editor
        self.setFontFamily('Courier New')
        self.setFontPointSize(10)
        self.setTabStopWidth(20) # Adjust tab width as needed