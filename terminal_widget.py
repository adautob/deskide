# No arquivo terminal_widget.py

import sys
import subprocess
from PyQt5.QtWidgets import QPlainTextEdit, QApplication, QVBoxLayout
from PyQt5.QtCore import QProcess, QTextCodec, QByteArray, QIODevice, QTimer, Qt, QPoint
from PyQt5.QtCore import pyqtSignal as Signal # Importação corrigida
import threading
import os
import locale # Importar o módulo locale

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
         print(f"after_shell_start: command_start_position definida como {self.command_start_position}") # <-- Debug print


    # **Slots para ler a saída do QProcess**
    def read_standard_output(self):
        data = self.process.readAllStandardOutput()
        try:
            # **Usar a codificação preferencial do sistema para decodificar**
            system_encoding = locale.getpreferredencoding(False)
            text = bytes(data).decode(system_encoding) # Usar a codificação do sistema

            if text:
                print(f"Saída Standard recebida (QProcess): {repr(text)}") # Debug print com repr()
                self.appendPlainText(text) # appendPlainText agora lida com a detecção de fim de comando

        except Exception as e:
            print(f"Erro ao decodificar saída standard: {e}")
            # Em caso de erro de decodificação, tentar decodificar como bytes brutos ou com outra codificação
            self.appendPlainText(f"\nErro de decodificação na saída standard: {e}\n")
            self.appendPlainText(repr(bytes(data)) + '\n') # Exibir os bytes brutos para depuração


    def read_standard_error(self):
        data = self.process.readAllStandardError()
        try:
            # **Usar a codificação preferencial do sistema para decodificar**
            system_encoding = locale.getpreferredencoding(False)
            text = bytes(data).decode(system_encoding)

            if text:
                print(f"Saída de Erro Standard recebida (QProcess): {repr(text)}") # Debug print com repr()
                self.appendPlainText(text) # appendPlainText agora lida com a detecção de fim de comando

        except Exception as e:
            print(f"Erro ao decodificar saída de erro standard: {e}")
            self.appendPlainText(f"\nErro de decodificação na saída de erro standard: {e}\n")
            self.appendPlainText(repr(bytes(data)) + '\n') # Exibir os bytes brutos para depuração


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
         print(f"handle_output_displayed: command_start_position redefinida como {self.command_start_position}") # <-- Debug print


    # Slot conectado ao sinal output_received (este slot agora é o principal para adicionar texto)
    # Renomeei de appendPlainText para _append_text_and_scroll para clareza
    def appendPlainText(self, text):
        # Adiciona texto ao widget e rola para o final
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.ensureCursorVisible()

        # **Após adicionar a saída, agendar a reabilitação com um pequeno atraso**
        # Isso reabilitará o widget após cada pedaço de saída, confiando no QTimer.singleShot(0, ...) em handle_output_displayed
        # Remove a heurística baseada em newline
        if self.isReadOnly() and self.process and self.process.state() == QProcess.Running:
            # Agenda a chamada de handle_output_displayed com um pequeno atraso
            QTimer.singleShot(50, self.handle_output_displayed) # Ajuste o atraso se necessário


    # Método para enviar comandos para o shell (usando QProcess.write)
    def send_command(self, command):
        if self.process and self.process.state() == QProcess.Running:
            try:
                print(f"Enviando comando para QProcess: {command}") # Debug print
                # Adiciona a linha digitada e uma nova linha visualmente antes de enviar
                # appendPlainText já lida com a exibição e a heurística de fim de comando
                print(f"Enviando comando para QProcess (string original): {repr(command)}") # <-- Debug print
                print(f"Enviando comando para QProcess (com newline): {repr(command + '\\n')}") # <-- Debug print
                
                self.process.write((command + '\n').encode(locale.getpreferredencoding(False))) # Envia como bytes usando a codificação do sistema
                # self.process.waitForBytesWritten() # Evitar ao máximo para não bloquear a UI
                self.setReadOnly(True) # Torna somente leitura enquanto espera a resposta
                print("Widget definido como somente leitura (enviando comando).") # Debug print


            except Exception as e:
                print(f"Erro ao enviar comando para QProcess: {e}") # Debug print
                self.appendPlainText(f"Erro ao enviar comando: {e}\n")
                self.setReadOnly(False)
                self.moveCursor(self.textCursor().End)
                self.command_start_position = self.textCursor().position() # Redefinir posição de início

        else:
            print("send_command (QProcess): Processo não rodando ou não disponível.") # Debug print
            self.appendPlainText("Shell não iniciado ou não disponível.\n")


    # Lidar com eventos de teclado (mantido, ajustado para QProcess)
    def keyPressEvent(self, event):
        if self.process and self.process.state() == QProcess.Running and not self.isReadOnly():
            cursor = self.textCursor()
            cursor_position_in_document = cursor.position() # Posição do cursor ANTES do Enter

            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # Capturar a linha atual como texto simples
                cursor.movePosition(cursor_position_in_document)
                cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
                current_line_text = cursor.selectedText()

                # **Debug prints para inspecionar os valores antes do fatiamento**
                print(f"keyPressEvent (Enter): current_line_text = {repr(current_line_text)}")
                print(f"keyPressEvent (Enter): len(current_line_text) = {len(current_line_text)}")
                print(f"keyPressEvent (Enter): self.command_start_position = {self.command_start_position}")
                print(f"keyPressEvent (Enter): cursor_position_in_document (before Enter) = {cursor_position_in_document}")
                print(f"keyPressEvent (Enter): cursor.block().position() = {cursor.block().position()}")


                # **CORREÇÃO FINAL (Tentativa 4):** Encontrar a posição do prompt na linha atual e fatiar a partir daí.
                prompt_end_index = current_line_text.rfind('>') # Encontra o último '>' (heurística para prompt do CMD)
                if prompt_end_index != -1:
                    # Adiciona 2 para pular o "> "
                    command_start_pos_in_line = prompt_end_index + 2
                else:
                    # Caso o prompt não seja encontrado (inesperado, mas seguro)
                    command_start_pos_in_line = 0 # Começa do início da linha

                # Calcular a posição do cursor antes do Enter, relativa à linha
                cursor_pos_in_line = cursor_position_in_document - cursor.block().position()
                # Garante que a posição do cursor relativa não seja negativa
                cursor_pos_in_line = max(0, cursor_pos_in_line)

                # **Debug prints para inspecionar posições relativas (com a nova lógica)**
                print(f"keyPressEvent (Enter): command_start_pos_in_line (after prompt find) = {command_start_pos_in_line}")
                print(f"keyPressEvent (Enter): cursor_pos_in_line = {cursor_pos_in_line}")


                # Fatiar a string da linha atual usando posições relativas
                command_text = current_line_text[command_start_pos_in_line : cursor_pos_in_line]


                # Remover quebras de linha e espaços em branco do início/fim
                command_text = command_text.strip()

                # Debug print para inspecionar command_text ANTES de enviar
                print(f"keyPressEvent (Enter): Extracted command_text (before strip) = {repr(command_text)}")
                print(f"keyPressEvent (Enter): Extracted command_text (after strip) = {repr(command_text.strip())}")


                # Adicionar a linha digitada com prompt ao display antes de enviar
                self.appendPlainText(current_line_text + '\n')


                self.send_command(command_text)

                # Resetar a posição de início do comando APÓS enviar (será ajustado por handle_output_displayed)
                # self.command_start_position = self.textCursor().position() # Não resetar aqui, handle_output_displayed fará isso


            elif event.key() == Qt.Key_Backspace:
                 if cursor_position_in_document > self.command_start_position:
                     cursor.deletePreviousChar()

            elif event.key() == Qt.Key_Left:
                if cursor_position_in_document > self.command_start_position:
                    super().keyPressEvent(event)
            elif event.key() == Qt.Key_Right:
                 # Permite mover para a direita APENAS dentro da linha atual e antes do final do texto digitado
                 # A posição do cursor no final da linha digitada é self.textCursor().block().position() + self.textCursor().block().length() - 1
                 # O final do texto digitado é a posição atual do cursor antes do Enter.
                 # Precisamos de um jeito de saber o final do texto digitado antes de adicionar o newline visual.
                 # A forma mais simples é limitar o movimento do cursor pela posição original antes do Enter.
                 # No entanto, como adicionamos o newline visual antes, o cálculo do final da linha muda.
                 # Uma abordagem melhor é limitar o movimento para a direita pela posição atual do cursor ANTES do Enter.
                 # Isso requer armazenar a posição inicial do cursor no keyPressEvent.

                 # Vamos simplificar e apenas limitar o movimento para a direita para não ir além do final da linha atual.
                 # O controle preciso de onde o usuário pode digitar (entre command_start_position e a posição atual)
                 # já é feito implicitamente pelo controle de Backspace e Left.

                 # Verifica se o cursor não está no final do documento ou no final da linha atual
                 if cursor_position_in_document < self.textCursor().document().characterCount() and \
                    cursor.block().position() + cursor.block().length() -1 > cursor_position_in_document: # Verifica se não é o último caractere da linha (quebra de linha)
                    super().keyPressEvent(event)


            elif event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
                 # Implementar histórico de comandos se necessário
                 pass
            elif event.key() == Qt.Key_Delete:
                 # Permite deletar APENAS se estiver após command_start_position (não implementado explicitamente aqui)
                 pass
            elif event.key() == Qt.Key_Home:
                 cursor.movePosition(cursor.StartOfLine)
                 # Mover para a direita APENAS até command_start_position
                 cursor.movePosition(cursor.Right, cursor.MoveAnchor, max(0, self.command_start_position - cursor.position())) # Garante que a posição de movimento não seja negativa
                 self.setTextCursor(cursor)


            elif event.key() == Qt.Key_End:
                 # Mover para o final da linha digitada (antes do newline visual)
                 # A posição do final da linha digitada é a posição do cursor antes do Enter.
                 # Como adicionamos o newline visual, o "fim" da linha é antes do newline.
                 # Isso requer saber a posição original do cursor antes de adicionar o newline visual.
                 # Uma alternativa é mover para o final da linha atual e então um caractere para a esquerda,
                 # se o último caractere for um newline.

                 # Vamos simplificar: move para o final da linha atual
                 cursor.movePosition(cursor.EndOfLine)
                 self.setTextCursor(cursor)


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
