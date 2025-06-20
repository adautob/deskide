# No arquivo ai_chat_widget.py

import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal as Signal, QThread, QObject, pyqtSlot # Adicionado QThread, QObject, pyqtSlot

# **Importar a biblioteca do Gemini**
import google.generativeai as genai

# Classe Worker para chamar a API do Gemini em uma thread separada
class GeminiWorker(QObject):
    # Sinais para comunicar com a thread principal
    finished = Signal() # Sinal emitido quando a tarefa termina
    response_ready = Signal(str) # Sinal emitido quando a resposta da IA está pronta
    error = Signal(str) # Sinal emitido em caso de erro

    def __init__(self, chat_session, user_message):
        super().__init__()
        self.chat_session = chat_session
        self.user_message = user_message

    @pyqtSlot() # Decorador para indicar que este método é um slot (será chamado na thread)
    def run(self):
        """Executa a chamada para a API do Gemini."""
        try:
            print(f"Worker: Enviando mensagem para a API: {self.user_message}") # Debug print
            # Enviar a mensagem do usuário para a sessão de chat do Gemini
            response = self.chat_session.send_message(self.user_message)
            print(f"Worker: Resposta da API recebida: {response}") # Debug print

            # Extrair o texto da resposta
            ai_text = ""
            try:
                ai_text = response.text # Tenta obter o texto diretamente
            except Exception as e:
                ai_text = f"Erro ao extrair texto da resposta da IA: {e}\n{response}" # Exibe a resposta completa em caso de erro


            print(f"Worker: Texto da IA extraído: {ai_text}") # Debug print
            self.response_ready.emit(ai_text) # Emite o sinal com a resposta

        except Exception as e:
            print(f"Worker: Erro na chamada da API: {e}") # Debug print
            self.error.emit(f"Erro na comunicação com a IA: {e}") # Emite o sinal de erro

        finally:
            self.finished.emit() # Emite o sinal de finalização


class AIChatWidget(QWidget):
    thinking_status = Signal(bool)

    def __init__(self, parent=None, api_key=None):
        super().__init__(parent)

        # **Configurar a API do Gemini (precisa da chave)**
        self.api_key = api_key
        self.model = None
        self.chat_session = None # A sessão de chat do Gemini

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Inicializar o modelo de conversação (chat)
                # Usando um modelo que suporta chat
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest') # Use o modelo apropriado
                self.chat_session = self.model.start_chat(history=[]) # Iniciar uma nova sessão de chat com histórico vazio
                print("API do Gemini configurada e sessão de chat iniciada.") # Debug print
            except Exception as e:
                print(f"Erro ao configurar a API do Gemini ou iniciar sessão de chat: {e}")
                self.append_message("Sistema", f"Erro ao configurar a API do Gemini: {e}. O chat de IA não estará funcional.")
                self.api_key = None # Invalidar a chave se a configuração falhar
        else:
            print("Chave de API do Gemini não fornecida. O chat de IA não estará funcional.")
            self.append_message("Sistema", "Chave de API do Gemini não fornecida. O chat de IA não estará funcional.")


        self.initUI()
        self.thinking_status.connect(self.update_send_button_status)


    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        main_layout.addWidget(self.history_display)

        input_layout = QHBoxLayout()
        main_layout.addLayout(input_layout)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Digite sua mensagem para a IA aqui...")
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        self.append_message("IA", "Olá! Como posso ajudar com seu código hoje?")

    def append_message(self, sender, message):
        formatted_message = f"<b>{sender}:</b> {message}<br>"
        self.history_display.append(formatted_message)
        self.history_display.ensureCursorVisible() # Garante que o texto adicionado seja visível


    def send_message(self):
        if not self.chat_session:
             self.append_message("Sistema", "Sessão de chat da IA não iniciada. Verifique sua chave de API.")
             return # Sai se a sessão de chat não estiver pronta

        user_text = self.user_input.text().strip()
        if user_text:
            self.append_message("Você", user_text)
            self.user_input.clear()
            self.user_input.setDisabled(True)
            self.send_button.setDisabled(True)
            self.thinking_status.emit(True) # Indica que a IA está pensando

            # **Criar Worker e Thread para chamar a API**
            self.thread = QThread() # Cria uma nova thread
            self.worker = GeminiWorker(self.chat_session, user_text) # Cria o worker com a sessão de chat e mensagem
            self.worker.moveToThread(self.thread) # Move o worker para a thread

            # Conectar sinais do worker aos slots no widget principal
            self.thread.started.connect(self.worker.run) # Quando a thread iniciar, execute o método run do worker
            self.worker.finished.connect(self.thread.quit) # Quando o worker terminar, saia da thread
            self.worker.finished.connect(self.worker.deleteLater) # Limpa o worker da memória
            self.thread.finished.connect(self.thread.deleteLater) # Limpa a thread da memória

            # Conectar sinais de resposta/erro do worker aos slots no widget principal
            self.worker.response_ready.connect(self.receive_ai_response)
            self.worker.error.connect(self.handle_ai_error)


            self.thread.start() # Inicia a thread

            print(f"Mensagem do usuário enviada para processamento da API.")


    @pyqtSlot(str) # Indica que este slot espera uma string
    def receive_ai_response(self, ai_text):
        # Chamado quando a resposta da IA é recebida do worker
        print(f"Recebendo resposta da IA: {ai_text}") # Debug print
        self.append_message("IA", ai_text)
        # Reabilitação da UI acontece no slot handle_api_task_finished (conectado ao worker.finished)
        # self.user_input.setDisabled(False)
        # self.send_button.setDisabled(False)
        # self.user_input.setFocus()


    @pyqtSlot(str) # Indica que este slot espera uma string de erro
    def handle_ai_error(self, error_message):
        # Chamado em caso de erro na chamada da API
        print(f"Erro da API da IA: {error_message}") # Debug print
        self.append_message("Sistema", f"Erro na comunicação com a IA: {error_message}")
        # Reabilitação da UI acontece no slot handle_api_task_finished (conectado ao worker.finished)


    @pyqtSlot() # Indica que este slot não espera argumentos
    def handle_api_task_finished(self):
        # Chamado quando a tarefa da API (sucesso ou erro) termina
        print("Tarefa da API finalizada. Reabilitando UI.") # Debug print
        self.user_input.setDisabled(False)
        self.send_button.setDisabled(False)
        self.user_input.setFocus()
        self.thinking_status.emit(False) # Indica que a IA terminou de pensar


    @pyqtSlot(bool) # Indica que este slot espera um booleano
    def update_send_button_status(self, thinking):
        # Slot para atualizar o status visual do botão e entrada
        if thinking:
            self.send_button.setText("Pensando...")
            self.send_button.setDisabled(True)
            self.user_input.setDisabled(True)
        else:
            self.send_button.setText("Enviar")
            self.send_button.setDisabled(False)
            self.user_input.setDisabled(False)
            self.user_input.setFocus()


# Exemplo básico de uso (para teste individual do widget)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Substitua "SUA_CHAVE_DE_API" pela sua chave real para teste individual
    # Gerencie sua chave de API de forma segura (variáveis de ambiente, arquivo de configuração)
    # NUNCA inclua sua chave diretamente no código fonte compartilhado.
    # Exemplo: ler de uma variável de ambiente
    # import os
    # api_key = os.environ.get("GEMINI_API_KEY")
    api_key = "AIzaSyBZl62T-QP2U8aVtvcWY5k8Y2Dv4veeZeQ" # Substitua ou use o método seguro

    chat_widget = AIChatWidget(api_key=api_key)
    chat_widget.setWindowTitle("Chat de IA Básico com Gemini")
    chat_widget.resize(400, 600)
    chat_widget.show()
    sys.exit(app.exec_())
