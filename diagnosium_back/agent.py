from google.adk.agents import agent

@agent(
  model="gemini-1.0-pro",
  name="duck_name_generator",
  description="Create a fun name for a pet duck",
  instruction="Create a fun name for a pet duck when asked. Respond only with the name."
)
def generate_duck_name(input_text):
  return input_text
