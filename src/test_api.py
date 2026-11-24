import truststore
truststore.inject_into_ssl()  # lets Python work with Kaspersky

from dotenv import load_dotenv
import anthropic

load_dotenv()  # loads your API key from .env
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=100,
    messages=[{"role": "user", "content": "In one sentence, what is a gas turbine service agreement?"}],
)

print(response.content[0].text)
print(response.usage)