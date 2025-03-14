import openai
import json
import os
import nearai

hub_url = "https://api.near.ai/v1"

# Login to NEAR AI Hub using nearai CLI.
# Read the auth object from ~/.nearai/config.json
auth = nearai.config.load_config_file()["auth"]
signature = json.dumps(auth)

client = openai.OpenAI(base_url=hub_url, api_key=signature)
models = client.models.list()
print(models)

providers = set([model.id.split("::")[0] for model in models])
print(providers)
