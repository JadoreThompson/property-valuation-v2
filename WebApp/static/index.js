document.addEventListener('DOMContentLoaded', function(){
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