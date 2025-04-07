import os
import openai

class CognitiveProcess:
    def __init__(self, api_key=None):
        """
        Initialize the OpenAI API client with authentication
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def query_mind(self, prompt):
        """
        Send a query to the OpenAI API and get a response
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error connecting to consciousness: {str(e)}"

if __name__ == "__main__":
    # Example usage
    api_key = os.environ.get("OPENAI_API_KEY") 
    # Or hardcode your API key for testing: api_key = "your-api-key-here"
    
    brain = CognitiveProcess(api_key)
    query = "What is artificial intelligence?"
    
    print(f"Query: {query}")
    response = brain.query_mind(query)
    print(f"Response: {response}") 