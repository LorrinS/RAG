function sendQuery() {
    const query = document.getElementById("user-query").value;
    if (query.trim() === "") return;

    const chatContent = document.getElementById("chat-content");

    // Display user's question in the chat
    const userMessage = document.createElement("p");
    userMessage.textContent = "You: " + query;
    chatContent.appendChild(userMessage);

    // Send the query to the server using fetch API
    fetch("/ask", {
        method: "POST",
        body: new URLSearchParams({
            query: query
        }),
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    })
    .then(response => response.json())
    .then(data => {
        // Display bot's answer in the chat
        const botMessage = document.createElement("p");
        botMessage.textContent = "Bot: " + data.answer;
        chatContent.appendChild(botMessage);

        // Clear the input field
        document.getElementById("user-query").value = "";
        chatContent.scrollTop = chatContent.scrollHeight; // Scroll to the bottom
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
