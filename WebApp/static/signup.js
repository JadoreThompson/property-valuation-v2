document.addEventListener('DOMContentLoaded', function(){
    const signupForm = document.getElementById('signupForm');
    const signupFormSubmit = document.getElementById('signupFormSubmit');

    signupFormSubmit.addEventListener('click', async function(e){
        e.preventDefault();
        const formStatus = document.getElementById('signupFormStatus');

        const formData = new FormData(signupForm);
        let formObj = {};
        try {
            for (let [k, v] of formData.entries()) {
                if (v.trim()) {
                    formObj[k] = v;
                } else {
                    throw new Error('Fields Missing');
                }
            }

            await signUp(formData, formStatus, formObj);
        } catch (e) {
            formStatus.textContent = e.message;
            formStatus.style.visibility = 'visible';
        }
    });

    async function signUp(formData, formStatus, formObj) {
        if (formData) {
            try {
                const rsp = await fetch("http://127.0.0.1:80/auth/signup" ,{
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formObj)
                });

                const data = await rsp.json()
                console.log(data);

                if (rsp.status == 200) {
                    const rsp2 = await fetch("/save-session-object", {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_id: data["user_id"]})
                    });
                    if (rsp.status == 200) {
                        window.location.href = '/pricing';
                    } else {
                        const data = await rsp2.json();
                        throw new Error(data["message"]);
                    }

                } else {
                    throw new Error(data.detail);
                }
            } catch (e) {
                formStatus.textContent = e.message;
                formStatus.style.visibility = 'visible';
            } finally {
                signupForm.reset();
            }
        }
    }
});
