document.addEventListener('DOMContentLoaded', function() {
    const events = document.querySelectorAll('.event');
    
    events.forEach(event => {
        event.addEventListener('mouseenter', showDetails);
        event.addEventListener('mouseleave', hideDetails);
        event.addEventListener('touchstart', toggleDetails);
    });

    function showDetails(e) {
        const details = this.querySelector('.event-details');
        details.style.display = 'block';
        
        // Adjust position if near the right edge
        const rect = details.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            details.style.left = 'auto';
            details.style.right = '0';
        }
    }

    function hideDetails(e) {
        this.querySelector('.event-details').style.display = 'none';
    }

    function toggleDetails(e) {
        e.preventDefault();
        const details = this.querySelector('.event-details');
        details.style.display = details.style.display === 'block' ? 'none' : 'block';
    }
});