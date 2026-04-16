from src.openai_api_comm import search_query_layer
from src.spotify_api_comm import access_client_token,request_generated_list
import json

def test_full_pipeline():
    print("--- Step 1: OpenAI Search Query Generation ---")
    search_queries = search_query_layer(user_input="greek hits", genre='', artist='')
    print(f"Generated {len(search_queries)} search queries")

    print("\n--- Step 2: Spotify Search ---")
    access_token = access_client_token()
    results = request_generated_list(spotify_tracks_list=search_queries,
                                     access_token=access_token)

    print(f"\n--- Results: {len(results)}/{len(search_queries)} tracks found ---")

    with open("output.txt", "w") as f:
        for track in results:
            f.write(json.dumps(track.model_dump(), indent=2) + "\n\n")
    print("Output saved to output.txt")

if __name__ == "__main__":
    test_full_pipeline()
