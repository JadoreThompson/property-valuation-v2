document.addEventListener('DOMContentLoaded', async function(){
    const checkoutForm = document.getElementById('checkoutForm');
    const checkoutSubmitBtn = document.getElementById('checkoutSubmitBtn');
    const checkoutStatus = document.getElementById('checkoutStatus');

    async function checkout(formObj) {
        const rsp = await fetch("http://127.0.0.1:80/", {
        });
    };

    checkoutSubmitBtn.addEventListener('click', function(e) {
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

            console.log(formObj);

            //await checkout();

        } catch (e) {
            checkoutStatus.textContent = e.message;
            checkoutStatus.style.visibility = 'visible';
        }

        console.log(formObj);
    });
});