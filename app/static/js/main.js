// Save this as app/static/js/main.js
document.addEventListener('DOMContentLoaded', function () {
    // Modal functionality for home page cards
    const cardButtons = document.querySelectorAll('.show-modal');
    const modals = document.querySelectorAll('.fullscreen-modal');
    const closeButtons = document.querySelectorAll('.modal-close');

    // Open modal with dropdown effect
    cardButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();

            // Get the target modal ID
            const targetId = this.getAttribute('data-target');
            const modal = document.getElementById(targetId);

            if (modal) {
                // Get the content wrapper
                const contentWrapper = modal.querySelector('.modal-content-wrapper');

                // First set the initial state of the content wrapper
                contentWrapper.style.transform = 'translateY(-100%)';
                modal.style.display = 'flex';

                // Force reflow to ensure the initial state is applied
                void modal.offsetWidth;

                // Then animate the dropdown
                modal.classList.add('active');
                contentWrapper.style.transform = 'translateY(0)';
                document.body.style.overflow = 'hidden'; // Prevent scrolling
            }
        });
    });

    // Add click events to all feature cards for opening their modals
    document.querySelectorAll('.feature-card').forEach(card => {
        // Exclude cards that already have a direct link or button
        if (!card.querySelector('.show-modal') && !card.querySelector('a.stretched-link')) {
            card.addEventListener('click', function () {
                const targetId = this.getAttribute('data-target') + '-modal';
                const modal = document.getElementById(targetId);

                if (modal) {
                    const contentWrapper = modal.querySelector('.modal-content-wrapper');
                    contentWrapper.style.transform = 'translateY(-100%)';
                    modal.style.display = 'flex';
                    void modal.offsetWidth;
                    modal.classList.add('active');
                    contentWrapper.style.transform = 'translateY(0)';
                    document.body.style.overflow = 'hidden';
                }
            });
        }
    });

    // Close buttons
    closeButtons.forEach(button => {
        button.addEventListener('click', closeModal);
    });

    // Close when clicking outside content
    modals.forEach(modal => {
        modal.addEventListener('click', function (e) {
            if (e.target === this) {
                closeModal.call(this);
            }
        });
    });

    // Close with ESC key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.fullscreen-modal.active');
            if (activeModal) {
                closeModal.call(activeModal);
            }
        }
    });

    // Close modal function with slide-up animation
    function closeModal() {
        const modal = this.closest('.fullscreen-modal');
        const contentWrapper = modal.querySelector('.modal-content-wrapper');

        // Animate slide up
        contentWrapper.style.transform = 'translateY(-100%)';

        // After animation completes, hide modal
        setTimeout(() => {
            modal.classList.remove('active');
            document.body.style.overflow = ''; // Restore scrolling
            setTimeout(() => {
                modal.style.display = 'none';
                contentWrapper.style.transform = ''; // Reset for next opening
            }, 300);
        }, 300);
    }

    // Gallery functionality if gallery page is loaded
    const galleryItems = document.querySelectorAll('.gallery-item');
    const galleryModal = document.querySelector('.gallery-modal');

    if (galleryItems.length > 0 && galleryModal) {
        const modalImg = document.getElementById('modal-image');
        const captionText = document.getElementById('modal-caption-text');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');

        let currentIndex = 0;

        // Build image data array
        const images = [];
        galleryItems.forEach(item => {
            const img = item.querySelector('img');
            const caption = item.querySelector('.gallery-caption p');
            images.push({
                src: img.src,
                alt: img.alt,
                caption: caption ? caption.textContent : ''
            });
        });

        // Open modal when clicking on an image
        galleryItems.forEach((item, index) => {
            item.addEventListener('click', function () {
                currentIndex = index;
                showImage(currentIndex);
                galleryModal.style.display = 'flex';
                document.body.style.overflow = 'hidden'; // Prevent scrolling
            });
        });

        // Close gallery modal
        const closeGalleryBtn = galleryModal.querySelector('.close-modal');
        if (closeGalleryBtn) {
            closeGalleryBtn.addEventListener('click', function () {
                galleryModal.style.display = 'none';
                document.body.style.overflow = ''; // Restore scrolling
            });
        }

        // Close modal on outside click
        galleryModal.addEventListener('click', function (e) {
            if (e.target === this) {
                galleryModal.style.display = 'none';
                document.body.style.overflow = ''; // Restore scrolling
            }
        });

        // Previous button
        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                currentIndex = (currentIndex - 1 + images.length) % images.length;
                showImage(currentIndex);
            });
        }

        // Next button
        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                currentIndex = (currentIndex + 1) % images.length;
                showImage(currentIndex);
            });
        }

        // Show image at given index
        function showImage(index) {
            const image = images[index];
            modalImg.src = image.src;
            modalImg.alt = image.alt;
            if (captionText) {
                captionText.textContent = image.caption;
            }
        }
    }
});