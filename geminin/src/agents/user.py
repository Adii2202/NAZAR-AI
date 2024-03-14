# Importing necessary libraries from uagents package
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from uagents import Model

# Defining a model for messages
class Message(Model):
    message: str

# Specifying the address of the gemini ai agent
Gemini_Address = "agent1qwg20ukwk97t989h6kc8a3sev0lvaltxakmvvn3sqz9jdjw4wsuxqa45e8l" # replace your Gemini API key here

# Defining the user agent with specific configuration details
user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint=["http://localhost:8000/submit"],
)
 
# Checking and funding the user agent's wallet if its balance is low
fund_agent_if_low(user.wallet.address())
 
# Event handler for the user agent's startup event
@user.on_event('startup')
async def agent_address(ctx: Context):
    # Logging the user agent's address
    ctx.logger.info(user.address)
    # Prompting for user input and sending it as a message to the gemini agent
    message = str(input('You:'))
    await ctx.send(Gemini_Address, Message(message=message))

async def handle_message(message):
    while True:
        user_message = message
        
        # Check for "new session" command
        if user_message.lower() == "new session":
            # Reset chat session (implementation specific to the library)
            chat = user.start_chat(history=[])  # Replace with appropriate reset method
            print("New chat session started.")
            break

# Handler for receiving messages from gemini agent and sending new request
@user.on_message(model=Message)
async def handle_query_response(ctx: Context, sender: str, msg: Message):
    message = await handle_message(msg.message)
    print(message)

    # Loop for continuous user interaction
    while True:
        # Prompt user for next message
        message = str(input('You: '))

        # Check for exit command
        if message.lower() == 'quit':
            break

        # Send user message to Gemini agent
        await ctx.send(sender, Message(message=message))
