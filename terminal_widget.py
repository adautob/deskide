# No arquivo terminal_widget.py

import sys
import subprocess
from PyQt5.QtWidgets import QPlainTextEdit, QApplication, QVBoxLayout
from PyQt5.QtCore import QProcess, QTextCodec, QByteArray, QIODevice, QTimer, Qt, QPoint
from PyQt5.QtCore import pyqtSignal as Signal # Importação corrigida
import threading
import os

class CustomTerminalWidget(QPlainTextEdit):
    # Não precisamos mais do sinal output_received com QProcess, mas mantido se a abordagem subprocess for usada
    output_received = Signal(str)


    def __init__(self, parent=None, shell_program=None):
        super().__init__(parent)

        # Tentar encontrar o shell bash ou cmd/powershell no Windows
        if shell_program is None:
            if sys.platform.startswith('linux') or sys.platform == 'darwin':
                shell_program = "bash"
            elif sys.platform == 'win32':
                shell_program = "cmd.exe"
                # shell_program = "powershell.exe"
            else:
                shell_program = "sh"

        self.shell_program = shell_program
        self.process = QProcess(self) # Usar QProcess
        self.command_start_position = 0

        self.setReadOnly(True)
        self.appendPlainText(f"Iniciando terminal com: {self.shell_program}...\n")

        # **Conectar sinais do QProcess**
        self.process.readyReadStandardOutput.connect(self.read_standard_output)
        self.process.readyReadStandardError.connect(self.read_standard_error)
        self.process.finished.connect(self.process_finished)

        self.start_shell()


    def start_shell(self):
        try:
            # Inicia o processo do shell usando QProcess
            if sys.platform.startswith('win32'):
                 self.process.start(self.shell_program, ["/K"]) # Usar /K para manter o cmd aberto
            else:
                 self.process.start(self.shell_program)


            # **Após iniciar o shell, tornar o widget editável e definir a posição inicial da linha de comando**
            QTimer.singleShot(200, self.after_shell_start) # Ajuste no tempo se necessário


        except FileNotFoundError:
            self.appendPlainText(f"Erro: Programa do shell '{self.shell_program}' não encontrado.\n")
            self.setReadOnly(False)
        except Exception as e:
            self.appendPlainText(f"Erro ao iniciar o shell: {e}")
            self.setReadOnly(False)


    def after_shell_start(self):
         print("after_shell_start chamado (QProcess).") # Debug print
         self.setReadOnly(False)
         print("Widget definido como editável.") # Debug print
         self.moveCursor(self.textCursor().End)
         self.command_start_position = self.textCursor().position()
         # Opcional: Enviar um comando inicial como 'cd' para mostrar o diretório atual
         # self.send_command("cd")


    # **Slots para ler a saída do QProcess**
    def read_standard_output(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode(QTextCodec.codecForLocale().name()) # Não usar strip() aqui para manter quebras de linha
        if text:
            print(f"Saída Standard recebida (QProcess): {repr(text)}") # Debug print com repr()
            self.appendPlainText(text) # appendPlainText agora lida com a detecção de fim de comando

    def read_standard_error(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode(QTextCodec.codecForLocale().name()) # Não usar strip() aqui
        if text:
            print(f"Saída de Erro Standard recebida (QProcess): {repr(text)}") # Debug print com repr()
            self.appendPlainText(text) # appendPlainText agora lida com a detecção de fim de comando


    def process_finished(self, exit_code, exit_status):
        print(f"Processo do shell ({self.shell_program}) encerrado com código {exit_code} e status {exit_status}.") # Debug print
        self.appendPlainText(f"\nProcesso do shell ({self.shell_program}) encerrado.\n")
        self.setReadOnly(True) # Tornar somente leitura quando o processo terminar


    def handle_output_displayed(self):
         print("handle_output_displayed chamado (QProcess).") # Debug print
         self.setReadOnly(False)
         print("Widget definido como editável.") # Debug print
         self.moveCursor(self.textCursor().End)
         self.command_start_position = self.textCursor().position()


    # Slot conectado ao sinal output_received (este slot agora é o principal para adicionar texto)
    # Renomeei de appendPlainText para _append_text_and_scroll para clareza
    def appendPlainText(self, text):
        # Adiciona texto ao widget e rola para o final
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.ensureCursorVisible()

        # **Após adicionar a saída, tentar detectar o fim do comando (heurística)**
        # Se a saída terminar com uma quebra de linha e o widget for somente leitura,
        # pode ser o fim da resposta do comando.
        # Adicionado um pequeno atraso para dar tempo da UI processar o redraw.
        # Verifique se o widget está somente leitura e se o processo está rodando
        if self.isReadOnly() and self.process and self.process.state() == QProcess.Running:
            # Heurística: se a última parte da saída termina com newline, pode ser o fim do prompt
            # Isso é muito básico e pode não funcionar para todos os shells/prompts
            # Uma detecção de prompt mais robusta seria necessária para maior confiabilidade
            # Para cmd.exe, o prompt geralmente termina com ">" seguido de espaço ou newline.
            # Para bash, geralmente termina com "$" ou "#" seguido de espaço.
            # Vamos tentar detectar um newline e depois talvez um prompt simples
            last_text = self.document().toPlainText()[-len(text):] # Pega a última parte adicionada

            if last_text.endswith('\n'):
                 # Agenda a chamada de handle_output_displayed
                 QTimer.singleShot(50, self.handle_output_displayed)


    # Método para enviar comandos para o shell (usando QProcess.write)
    def send_command(self, command):
        if self.process and self.process.state() == QProcess.Running:
            try:
                print(f"Enviando comando para QProcess: {command}") # Debug print
                # Adiciona a linha digitada e uma nova linha visualmente antes de enviar
                # appendPlainText já lida com a exibição e a heurística de fim de comando
                self.process.write((command + '\n').encode(QTextCodec.codecForLocale().name())) # Envia como bytes
                # self.process.waitForBytesWritten() # Evitar ao máximo para não bloquear a UI
                self.setReadOnly(True) # Torna somente leitura enquanto espera a resposta
                print("Widget definido como somente leitura (enviando comando).") # Debug print


            except Exception as e:
                print(f"Erro ao enviar comando para QProcess: {e}") # Debug print
                self.appendPlainText(f"Erro ao enviar comando: {e}\n")
                self.setReadOnly(False)
                self.moveCursor(self.textCursor().End)
                self.command_start_position = self.textCursor().position()

        else:
            print("send_command (QProcess): Processo não rodando ou não disponível.") # Debug print
            self.appendPlainText("Shell não iniciado ou não disponível.\n")


    # Lidar com eventos de teclado (mantido, ajustado para QProcess)
    def keyPressEvent(self, event):
        if self.process and self.process.state() == QProcess.Running and not self.isReadOnly():
            cursor = self.textCursor()
            cursor_position_in_document = cursor.position()

            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                cursor.movePosition(cursor.End)
                cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
                current_line_with_prompt = cursor.selectedText()

                # Calcular o texto digitado pelo usuário
                cursor_pos_in_block = cursor_position_in_document - cursor.block().position()
                command_start_pos_in_block = self.command_start_position - cursor.block().position()
                # Garante que a posição de início não seja negativa
                command_text = current_line_with_prompt[max(0, command_start_pos_in_block):]


                self.send_command(command_text.strip())


            elif event.key() == Qt.Key_Backspace:
                 if cursor_position_in_document > self.command_start_position:
                     cursor.deletePreviousChar()

            elif event.key() == Qt.Key_Left:
                if cursor_position_in_document > self.command_start_position:
                    super().keyPressEvent(event)
            elif event.key() == Qt.Key_Right:
                 if cursor_position_in_document < self.textCursor().block().position() + self.textCursor().block().length() - 1:
                      super().keyPressEvent(event)

            elif event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
                 pass
            elif event.key() == Qt.Key_Delete:
                 pass
            elif event.key() == Qt.Key_Home:
                 cursor.movePosition(cursor.StartOfLine)
                 cursor.movePosition(cursor.Right, cursor.MoveAnchor, max(0, self.command_start_position - cursor.position())) # Garante que a posição de movimento não seja negativa
                 self.setTextCursor(cursor)

            elif event.key() == Qt.Key_End:
                 self.moveCursor(self.textCursor().End)


            else:
                super().keyPressEvent(event)

        else:
            super().keyPressEvent(event)


    # Lidar com o fechamento do widget (terminar o processo do shell)
    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.NotRunning:
            print(f"Encerrando processo do shell ({self.shell_program}) ao fechar widget.") # Debug print
            self.process.terminate()
            if not self.process.waitForFinished(1000): # Espera no máximo 1 segundo
                self.process.kill()
                print("Processo do shell forçado a encerrar.") # Debug print


        super().closeEvent(event)


# Exemplo básico de uso (para teste individual do widget)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    shell_to_use = None
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        shell_to_use = "bash"
    elif sys.platform == 'win32':
        shell_to_use = "cmd.exe"

    terminal = CustomTerminalWidget(shell_program=shell_to_use)
    terminal.setWindowTitle("Terminal Básico")
    terminal.resize(600, 400)
    terminal.show()

    sys.exit(app.exec_())
