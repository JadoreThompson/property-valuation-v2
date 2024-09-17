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
                const rsp = await fetch("http://127.0.0.1:80/signup" ,{
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formObj)
                });

                const data = await rsp.json()

                if (rsp.status == 200) {
                    console.log("below");
                    console.log({email: formObj["email"]});
                    const rsp2 = await fetch("/get-email", {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email: formObj["email"]})
                    });

                    const data2 = await rsp2.json();
                    console.log(data2);
                    window.location.href = '/pricing';
                } else {
                    console.log(data.detail);
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
