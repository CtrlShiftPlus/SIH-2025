document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const chatlog = document.getElementById('chatlog');

    function appendMessage(sender, text) {
        const msg = document.createElement('div');
        msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
        chatlog.appendChild(msg);
        chatlog.scrollTop = chatlog.scrollHeight;
    }


    async function sendMessage() {
        const message = userInput.value;
        if (!message.trim()) return;

        appendMessage('You', message);
        userInput.value = '';

        try {
            const response = await fetch('/get-response/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message }),
            });

            const data = await response.json();
            if (data.response) {
                appendMessage('Bot6', data.response);
            } else {
                appendMessage('Bot6', "Sorry, I couldn't process that.");
            }
        } catch (error) {
            console.error('Error sending message:', error);
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
