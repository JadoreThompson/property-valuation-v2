document.addEventListener('DOMContentLoaded', async function() {
    const userInputTextArea = document.getElementById('user-input-textarea');
    const userInputSubmitButton = document.getElementById('user-input-button');

    /* API Requests */
    async function getResponse(prompt) {
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
            await addBotMessage(data.response);
        } catch(e) {
            console.log("Error: ", e);
        }
    }

    // Testing
    //await getResponse("average price of a house in enfield");


    /* User Input */
    userInputSubmitButton.addEventListener('click', function(){
        addUserMessage(userInputTextArea.value.trim());
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
        newDiv.className = 'message user-message';
        newDiv.textContent = question;

        allMessageContainer.appendChild(newDiv);
        await getResponse(question);
    }

    async function addBotMessage(response) {
        const allMessageContainer = document.querySelector('.chat-messages');
        const newDiv = document.createElement('div');
        newDiv.className = 'message bot-message';
        newDiv.textContent = response;

        allMessageContainer.appendChild(newDiv);
    }
});