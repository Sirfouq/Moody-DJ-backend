from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


def openAi_request(message :str):
    client = OpenAI()

    response = client.responses.create(
        model="gpt-5-mini",
        input=message
    )
    return response.model_dump_json()



