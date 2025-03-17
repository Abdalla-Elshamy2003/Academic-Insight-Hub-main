import os
import logging
from groq import Groq
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_groq_api():
    """Test the Groq API connection and functionality"""
    
    # Get API key from environment variable
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        logger.error("GROQ_API_KEY not found in environment variables")
        print("ERROR: GROQ_API_KEY not found in environment variables")
        print("Please set the GROQ_API_KEY environment variable or add it to your .env file")
        return False
    
    try:
        # Initialize Groq client
        client = Groq(api_key=api_key)
        
        # Test a simple completion
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello and confirm that the API is working correctly."}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            max_completion_tokens=100
        )
        
        # Print the response
        print("\n=== API TEST RESULTS ===")
        print(f"API Key (first 5 chars): {api_key[:5]}...")
        print(f"Response: {response.choices[0].message.content}")
        print("=== TEST SUCCESSFUL ===\n")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing Groq API: {str(e)}")
        print(f"\nERROR: Failed to connect to Groq API: {str(e)}")
        print("Please check your API key and internet connection")
        return False

if __name__ == "__main__":
    print("\nTesting Groq API connection...")
    success = test_groq_api()
    
    if success:
        print("✅ Groq API is working correctly!")
    else:
        print("❌ Groq API test failed. See error messages above.") 