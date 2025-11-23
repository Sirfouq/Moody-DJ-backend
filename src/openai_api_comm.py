from openai import OpenAI
from dotenv import load_dotenv
from src.util.searchQuerymodel import SearchQuery
from typing import Optional
load_dotenv()


def openAi_request(message :str):
    client = OpenAI()

    response = client.responses.create(
        model="gpt-5-mini",
        input=message
    )
    return response.model_dump_json()

agent_prompt = {
    'role' : 'system',
    'content': (
    "You are a music search assistant. Your goal is to generate a Spotify search query based on the users input and selected genre. "
    "Rules: "
    "1. If the user message contains 'genre : <value>', that is the MANDATORY genre filter. You MUST use 'genre:<value>' in the 'q' field. "
    "2. Treat any other text in the user input as a description of the mood/vibe/energy. "
    "3. STRICTLY IGNORE any other genre names mentioned in the user text. ONLY use the mandatory genre from Rule 1. "
    "4. Do NOT use generic mood words (like 'uplifting', 'sad', 'happy') as literal search terms. Instead, convert them into descriptive acoustic characteristics (e.g., use 'driving melodic' instead of 'uplifting')."
    )

}

def openAI_searchquery_layer(user_input: str, genre: Optional[str] = None):
    client = OpenAI()
    final_user_input = f"{user_input} "
    final_user_input += f"genre : {genre}" if genre else ""
    response = client.responses.parse(
        model= "gpt-5-mini",
        input = [
            agent_prompt,
            {'role' : 'user',
            'content' : final_user_input}
        ],
        text_format = SearchQuery
    )
    return response.output_parsed.model_dump_json()
