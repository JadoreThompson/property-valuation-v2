document.addEventListener('DOMContentLoaded', function(){
        const contactSalesOpenBtn = document.getElementById('contact-sales-btn');
        const contactSalesCloseBtn = document.getElementById('contact-sales-close-btn');
        const contactSalesCard = document.getElementById('contactSalesCard');
        const contactSalesSubmitBtn = document.getElementById('contactSalesSubmitBtn');
        const contactSalesForm = document.getElementById('contactSalesForm');

        const tryForFreeBtn = document.getElementById('tryForFreeBtn');

        /*
           -------------------------
                Contact Sales Code
            ------------------------
        */

        // Event Listener for contact sales BTN
        // :param:
        // :return: Contact Sales Card
        contactSalesOpenBtn.addEventListener('click', function(e){
            const span = document.getElementById('errorMessage');
            span.style.display = 'none';
            contactSalesCard.style.display = 'flex';
            document.body.classList.add('modal-open');
        });

        // Event listener for contact sales close BTN
        // :param:
        // :return: Removes the contact sales card from the screen
        contactSalesCloseBtn.addEventListener('click', function(){
            contactSalesCard.style.display = 'none';
            document.body.classList.remove('modal-open');
        });

        // Handles the submission of the form to the API
        // :param: pydantic class(ContactSales)
        //              - Requires an email
        // :return:
        contactSalesForm.onsubmit = async (e) => {
            e.preventDefault();

            const span = document.getElementById('errorMessage');
            const formData = new FormData(contactSalesForm);

            // To prevent form submission issues, converting to an object / dictionary
            const formDataObject = {};
            for (let [key, val] of formData.entries()){
                if (val.trim() && key != 'csrf_token') {
                    formDataObject[key] = val.trim();
                }
            }

            try {
                let rsp = await fetch('http://127.0.0.1:80/contact-sales', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formDataObject)
                });

                const data = await rsp.json();

                if (data.status != 200) {
                    throw new Error(data.message);
                }

                span.textContent = data.message;
                span.style.display = 'flex';
            } catch (error) {
                span.textContent = error;
                span.style.display = 'flex';
            } finally {
                contactSalesForm.reset();
            }
        };

        tryForFreeBtn.addEventListener('click', function(){
            window.location.href = '/dashboard';
        });
    });