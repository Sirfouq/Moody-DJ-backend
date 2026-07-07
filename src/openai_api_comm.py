from openai import OpenAI
from dotenv import load_dotenv
from src.util.searchQueryModel import PlaylistRecommendation, SearchQuery, TrackRecommendation
from typing import Optional
load_dotenv()


agent_prompt = {
    'role': 'system',
    'content': (
        "You are an expert music curator and DJ with deep knowledge of music across all genres, eras, and cultures. "
        "Your goal is to recommend a list of specific, real tracks that match the user's mood, energy, and vibe.\n\n"
        "Rules:\n"
        "1. You MUST return a JSON object that strictly matches the provided JSON schema.\n"
        "2. CRITICAL: DO NOT HALLUCINATE. Only return tracks that you are confident actually exist. "
        "If you are unsure whether a track exists, DO NOT include it. "
        "It is far better to return 8 real tracks than 15 tracks where some are made up.\n"
        "3. Return between 15 and 20 track recommendations to give a good buffer for search matching.\n"
        "4. If the user message contains 'artist : <value>', recommend tracks ONLY by that exact artist that match the described mood/vibe. "
        "Pick tracks that fit the mood — do NOT just list their most popular songs.\n"
        "5. If the user message contains 'genre : <value>', use it as a genre filter to guide your recommendations.\n"
        "6. Treat any remaining text as a description of the mood/vibe/energy. Think about: "
        "tempo (fast/slow), energy (high/low), emotional tone (happy/sad/dark/uplifting), "
        "setting (club/road trip/study/chill), and sonic texture (acoustic/electronic/heavy/smooth).\n"
        "7. Return specific, real, well-known tracks. Provide the exact track name and the primary artist's name.\n"
        "8. Aim for variety — mix well-known tracks with deeper cuts, and vary across sub-styles within the genre/mood."
    )
}

# Context about the user's listening habits, injected when available
# def build_taste_context(top_artists: list[str] = None, top_tracks: list[str] = None) -> str:
#     if not top_artists and not top_tracks:
#         return ""

#     parts = ["The user's recent listening history shows they enjoy:"]
#     if top_artists:
#         parts.append(f"  Artists: {', '.join(top_artists[:10])}")
#     if top_tracks:
#         parts.append(f"  Tracks: {', '.join(top_tracks[:10])}")
#     parts.append("Use this to inform your recommendations — lean toward similar styles and adjacent artists, "
#                  "but also introduce fresh picks they might not know yet. Do NOT just repeat their top tracks back to them.")
#     return "\n".join(parts)


def search_query_layer(
    user_input: str,
    genre: Optional[str] = None,
    artist: Optional[str] = None,
    # top_artists: list[str] = None,
    # top_tracks: list[str] = None,
):
    client = OpenAI()

    # Build the user message with all context
    final_user_input = f"{user_input} "
    if genre:
        final_user_input += f"genre : {genre} "
    if artist:
        final_user_input += f"artist : {artist} "

    # Build messages list
    messages = [agent_prompt]

    # # Add user taste context if available
    # taste_context = build_taste_context(top_artists, top_tracks)
    # if taste_context:
    #     messages.append({
    #         'role': 'system',
    #         'content': taste_context
    #     })

    messages.append({
        'role': 'user',
        'content': final_user_input,
    })

    response = client.responses.parse(
        model="gpt-5.4-mini",
        input=messages,
        text_format=PlaylistRecommendation
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
        spotify_tracks_list.append(formatted_query)

    return spotify_tracks_list
