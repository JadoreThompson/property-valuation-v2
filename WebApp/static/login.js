document.addEventListener('DOMContentLoaded', function(){
    const loginForm = document.getElementById('loginForm');
    const loginSubmit = document.getElementById('loginFormSubmit');

    loginSubmit.addEventListener('click', async function(e){
        e.preventDefault();
        const formStatus = document.getElementById('loginFormStatus');

        const formData = new FormData(loginForm);
        let formObj = {};
        for (let [k, v] of formData.entries()) {
            formObj[k] = v;
        }

        if (formData) {
            try {
                const rsp = await fetch("http://127.0.0.1:80/auth/login" ,{
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formObj)
                });

                const data = await rsp.json()
                console.log(data);
                if (rsp.status == 200) {
                    console.log('success');
                    const rsp2 = await fetch("/save-session-object", {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_id: data["user_id"]})
                    })
                    if (rsp2.status == 200) {
                        window.location.href = "/dashboard";
                    }

                } else {
                    console.log(data.detail);
                    throw new Error(data.detail);
                }
            } catch (e) {
                formStatus.textContent = e.message;
                formStatus.style.visibility = 'visible';
            } finally {
                //loginForm.reset();
            }
        }
    });
});
