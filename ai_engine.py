# ai_engine.py
from groq import Groq

# Initialize the Groq client with your API key
client = Groq(
    api_key="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"
)

def query_ollama_context(prompt_content, context_data="", model_name="llama-3.3-70b-versatile"):
    """
    Routes portfolio analytics queries to Groq Cloud's Llama 3.3 engine.
    (Kept function name as query_ollama_context to avoid breaking callbacks.py imports)
    """
    # Combine system guidelines, the raw spreadsheet context, and your actual question
    full_prompt = f"{prompt_content}\n\n[CONTEXT_DATA]:\n{context_data}" if context_data else prompt_content

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            model=model_name,
            temperature=0.2, # Low temperature for analytical accuracy
        )
        
        # Extract and return the text response
        reply = chat_completion.choices[0].message.content
        return reply if reply else "⚠️ Received a blank response from Groq."
        
    except Exception as e:
        return f"⚠️ Groq API Error: {str(e)}"