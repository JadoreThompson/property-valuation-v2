document.addEventListener('DOMContentLoaded', function(){
    const contactForm = document.getElementById('contactForm');
    const formSubmitBtn = document.getElementById('formSubmitBtn');


    /* Submitting the Form */
    formSubmitBtn.addEventListener('click', async function(e){
        e.preventDefault();
        const formData = new FormData(contactForm);
        for (let [k, v] of formData.entries()) {
            console.log(`Key ${k} - Value ${v}`);
        }
    });
});