document.addEventListener('DOMContentLoaded', function(){
    const contactForm = document.getElementById('contactForm');
    const formSubmitBtn = document.getElementById('formSubmitBtn');


    /* Submitting the Form */
    formSubmitBtn.addEventListener('click', async function(e){
        e.preventDefault();

        const formStatus = document.getElementById('formStatus');
        let formObj = {};
        const formData = new FormData(contactForm);
        for (let [k, v] of formData.entries()) {
            formObj[k] = v;
        }

        try {
            if (formObj['employees'] < 1) {
                throw new Error("Employees must be greater than 0")
            }

            const rsp = await fetch("http://127.0.0.1:8000/contact-sales", {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formObj)
            });

            const data = await rsp.json();
            if (data.detail) {
                formStatus.textContent = data.detail;
            }

            if (rsp.status == 200) {
                window.location.href("/");
            } else if ((rsp.status == 409) || (rsp.status == 500)) {
                contactForm.reset();
            } else {
                formStatus.textContent = 'Something went wrong';
            }

        } catch(e) {
            formStatus.textContent = e.message;
        } finally {
            contactForm.reset();
            formStatus.style.visibility = 'visible';

        }
    });
});