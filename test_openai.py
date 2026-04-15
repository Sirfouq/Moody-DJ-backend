from src.openai_api_comm import search_query_layer
from src.spotify_api_comm import access_client_token
import json

def test_openai_integration():
    print("Testing OpenAI Search Query Generation...")
    
 
    print("\n--- Test Case 1----")
    try:
        result = search_query_layer(user_input="No lyrics , house beat , focus", genre='', artist='')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

    
    # print("\n--- Test Case 2: 'Techno' text with 'Country' genre ---")
    # try:
    #     result = openAI_searchquery_layer(user_input="Techno", genre="country")
    #     print(f"Result: {result}")
    # except Exception as e:
    #     print(f"Error: {e}")

if __name__ == "__main__":
    test_openai_integration()
    # access_token = spotify_client_access_token()
    # print(access_token)
