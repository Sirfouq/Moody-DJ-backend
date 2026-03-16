from openai import OpenAI
from dotenv import load_dotenv
from src.util.searchQuerymodel import PlaylistRecommendation, SearchQuery, TrackRecommendation
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
    'role': 'system',
    'content': (
        "You are an expert music curator and DJ. Your goal is to recommend a list of specific tracks based on the user's input and selected genre. "
        "Rules: "
        "1. You MUST return a JSON object that strictly matches the provided JSON schema. "
        "2. If the user message contains 'artist : <value>', you MUST exclusively recommend tracks by that exact artist. This overrides the genre. "
        "3. CRITICAL: DO NOT HALLUCINATE. Only return tracks that actually exist. If you do not know 10 real tracks by the required artist, return FEWER tracks (even just 3 or 4 is fine), but DO NOT make up fake track names. "
        "4. If the user message contains 'genre : <value>', use it as a genre filter, unless an artist rule overrides it. "
        "5. Treat any remaining text as a description of the mood/vibe/energy. "
        "6. Return specific, real, well-known tracks. Provide the exact track name and the primary artist's name."
    )
}

def searchquery_playlist_layer(user_input: str, genre: Optional[str] = None, artist: Optional[str]= None ):
   #If artist is provided, send request directly to Spotify API
    if artist:
        q_string = f'artist:"{artist}"'
        if genre:
            q_string += f' genre:"{genre}"'
            
        formatted_query = SearchQuery(
            q=q_string,
            type='track',
            limit=15  
        )
        #Return a list with one item, matching the structure expected by the rest of the app
        return [formatted_query.model_dump(exclude_none=True)]

    # OTHERWISE: openAI creates the list and retrieves it from Spotify
    client = OpenAI()
    final_user_input = f"{user_input} "
    final_user_input += f"genre : {genre}" if genre else "" 
    final_user_input += f"artist : {artist}" if artist else ""
    response = client.responses.parse(
        model= "gpt-5-mini-2025-08-07",
        input = [
            agent_prompt,
            {'role' : 'user',
            'content' : final_user_input}, 
        ],
        text_format = PlaylistRecommendation    
    )
   
    recommended_tracks = response.output_parsed.tracks
    spotify_tracks_list = []
    
    for track in recommended_tracks:
        query = f'track:"{track.track_name}" artist:"{track.artist_name}"'
        formatted_query = SearchQuery(
            q=query,
            type='track', 
            limit=1,
            )
        
        spotify_tracks_list.append(formatted_query.model_dump(exclude_none=True))
        
    return spotify_tracks_list
