document.addEventListener("DOMContentLoaded", function() {
    const textArea = document.getElementById("user-textarea");
    const promptSubmit = document.getElementById("prompt-submit");
    const loadingWheel = document.getElementById("loading-wheel");
    const msgContainer = document.querySelector("main .all-messages-container");

    /*
    -------------------------------------------------------------
        Auto expand textarea height for user input textarea
    -------------------------------------------------------------
    */
    // :param:
    // :return: new height for text area per line addition
    function adjustHeight() {
        textArea.style.height = 'auto';
        const newHeight = Math.min(textArea.scrollHeight, 300); // 300px is the max height
        textArea.style.height = `${newHeight}px`;

        // Enable or disable scrolling based on content height
        textArea.style.overflowY = textArea.scrollHeight > 300 ? 'auto' : 'hidden';
    }
    // Initial adjustment
    textArea.addEventListener('input', adjustHeight);
    // Adjust on window resize
    window.addEventListener('resize', adjustHeight);


    /*
    -----------------------------------------------------------
    Functions relating to the incoming and outgoing cards
    ----------------------------------------------------------
    */
    function scrollToNewContainer() {
        //msgContainer.scrollIntoView({behavior: 'smooth', block: 'end'});
        msgContainer.scrollTop = msgContainer.scrollHeight;
    }

    // Making card editable
    // :param: element containing the edit button
    // : return: Edit event listener
    function makeEditable(button) {
        const container = button.parentElement.parentElement;
        const actionCancel = container.querySelector('.action-toolbar .cancel-edit-btn');
        const originalP = container.querySelector('p');
        const originalSpan = container.querySelector('.action-toolbar .edit-prompt-btn span');

        // Event Listener for edit button
        // :param:
        // :return: Elements:
        //  - textarea element replacing the p element
        //  - Save button replacing the element button
        function editHandler() {
            const originalPrompt = originalP.textContent;

            const newTextArea = document.createElement('textarea');
            newTextArea.value = originalPrompt;
            newTextArea.style.width = '100%';
            newTextArea.className = 'textarea';

            originalP.replaceWith(newTextArea);
            newTextArea.addEventListener('input', function adjHeight() {
                newTextArea.style.height = 'auto';
                const newHeight = Math.min(newTextArea.scrollHeight, 300); // 300px is the max height
                newTextArea.style.height = `${newHeight}px`;

                // Enable or disable scrolling based on content height
                newTextArea.style.overflowY = newTextArea.scrollHeight > 300 ? 'auto' : 'hidden';
            });

            actionCancel.style.display = 'flex';
            originalSpan.textContent = 'Save';

            button.removeEventListener('click', editHandler);
            button.addEventListener('click', saveHandler);
            actionCancel.addEventListener('click', cancelHandler);

            // Trigger the adjHeight function once to set initial height
            newTextArea.dispatchEvent(new Event('input'));
        }

        // Event Listener for save button
        // :param:
        // :return: Element:
        //  - p element replacing textarea element
        //  - incoming card based off new edited prompt
        async function saveHandler() {
            const newTextArea = container.querySelector('textarea');
            if (newTextArea) {
                const newPrompt = newTextArea.value;
                originalP.textContent = newPrompt;
                newTextArea.replaceWith(originalP);

                actionCancel.style.display = 'none';
                originalSpan.textContent = 'Edit';

                let nextElement = container.parentElement.nextElementSibling;
                while (nextElement) {
                    nextElement.remove();
                    nextElement = container.parentElement.nextElementSibling;
                }

                resetHandlers();
                await addOutgoing(newPrompt);
            }
        }

        // Event Listener for cancel button
        // :param:
        // :return: Element:
        //  - original p element and it's contents
        function cancelHandler() {
            const newTextArea = container.querySelector('textarea');
            if (newTextArea) {
                newTextArea.replaceWith(originalP);
                actionCancel.style.display = 'none';
                originalSpan.textContent = 'Edit';
                resetHandlers();
            }
        }

        // :return: Removes save and cancel handler, then finally adds the edit handler
        function resetHandlers() {
            button.removeEventListener('click', saveHandler);
            actionCancel.removeEventListener('click', cancelHandler);
            button.addEventListener('click', editHandler);
        }

        button.addEventListener('click', editHandler);
    }

    // Adding Outgoing Card
    // :param: String(prompt)
    // :return: On screen, outgoing card
    async function addOutgoing(prompt) {
        if (prompt.trim()) {
            loadingWheel.style.display = 'flex';

            const rsp = await getPromptResponse(prompt);

            const li = document.createElement('li');
            const div = document.createElement('div');
            div.className = 'container outgoing-container';
            const p = document.createElement('p');
            p.textContent = rsp;

            div.appendChild(p);
            li.appendChild(div);
            const ul = document.querySelector('.all-messages-container ul');

            loadingWheel.style.display = 'none';

            ul.appendChild(li);

            scrollToNewContainer();
        }
    }

    // Adding Incoming Card
    // :param: String(prompt)
    // :return: On screen, outgoing card
    function addIncoming(prompt) {
        const li = document.createElement('li');
        const div = document.createElement('div');
        div.className = 'container incoming-container';

        const p = document.createElement('p');
        p.textContent = prompt;

        const actionToolbar = document.createElement('div');
        actionToolbar.className = 'action-toolbar';

        // Creating the action buttons
        const actionCancel = document.createElement('div');
        const actionEdit = document.createElement('div');
        actionCancel.className = 'action cancel-edit-btn';
        actionEdit.className = 'edit-prompt-btn action';

        const cancelIcon = document.createElement('i');
        const editIcon = document.createElement('i');
        cancelIcon.className = 'fa-solid fa-x';
        editIcon.className = 'fa-solid fa-pencil';

        const cancelSpan = document.createElement('span');
        const editSpan = document.createElement('span');
        cancelSpan.textContent = 'Cancel';
        editSpan.textContent = 'Edit';

        // Putting all the elements together
        actionEdit.appendChild(editIcon);
        actionEdit.appendChild(editSpan);
        actionCancel.appendChild(cancelIcon);
        actionCancel.appendChild(cancelSpan);

        actionToolbar.appendChild(actionCancel);
        actionToolbar.appendChild(actionEdit);

        div.appendChild(p);
        div.appendChild(actionToolbar);

        li.appendChild(div);
        const ul = document.querySelector('.all-messages-container ul');
        ul.appendChild(li);
        makeEditable(actionEdit);

        scrollToNewContainer();
    }


    /*
        Requests endpoint for LLM Response
        :Param: String(prompt)
        Response: String(response)
    */
    async function getPromptResponse(prompt) {
        try {
            const rsp = await fetch("http://127.0.0.1:80/get-response", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: prompt })
            });

            if (rsp.status != 200) {
                throw new Error();
            }

            const data = await rsp.json();
            return data.response;

        } catch(error) {
            return "Sorry, it seems something went wrong";
        }
    }

    /*
    -------------------------------
            User Input Container
    -------------------------------
    */
    // Key Press Listener
    textArea.addEventListener("keypress", function(e) {
        if (e.key === "Enter" && !e.shiftKey && textArea.value.trim()) {
            promptSubmit.click();
        }
    });

    // Up Arrow Prompt Submit Listener
    promptSubmit.addEventListener("click", async function(e) {
        addIncoming(textArea.value);
        let userPrompt = textArea.value;
        textArea.value = '';
        await addOutgoing(userPrompt);
    });
});