import sys
import subprocess
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtCore import QProcess, QTextCodec, QByteArray, QIODevice, QTimer, Signal, Qt
import threading
import os # Importar os para encontrar o shell


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
                # shell_program = "powershell.exe"
            else:
                shell_program = "sh" # Fallback para sh

        self.shell_program = shell_program
        self.process = None

        self.setReadOnly(False) # Permitir que o usuário digite
        self.appendPlainText(f"Iniciando terminal com: {self.shell_program}...\n")

        # Conecta o sinal output_received ao slot para exibir a saída
        self.output_received.connect(self.appendPlainText)


        self.start_shell()


    def start_shell(self):
        try:
            # Inicia o subprocesso do shell
            self.process = subprocess.Popen(
                self.shell_program,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Decodifica stdout/stderr como texto
                bufsize=1, # Buffer de linha para stdout/stderr
                universal_newlines=True # Sinônimo para text em versões mais recentes
            )

            # Lê a saída do stdout e stderr em threads separadas para não bloquear a UI
            threading.Thread(target=self.read_output, args=(self.process.stdout, False), daemon=True).start() # daemon=True para encerrar com o programa
            threading.Thread(target=self.read_output, args=(self.process.stderr, True), daemon=True).start() # daemon=True para encerrar com o programa


        except FileNotFoundError:
            self.appendPlainText(f"Erro: Programa do shell '{self.shell_program}' não encontrado.\n")
        except Exception as e:
            self.appendPlainText(f"Erro ao iniciar o shell: {e}\n")


    def read_output(self, pipe, is_stderr):
        # Lê a saída do pipe e emite um sinal para a UI thread
        try:
            for line in iter(pipe.readline, ''):
                self.output_received.emit(line)
        except Exception as e:
            # Emite erro para a UI thread também
            self.output_received.emit(f"Erro na leitura do pipe ({'stderr' if is_stderr else 'stdout'}): {e}\n")


    # Método para enviar comandos para o shell
    def send_command(self, command):
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(command + '\n') # Envia o comando com uma quebra de linha
                self.process.stdin.flush() # Garante que o comando seja enviado imediatamente
            except Exception as e:
                self.appendPlainText(f"Erro ao enviar comando: {e}\n")
        else:
            self.appendPlainText("Shell não iniciado ou stdin não disponível.\n")


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


    # Permitir que o usuário digite no terminal e enviar comandos
    def keyPressEvent(self, event):
        if self.process and self.process.stdin:
            # Se a tecla Enter for pressionada, envie a linha atual como comando
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # Obter o texto da última linha digitada (considerando que o cursor está no final)
                # Para simulação básica, apenas obter a última linha
                current_line = self.document().lastBlock().text()
                self.appendPlainText('') # Adiciona uma nova linha para o próximo prompt (simulação)
                self.send_command(current_line)
                # TODO: Limpar a linha digitada após enviar (requer controle do cursor)

            elif event.key() == Qt.Key_Backspace:
                 # Simulação de backspace (remove o último caractere da última linha)
                 cursor = self.textCursor()
                 cursor.movePosition(cursor.End)
                 if cursor.positionInBlock() > 0:
                      cursor.deletePreviousChar()

            else:
                # Para outras teclas, adicione o texto ao final do documento (simulação de digitação)
                # TODO: Lidar com outras teclas especiais (setas, delete, etc.) para simular um terminal real
                super().keyPressEvent(event)


        else:
             # Comportamento padrão se o shell não estiver rodando
             super().keyPressEvent(event)


# Exemplo básico de uso (para teste individual do widget)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Tentar detectar o shell apropriado
    shell_to_use = None
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        shell_to_use = "bash"
    elif sys.platform == 'win32':
        shell_to_use = "cmd.exe"
        # shell_to_use = "powershell.exe"
    else:
        shell_to_use = "sh"

    terminal = CustomTerminalWidget(shell_program=shell_to_use)
    terminal.setWindowTitle("Terminal Básico")
    terminal.resize(600, 400)
    terminal.show()

    sys.exit(app.exec_())