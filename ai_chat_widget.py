# No arquivo ai_chat_widget.py

import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer # Adicionado QTimer, Signal
from PyQt5.QtCore import pyqtSignal as Signal
# Precisaremos importar a biblioteca do Gemini mais tarde
# import google.generativeai as genai

class AIChatWidget(QWidget):
    # Sinal opcional para indicar que a IA está digitando/processando
    thinking_status = Signal(bool)

    def __init__(self, parent=None, api_key=None):
        super().__init__(parent)

        # **Configurar a API do Gemini (precisa da chave)**
        self.api_key = api_key
        self.model = None # Instância do modelo Gemini
        # if self.api_key:
        #     try:
        #         genai.configure(api_key=self.api_key)
        #         # Inicializar o modelo de conversação (chat)
        #         # self.model = genai.GenerativeModel('gemini-1.5-flash-latest') # Ou outro modelo
        #         # self.chat_session = self.model.start_chat(history=[]) # Iniciar uma nova sessão de chat
        #     except Exception as e:
        #         print(f"Erro ao configurar a API do Gemini: {e}")
        # else:
        #     print("Chave de API do Gemini não fornecida. O chat de IA não estará funcional.")


        self.initUI()
        # self.thinking_status.connect(self.update_send_button_status) # Conecta sinal para atualizar botão


    def initUI(self):
        # Layout principal vertical
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Área de histórico da conversa
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True) # Apenas para exibir o histórico
        main_layout.addWidget(self.history_display)

        # Área de entrada do usuário e botão
        input_layout = QHBoxLayout()
        main_layout.addLayout(input_layout)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Digite sua mensagem para a IA aqui...")
        self.user_input.returnPressed.connect(self.send_message) # Envia mensagem ao pressionar Enter
        input_layout.addWidget(self.user_input)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message) # Envia mensagem ao clicar no botão
        input_layout.addWidget(self.send_button)

        # Adicionar uma mensagem inicial no histórico
        self.append_message("IA", "Olá! Como posso ajudar com seu código hoje?")


    def append_message(self, sender, message):
        # Adiciona uma mensagem formatada ao histórico
        formatted_message = f"<b>{sender}:</b> {message}<br>"
        self.history_display.append(formatted_message) # Usa append para adicionar nova linha


    def send_message(self):
        user_text = self.user_input.text().strip()
        if user_text:
            self.append_message("Você", user_text) # Exibe a mensagem do usuário no histórico
            self.user_input.clear() # Limpa a área de entrada
            self.user_input.setDisabled(True) # Desabilita a entrada enquanto espera a resposta
            self.send_button.setDisabled(True) # Desabilita o botão Enviar

            # **TODO: Chamar a API do Gemini aqui de forma assíncrona**
            print(f"Enviando para IA: {user_text}") # Debug print

            # Simulação de resposta da IA (remover depois)
            QTimer.singleShot(1000, lambda: self.receive_ai_response(f"Simulação de resposta para: {user_text}"))


    def receive_ai_response(self, ai_text):
        # Chamado quando a resposta da IA é recebida
        self.append_message("IA", ai_text) # Exibe a resposta da IA no histórico
        self.user_input.setDisabled(False) # Reabilita a entrada
        self.send_button.setDisabled(False) # Reabilita o botão
        self.user_input.setFocus() # Retorna o foco para a área de entrada

        # Opcional: Emitir sinal para indicar que a IA terminou de "pensar"
        # self.thinking_status.emit(False)

    # Slot para atualizar o status do botão (conectado ao sinal thinking_status)
    # def update_send_button_status(self, thinking):
    #     if thinking:
    #         self.send_button.setText("Pensando...")
    #         self.send_button.setDisabled(True)
    #         self.user_input.setDisabled(True)
    #     else:
    #         self.send_button.setText("Enviar")
    #         self.send_button.setDisabled(False)
    #         self.user_input.setDisabled(False)
    #         self.user_input.setFocus()


# Exemplo básico de uso (para teste individual do widget)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Substitua "SUA_CHAVE_DE_API" pela sua chave real para teste individual
    # chat_widget = AIChatWidget(api_key="SUA_CHAVE_DE_API")
    chat_widget = AIChatWidget() # Sem chave de API por padrão no exemplo
    chat_widget.setWindowTitle("Chat de IA Básico")
    chat_widget.resize(400, 600)
    chat_widget.show()
    sys.exit(app.exec_())
