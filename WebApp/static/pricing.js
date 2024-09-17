document.addEventListener('DOMContentLoaded', function(){
    const pricingOptions = document.querySelectorAll('.pricing-button');
    pricingOptions.forEach(button => {
        button.addEventListener('click', async function(e){
            //e.preventDefault();
            const rsp = await fetch("/get-plan", {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({"plan": button.getAttribute('data-custom')})
            })
        });
    });
});
