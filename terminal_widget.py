# No arquivo terminal_widget.py

import sys
import subprocess
from PyQt5.QtWidgets import QPlainTextEdit, QApplication, QVBoxLayout
from PyQt5.QtCore import QProcess, QTextCodec, QByteArray, QIODevice, QTimer, Qt, QPoint
from PyQt5.QtCore import pyqtSignal as Signal # Importação corrigida
import threading
import os

class CustomTerminalWidget(QPlainTextEdit):
    # Sinal para emitir a saída do terminal de forma segura para a UI thread
    output_received = Signal(str)


    def __init__(self, parent=None, shell_program=None):
        super().__init__(parent)

        # Tentar encontrar o shell bash ou cmd/powershell no Windows
        if shell_program is None:
            if sys.platform.startswith('linux') or sys.platform == 'darwin':
                shell_program = "bash"
            elif sys.platform == 'win32':
                # No Windows, tentar cmd.exe ou powershell.exe
                shell_program = "cmd.exe"
                # shell_program = "powershell.exe" # Opcional: tentar Powershell
            else:
                shell_program = "sh" # Fallback para sh

        self.shell_program = shell_program
        self.process = None
        self.command_start_position = 0 # Rastreia o início da linha de comando

        self.setReadOnly(True) # Inicialmente somente para exibição
        self.appendPlainText(f"Iniciando terminal com: {self.shell_program}...\n")

        # Conecta o sinal output_received ao slot para exibir a saída
        self.output_received.connect(self.appendPlainText)

        self.start_shell()


    def start_shell(self):
        try:
            # Inicia o subprocesso do shell
            # stdout e stderr são redirecionados para PIPE
            # stdin também é redirecionado para PIPE para que possamos enviar comandos
            # cwd (current working directory) pode ser definido se necessário para iniciar na pasta do projeto
            # cwd=os.getcwd() # Exemplo: iniciar na pasta atual do script

            self.process = subprocess.Popen(
                self.shell_program,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Decodifica stdout/stderr como texto
                bufsize=1, # Buffer de linha para stdout/stderr
                universal_newlines=True # Sinônimo para text em versões mais recentes
                # shell=True # Use shell=True se precisar que o comando seja executado através do shell do sistema (pode ser necessário para alguns comandos)
            )

            # Lê a saída do stdout e stderr em threads separadas para não bloquear a UI
            # daemon=True para encerrar as threads automaticamente com o programa
            import threading
            threading.Thread(target=self.read_output, args=(self.process.stdout, False), daemon=True).start()
            threading.Thread(target=self.read_output, args=(self.process.stderr, True), daemon=True).start()

            # **Após iniciar o shell, tornar o widget editável e definir a posição inicial da linha de comando**
            # Usar singleShot para garantir que isso rode na UI thread após a inicialização da janela
            QTimer.singleShot(100, self.after_shell_start) # Pequeno atraso para a UI thread estar pronta


        except FileNotFoundError:
            self.appendPlainText(f"Erro: Programa do shell '{self.shell_program}' não encontrado.\n")
            self.setReadOnly(False) # Permitir edição para ver a mensagem de erro e tentar digitar
        except Exception as e:
            self.appendPlainText(f"Erro ao iniciar o shell: {e}\n")
            self.setReadOnly(False) # Permitir edição para ver a mensagem de erro e tentar digitar


    def after_shell_start(self):
         print("after_shell_start chamado.") # Debug print
         self.setReadOnly(False)
         print("Widget definido como editável.") # Debug print
         self.moveCursor(self.textCursor().End) # Move o cursor para o final
         self.command_start_position = self.textCursor().position() # Salva a posição do cursor
         # Opcional: Adicionar um prompt inicial se o shell não enviar um imediatamente
         # self.insertPlainText("$ ")
         # self.command_start_position = self.textCursor().position() # Atualiza após adicionar o prompt


    def read_output(self, pipe, is_stderr):
        try:
            print(f"Thread de leitura ({'stderr' if is_stderr else 'stdout'}) iniciada.") # Debug print
            for line in iter(pipe.readline, ''):
                print(f"Thread de leitura ({'stderr' if is_stderr else 'stdout'}) recebeu linha: {line.strip()}") # Debug print
                self.output_received.emit(line)

            print(f"Thread de leitura ({'stderr' if is_stderr else 'stdout'}) finalizada.") # Debug print
            self.output_received.emit(f"\nProcesso do shell ({self.shell_program}) encerrado.\n")


        except Exception as e:
            print(f"Thread de leitura ({'stderr' if is_stderr else 'stdout'}) encontrou erro: {e}") # Debug print
            self.output_received.emit(f"\nErro na leitura do pipe ({'stderr' if is_stderr else 'stdout'}): {e}\n")


    # Slot conectado ao sinal output_received
    def appendPlainText(self, text):
        # Adiciona texto ao widget e rola para o final
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.ensureCursorVisible() # Garante que o cursor (e o texto adicionado) esteja visível


    # Método para enviar comandos para o shell
    def send_command(self, command):
        if self.process and self.process.stdin:
            try:
                print(f"Enviando comando: {command}") # Debug print
                # Adiciona a linha digitada e uma nova linha visualmente antes de enviar
                self.appendPlainText(command + '\n')
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()
                self.setReadOnly(True) # Torna somente leitura enquanto espera a resposta
                print("Widget definido como somente leitura (enviando comando).") # Debug print


            except Exception as e:
                print(f"Erro ao enviar comando: {e}") # Debug print
                self.appendPlainText(f"Erro ao enviar comando: {e}\n")
                self.setReadOnly(False)
                self.moveCursor(self.textCursor().End)
                self.command_start_position = self.textCursor().position() # Redefinir posição de início

        else:
            print("send_command: Shell não iniciado ou stdin não disponível.") # Debug print
            self.appendPlainText("Shell não iniciado ou stdin não disponível.\n")


    # Lidar com eventos de teclado
    def keyPressEvent(self, event):
        if self.process and self.process.stdin and not self.isReadOnly():
            cursor = self.textCursor()
            cursor_position_in_document = cursor.position()

            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                cursor.movePosition(cursor.End)
                cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
                current_line_with_prompt = cursor.selectedText()

                # Extrair o texto digitado pelo usuário
                # Calcula a posição relativa do cursor dentro do bloco atual
                cursor_pos_in_block = cursor_position_in_document - cursor.block().position()
                # Calcula a posição de início do comando dentro do bloco atual
                command_start_pos_in_block = self.command_start_position - cursor.block().position()
                # Pega o texto a partir da posição de início do comando dentro do bloco atual
                command_text = current_line_with_prompt[command_start_pos_in_block:]


                self.send_command(command_text.strip()) # Envia o comando (remove espaços em branco no início/fim)


            # Lidar com Backspace
            elif event.key() == Qt.Key_Backspace:
                 # Apenas apagar se o cursor estiver após a posição de início do comando
                 if cursor_position_in_document > self.command_start_position:
                     cursor.deletePreviousChar()
                     # Não chamar super().keyPressEvent para evitar comportamento padrão
                 # else: ignorar backspace antes do início do comando

            # TODO: Implementar movimentação básica do cursor na linha de comando
            # Evitar que o cursor vá para linhas anteriores ou antes do início do comando
            elif event.key() == Qt.Key_Left:
                if cursor_position_in_document > self.command_start_position:
                    super().keyPressEvent(event) # Permite mover para a esquerda
            elif event.key() == Qt.Key_Right:
                 # Permitir mover para a direita, mas não além do final da linha atual (onde o cursor está)
                 # Precisa verificar a posição do cursor
                 if cursor_position_in_document < self.textCursor().block().position() + self.textCursor().block().length() - 1: # -1 para não ir para o newline invisível
                      super().keyPressEvent(event) # Permite mover para a direita

            elif event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
                 # TODO: Implementar histórico de comandos
                 pass # Ignora teclas de seta para cima/baixo por enquanto
            elif event.key() == Qt.Key_Delete:
                 # TODO: Implementar tecla Delete
                 pass # Ignora tecla Delete por enquanto
            elif event.key() == Qt.Key_Home:
                 # Mover para a posição de início do comando
                 cursor.movePosition(cursor.StartOfLine)
                 cursor.movePosition(cursor.Right, cursor.MoveAnchor, self.command_start_position - cursor.position())
                 self.setTextCursor(cursor)

            elif event.key() == Qt.Key_End:
                 # Mover para o final da linha atual
                 self.moveCursor(self.textCursor().End)


            else:
                # Para outras teclas (caracteres normais), adicionar o texto na posição do cursor
                super().keyPressEvent(event) # Permite a inserção de texto
                # Não move o cursor para o final aqui para permitir edição no meio da linha (básico)


        else:
            # Comportamento padrão para teclas quando o terminal não está editável ou processo não iniciado
            super().keyPressEvent(event)


    # Lidar com o fechamento do widget (terminar o processo do shell)
    def closeEvent(self, event):
        if self.process:
            try:
                self.process.terminate() # Tenta encerrar o processo gracefully
                self.process.wait(timeout=1) # Espera um pouco pelo encerramento
            except subprocess.TimeoutExpired:
                self.process.kill() # Se não encerrar, mata o processo
            except Exception as e:
                print(f"Erro ao encerrar processo do shell: {e}") # Imprime no console de depuração


        super().closeEvent(event)


# Exemplo básico de uso (para teste individual do widget)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Tentar detectar o shell apropriado
    shell_to_use = None
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        shell_to_use = "bash"
    elif sys.platform == 'win32':
        shell_to_use = "cmd.exe"
        # shell_to_use = "powershell.exe" # Opcional: tentar Powershell
    else:
        shell_to_use = "sh" # Fallback para sh

    terminal = CustomTerminalWidget(shell_program=shell_to_use)
    terminal.setWindowTitle("Terminal Básico")
    terminal.resize(600, 400)
    terminal.show()

    sys.exit(app.exec_())
