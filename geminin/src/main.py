from flask import Flask, request
from agents.user import user  # Imports the user agent configuration
from agents.gemini_agent import Gemini_agent  # Imports the Gemini agent configuration
from uagents import Bureau

app = Flask(__name__)
bureau = Bureau(endpoint="http://127.0.0.1:5000/submit", port=8000)
bureau.add(Gemini_agent)
bureau.add(user)

# Global variable to store the current chat session (initially empty)
chat_session = None

# The default endpoint handling incoming requests
@app.route("/", methods=["POST"])
def handle_request():
    global chat_session  # Access the global chat session variable

    data = request.json  # Assuming the request contains JSON data
    message = data.get("message")  # Extract the message from the JSON

    try:
        # Check if a chat session is already ongoing
        if chat_session is None:
            # Start a new chat session for the first request
            chat_session = Gemini_agent.model.start_chat(history=[])
            print("New chat session started.")

        # Forward the message to the current chat session
        response = chat_session.send_message(message, stream=True)

        # Process the response (accumulate chunks if necessary)
        full_response_text = ""
        for chunk in response:
            full_response_text += chunk.text
        response = "Gemini: " + full_response_text

        return response, 200  # Return the response with a success status code

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"An error occurred while processing the request.", 500

    finally:
        # Reset chat session if user enters a specific command (e.g., "new session")
        if message.lower() == "new session":
            chat_session = None
            print("Chat session reset.")



# Start the Bureau and Flask app
if __name__ == "__main__":
    bureau.run()
    app.run(host="0.0.0.0", port=80, debug=True)
