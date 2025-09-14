from Chatbot import chatbot
from Speak import speak
from listan import listen

while True:
    user_input = input("Enter your text ")
    response = chatbot(user_input)
    print(response)
    speak(response)
