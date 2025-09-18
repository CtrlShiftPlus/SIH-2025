document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const chatlog = document.getElementById('chatlog');

    function appendMessage(sender, text, isHTML = false) {
        const msg = document.createElement('div');
        msg.classList.add('message');
        msg.classList.add(sender === 'You' ? 'user-message' : 'bot-message');

        if (isHTML) {
            msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
        } else {
            msg.textContent = `${sender}: ${text}`;
        }

        chatlog.appendChild(msg);
        chatlog.scrollTop = chatlog.scrollHeight;
    }

    async function sendMessage() {
    const message = document.getElementById('user-input').value; // your input box id
    const language = document.getElementById('language-select').value; // get selected language
    if (!message.trim()) return;

    // Show user message immediately
    appendMessage('You', message);

    // Clear input
    document.getElementById('user-input').value = '';

    try {
        const response = await fetch('/get-response/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message, language: language }), // send message & language
        });

        const data = await response.json();
        if (data.response) {
            appendMessage('Bot6', data.response, true);
        } else {
            appendMessage('Bot6', "Sorry, I couldn't process that.");
        }
    } catch (error) {
        console.error('Error:', error);
        appendMessage('Bot6', "Sorry, something went wrong.");
    }
}

    sendBtn.addEventListener('click', sendMessage);

    userInput.addEventListener('keydown', (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
});
