from flask import Flask, request, jsonify, render_template
from ollama import chat
from app import get_embedding, UserSession, collection  # Importing your app functions

app = Flask(__name__)

# Create a user session
session = UserSession()

# Route for the main chat page (index.html)
@app.route('/')
def index():
    return render_template('index.html')  # Ensure index.html is placed in the templates folder

# Route to handle the chat interaction
@app.route('/chat', methods=['POST'])
def chat_route():
    try:
        # Get query from the POST request
        data = request.get_json()
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Process the query and generate an answer
        answer = chat_agent(query)

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def chat_agent(query: str) -> str:
    # Step 1: Get the query embedding
    query_embedding = get_embedding(query)
    if query_embedding is None:
        return "Error obtaining query embedding."

    # Step 2: Query ChromaDB for relevant documents (up to 3 results)
    try:
        results = collection.query(query_embeddings=[query_embedding], n_results=3)  # Get top 3 results
    except Exception as e:
        return f"Error querying ChromaDB: {str(e)}"

    # Step 3: If no results found in ChromaDB, fallback to Ollama (without ChromaDB context)
    if not results or "documents" not in results or not results["documents"]:
        # No relevant documents found, use Ollama directly
        return ollama_chat(query, "")

    # Step 4: Combine ChromaDB results into a context (join top results)
    documents = results["documents"][0]
    context = " ".join(documents)  # Combine top documents as the context for Ollama

    if not context.strip():
        # If context is empty, fallback to Ollama without additional context
        return ollama_chat(query, "")

    session_context = session.get_context()  # Get the accumulated context


# Step 5: Combine original query and ChromaDB context for a final prompt to Ollama
    combined_prompt = f"User query: {query}\n\nRelevant Information from Documents:\n{context}"

    # Step 6: Get the session context (if any) to pass to Ollama
    # Combine the session context with the query and ChromaDB context
    final_prompt = f"{session_context}\n\n{combined_prompt}"

    # Step 7: Send the final prompt to Ollama for the response
    answer = ollama_chat(query, final_prompt)

    # Step 7: Optionally, update the session context (for follow-up queries)
    session.update_context(query, answer)

    return answer

def ollama_chat(query: str, context: str) -> str:
    """
    This function interacts with Ollama, sending it either just the query or the combined query and context.
    """
    system_message = (
        "You are an expert chatbot that provides accurate answers based on the user's query and provided context. "
        "If there is no context provided, give a general answer based on your knowledge."
    )

    try:
        # If context is provided, use it in the prompt
        if context.strip():
            messages = [
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': f"{context}\n\n{query}"}
            ]
        else:
            # No context found, just ask Ollama the original question
            messages = [
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': query}
            ]

        # Send the combined prompt to Ollama
        response = chat(
            model='llama3.1:8b',  # Ensure you're using the correct model
            messages=messages,
            stream=False  # Set to True if you want to handle streaming responses
        )
        return response['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"


# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True)
