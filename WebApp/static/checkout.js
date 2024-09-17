document.addEventListener('DOMContentLoaded', async function(){
    const checkoutForm = document.getElementById('checkoutForm');
    const checkoutSubmitBtn = document.getElementById('checkoutSubmitBtn');
    const checkoutStatus = document.getElementById('checkoutStatus');
    const signupPrompt = document.getElementById('signupPrompt');

    async function checkout(formObj) {
        try {

            const rsp = await fetch("http://127.0.0.1:80/checkout", {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formObj)
            });
            const data = await rsp.json();

            if (rsp.status == 200) {
                window.location.href('/dashboard');
            } else if (rsp.status == 404) {
                signupPrompt.style.visibility = 'visible';
            } else if (rsp.status == 500) {
                checkoutStatus.textContent = data.detail;
                checkoutStatus.style.visibility = 'visible';
            }
        } catch (e) {

        }
    };

    checkoutSubmitBtn.addEventListener('click', async function(e) {
        e.preventDefault();

        const formData = new FormData(checkoutForm);
        let formObj = {};
        try {

            for (let [k, v] of formData.entries()) {
                if (v.trim()) {
                    formObj[k] = v;
                } else {
                    throw new Error('Fields Missing');
                }
            }
            formObj["message"] = formObj["message"].trim();
            await checkout();

        } catch (e) {
            checkoutStatus.textContent = e.message;
            checkoutStatus.style.visibility = 'visible';
        }
    });
});