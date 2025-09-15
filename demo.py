from Chatbot import chatbot


while True:
    user_input = input("Enter your text: ")
    response = chatbot(user_input)
    print(response)

