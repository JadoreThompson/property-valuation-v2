document.addEventListener('DOMContentLoaded', async function() {
    const userEmail = document.querySelector(".user-email").textContent;

    // Room Consts
    const newRoomBtn = document.getElementById('new-room-btn');
    const createRoomOverlay = document.getElementById('create-room-overlay');
    const cancelCreateRoomBtn = document.getElementById('cancelCreateRoom');
    const createRoomForm = document.getElementById('createRoomForm');
    const roomLinks = document.querySelectorAll('.room-link');
    const allRoomsContainer = document.getElementById('room-list');

    // User Input Consts
    const userInputTextArea = document.getElementById('user-input-textarea');
    const userInputSubmitButton = document.getElementById('user-input-button');

    // Sidebar Consts
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('active');
    });


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
    userInputTextArea.addEventListener('input', adjustHeight);
    window.addEventListener('resize', adjustHeight);

    // User Input Listeners
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


    /* Room Functions */
    newRoomBtn.addEventListener('click', function() {
        createRoomOverlay.style.display = 'flex';
    });

    cancelCreateRoomBtn.addEventListener('click', function() {
        createRoomOverlay.style.display = 'none';
    });

    createRoomForm.addEventListener('submit', async function(e) {
        try {
            e.preventDefault();
            const roomName = document.getElementById('roomName').value;
            const formData = new FormData(createRoomForm);

            let formObj = {};
            for (let [k, v] of formData.entries()) {
                if (v.trim()) {
                    formObj[k] = v;
                } else {
                    throw new Error('Fields Required');
                }
            }
            formObj["email"] = userEmail;

            if (userEmail) {
                const rsp = await fetch("http://127.0.0.1:80/create-room", {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formObj)
                });
                const data = await rsp.json();

                if (rsp.status == 401) {
                    window.location.href = '/login';
                } else if (rsp.status == 405) {
                    const roomStatus = document.querySelector('.roomStatus');
                    roomStatus.textContent = 'Room already exists';
                    roomStatus.style.display = 'block';
                } else if (rsp.status == 412) {
                    window.alert(data.detail);
                    // Add this to the card
                } else if (rsp.status == 200) {
                    roomStatus.style.display = 'none';
                    const roomList = document.getElementById('room-list');
                    const newRoom = document.createElement('li');
                    newRoom.textContent = roomName;
                    roomList.appendChild(newRoom);

                    createRoomOverlay.style.display = 'none';
                    createRoomForm.reset();
                }
            }
        } catch (e) {}
    });

    // Giving room link active status
    allRoomsContainer.addEventListener('click', function(e){
        const button = e.target.closest('.room-link');

        if (button) {
            console.log('button');
            const activeButtons = document.querySelectorAll('.room-link.active');
            if (activeButtons){
                activeButtons.forEach(btn => btn.classList.remove('active'));
            }
        }

        button.classList.add('active')
        console.log(button);
    });
});