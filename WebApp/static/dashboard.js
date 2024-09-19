document.addEventListener('DOMContentLoaded', async function() {
    const userEmailElement = document.querySelector(".user-email");
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


    /* User Input Area */
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
    userInputSubmitButton.addEventListener('click', async function(){
        addUserMessage(userInputTextArea.value.trim());
        userInputTextArea.value = '';
    });

    userInputTextArea.addEventListener('keypress', function(e){
        if (e.key === 'Enter' && !e.shiftKey && userInputTextArea.value.trim()) {
            userInputSubmitButton.click();
        }
    });


    /* API Requests */
    async function getResponse(prompt, type = 'user_message') {
        let message;
        url = "http://127.0.0.1:8000/chat/get-response";

        try {
            const rsp = await fetch(url, {
                method: 'POST',
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                message: prompt,
                room_id: document.querySelector('.room-link.active').getAttribute('data-id'),
                type: type
                })
            });

            if (rsp.status != 200) {
                throw new Error('Something went wrong');
            }

            const data = await rsp.json();
            message = data["response"];

        } catch(e) {
            message = e;
        } finally {
            await addBotMessage(message);
        }
    }


    /* Chat Cards */
    async function addUserMessage(question, get_response = true)  {
        const allMessageContainer = document.querySelector('.chat-messages');
        const newDiv = document.createElement('div');
        const editButton = document.createElement('button');

        newDiv.className = 'message user_message';
        newDiv.textContent = question;
        editButton.className = 'action-button edit-button';
        editButton.textContent = 'Edit';

        newDiv.appendChild(editButton);
        allMessageContainer.appendChild(newDiv);
        allMessageContainer.scrollTop = allMessageContainer.scrollHeight;

        if (get_response) {
            await getResponse(question);
        }
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
            formObj["admin_id"] = userEmailElement.dataset.custom;
            if (userEmail) {
                const rsp = await fetch("http://127.0.0.1:8000/create-room", {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formObj)
                });
                const data = await rsp.json();
                console.log(data);

                if (rsp.status == 401) {
                    window.location.href = '/pricing';
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
                    newRoom.classList.add('room-link');
                    newRoom.setAttribute('data-id', data["room_id"]);
                    console.log(newRoom);
                    roomList.appendChild(newRoom);

                    newRoom.addEventListener('click', function(){
                        loadChats(newRoom);
                    });
                    createRoomOverlay.style.display = 'none';
                    createRoomForm.reset();
                }
            }
        } catch (e) { console.log('Error: ', e.message); }
    });

    // Sidebar
    async function loadChats(room) {
        if (!room.classList.contains('active')) {
            const activeButtons = document.querySelectorAll('.room-link.active');
            console.log(activeButtons);
            if (activeButtons){
                activeButtons.forEach(btn => btn.classList.remove('active'));
            }

            room.classList.add('active');
            const allMessageContainer = document.querySelector('.chat-messages');
            allMessageContainer.innerHTML = '';

            try {
                const rsp = await fetch("http://127.0.0.1:8000/chat/load-chats", {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({room_id: Number(room.getAttribute('data-id'))})
                });
                if (rsp.status == 200) {
                    const data = await rsp.json()
                    let chats = data["chats"];
                    let allChats = [];

                    chats.forEach(chat => {
                        let chatObj = {type: chat[0], message: chat[1]};
                        if (chatObj["type"] == "user_message") {
                            addUserMessage(chatObj["message"], false);
                        }
                        if (chatObj["type"] == "bot_message") {
                            addBotMessage(chatObj["message"]);
                        }
                    });
                }
            } catch (e) {
                window.alert(e.message);
            }
        }
    }

    roomLinks.forEach(room => {
        room.addEventListener('click', function(){
            loadChats(room);
        });
    });
});