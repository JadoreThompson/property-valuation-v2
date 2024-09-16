document.addEventListener('DOMContentLoaded', async function() {
    const userInputTextArea = document.getElementById('user-input-textarea');
    const userInputSubmitButton = document.getElementById('user-input-button');

    /* API Requests */
    async function getResponse(prompt) {
        let message;
        url = "http://127.0.0.1:80/get-response";

        try {
            const rsp = await fetch(url, {
                method: 'POST',
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({question: prompt})
            });

            if (rsp.status != 200) {
                throw new Error('Something went wrong');
            }

            const data = await rsp.json();
            message = data.response;

        } catch(e) {
            console.log("Error: ", e);
            message = e;
        } finally {
            await addBotMessage(message);
        }
    }

    /* User Input */
    function adjustHeight() {
        userInputTextArea.style.height = 'auto';
        const newHeight = Math.min(userInputTextArea.scrollHeight, 300);
        userInputTextArea.style.height = `${newHeight}px`;

        // Enable or disable scrolling based on content height
        userInputTextArea.style.overflowY = userInputTextArea.scrollHeight > 300 ? 'auto' : 'hidden';
    }
    // Initial adjustment
    userInputTextArea.addEventListener('input', adjustHeight);
    window.addEventListener('resize', adjustHeight);

    userInputSubmitButton.addEventListener('click', function(){
        addUserMessage(userInputTextArea.value.trim());
        userInputTextArea.value = '';
    });

    userInputTextArea.addEventListener('keypress', function(e){
        if (e.key === 'Enter' && !e.shiftKey && userInputTextArea.value.trim()) {
            userInputSubmitButton.click();
        }
    });


    /* Chat Cards */
    async function addUserMessage(question)  {
        const allMessageContainer = document.querySelector('.chat-messages');
        const newDiv = document.createElement('div');
        const editButton = document.createElement('button');

        newDiv.className = 'message user-message';
        newDiv.textContent = question;
        editButton.className = 'action-button edit-button';
        editButton.textContent = 'Edit';

        newDiv.appendChild(editButton);
        allMessageContainer.appendChild(newDiv);
        allMessageContainer.scrollTop = allMessageContainer.scrollHeight;

        await getResponse(question);
    }

    async function addBotMessage(response) {
        const allMessageContainer = document.querySelector('.chat-messages');
        const newDiv = document.createElement('div');
        newDiv.className = 'message bot-message';
        newDiv.textContent = response;

        allMessageContainer.appendChild(newDiv);
        allMessageContainer.scrollTop = allMessageContainer.scrollHeight;
    }
});