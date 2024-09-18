document.addEventListener('DOMContentLoaded', function(){
    const pricingOptions = document.querySelectorAll('.pricing-button');
    pricingOptions.forEach(button => {
        button.addEventListener('click', async function(e){
            e.preventDefault();
            try {
                const rsp = await fetch("/get-plan", {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({"plan": button.getAttribute('data-custom')})
                })
                const data = await rsp.json();
                console.log("Get Plan JSON Response: ", data);

                if (rsp.status == 200) {
                    window.location.href = "/checkout";
                }
            } catch(e) {
                // Do Something
            }
        });
    });
});
