document.addEventListener('DOMContentLoaded', function(){
    /* Ensure element is centered when clicked */
//    function scrollToCenter(event) {
//        event.preventDefault();
//        const target = document.querySelector(event.target.getAttribute('href'));
//        const rect = target.getBoundingClientRect();
//        window.scrollBy({
//            top: rect.top + window.pageYOffset - (window.innerHeight / 2) + (rect.height / 2),
//            behavior: 'smooth'
//        });
//    }

    function scrollToCenter(event, id) {
        event.preventDefault(); // Prevent default anchor link behavior

        const element = document.getElementById(id);
        const elementRect = element.getBoundingClientRect();
        const elementTop = elementRect.top + window.pageYOffset;
        const elementHeight = elementRect.height;
        const windowHeight = window.innerHeight;

        // Calculate the scroll position to center the element
        const scrollPosition = elementTop - (windowHeight / 2) + (elementHeight / 2) - 1000;

        window.scrollTo({
            top: scrollPosition,
            behavior: 'smooth' // Smooth scrolling
        });
    }
});