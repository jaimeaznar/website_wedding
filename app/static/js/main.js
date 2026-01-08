// app/static/js/main.js
// CONSOLIDATED: All date configuration and countdown logic now in this single file

document.addEventListener('DOMContentLoaded', function () {

    // ========================================
    // DATE CONFIGURATION (Single Source of Truth)
    // CHANGED: Consolidated from both main.js and home.html
    // ========================================
    const urlParams = new URLSearchParams(window.location.search);
    const testDate = urlParams.get('_test_date');
    
    const today = testDate ? new Date(testDate) : new Date();
    const rsvpDeadline = new Date('2026-05-06');
    const weddingDay = new Date('2026-06-06');
    const weddingDateTime = new Date('2026-06-06T18:00:00').getTime();

    // Reset time to compare dates only
    const todayDateOnly = new Date(today);
    todayDateOnly.setHours(0, 0, 0, 0);
    const rsvpDeadlineDateOnly = new Date(rsvpDeadline);
    rsvpDeadlineDateOnly.setHours(0, 0, 0, 0);
    const weddingDayDateOnly = new Date(weddingDay);
    weddingDayDateOnly.setHours(0, 0, 0, 0);

    // ========================================
    // RSVP BANNER HANDLING
    // ========================================
    const bannerMessages = {
        rsvp_success: {
            es: '¡Gracias! Tu confirmación ha sido enviada.',
            en: 'Thank you! Your RSVP has been submitted.'
        },
        rsvp_cancelled: {
            es: 'Tu confirmación ha sido cancelada.',
            en: 'Your RSVP has been cancelled.'
        },
        deadline_passed: {
            es: 'La fecha límite ha pasado. Por favor, contáctanos directamente.',
            en: 'The deadline has passed. Please contact us directly.'
        },
        already_submitted: {
            es: 'Ya has confirmado tu asistencia.',
            en: 'You have already submitted your RSVP.'
        }
    };

    function showBanner(type, message) {
        const banner = document.getElementById('rsvp-banner');
        if (!banner) return;
        
        // Set alert type (success, info, warning, danger)
        banner.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        banner.style.display = 'block';
        banner.style.zIndex = '1050';
        banner.style.minWidth = '300px';
        
        document.getElementById('banner-message').textContent = message;
        
        // Remove URL params (so refresh doesn't show again)
        const url = new URL(window.location);
        url.searchParams.delete('rsvp_success');
        url.searchParams.delete('rsvp_cancelled');
        url.searchParams.delete('deadline_passed');
        url.searchParams.delete('already_submitted');
        history.replaceState({}, '', url);
        
        // Auto-hide after 3 seconds
        setTimeout(function() {
            hideBanner();
        }, 3000);
    }

    window.hideBanner = function() {
        const banner = document.getElementById('rsvp-banner');
        if (banner) {
            banner.style.display = 'none';
        }
    };

    // Check URL params for banners
    const lang = localStorage.getItem('preferredLanguage') || 'es';
    
    if (urlParams.get('rsvp_success') === '1') {
        showBanner('success', bannerMessages.rsvp_success[lang]);
    } else if (urlParams.get('rsvp_cancelled') === '1') {
        showBanner('info', bannerMessages.rsvp_cancelled[lang]);
    } else if (urlParams.get('deadline_passed') === '1') {
        showBanner('warning', bannerMessages.deadline_passed[lang]);
    } else if (urlParams.get('already_submitted') === '1') {
        showBanner('info', bannerMessages.already_submitted[lang]);
    }

    // ========================================
    // HIDE CARDS BASED ON DATE
    // CHANGED: Simplified using the consolidated date variables
    // ========================================
    
    // Hide RSVP card after RSVP deadline
    if (todayDateOnly >= rsvpDeadlineDateOnly) {
        // Handle both link version (with guest) and modal version (without guest)
        const rsvpCardLink = document.querySelector('a.rsvp-card');
        const rsvpCardModal = document.querySelector('[data-target="rsvp"]');
        const rsvpModal = document.getElementById('rsvp-modal');
        
        if (rsvpCardLink) rsvpCardLink.style.display = 'none';
        if (rsvpCardModal) rsvpCardModal.style.display = 'none';
        if (rsvpModal) rsvpModal.remove();
    }

    // Hide Accommodation on wedding day
    if (todayDateOnly >= weddingDayDateOnly) {
        const accommodationCard = document.querySelector('[data-target="accommodation"]');
        const accommodationModal = document.getElementById('accommodation-modal');
        
        if (accommodationCard) accommodationCard.style.display = 'none';
        if (accommodationModal) accommodationModal.remove();
    }

    // Hide Dresscode on wedding day
    if (todayDateOnly >= weddingDayDateOnly) {
        const dresscodeCard = document.querySelector('[data-target="dresscode"]');
        const dresscodeModal = document.getElementById('dresscode-modal');
        
        if (dresscodeCard) dresscodeCard.style.display = 'none';
        if (dresscodeModal) dresscodeModal.remove();
    }

    // ========================================
    // COUNTDOWN TIMER
    // CHANGED: Moved entirely from home.html inline script
    // ========================================
    function updateCountdown() {
        const now = testDate ? new Date(testDate).getTime() : new Date().getTime();
        const distance = weddingDateTime - now;
        
        const todayStr = (testDate ? new Date(testDate) : new Date()).toISOString().split('T')[0];
        const weddingDayStr = '2026-06-06';
        
        const countdownTimer = document.querySelector('.countdown-timer');
        if (!countdownTimer) return; // Not on home page, skip
        
        // Check if it's the wedding day
        if (todayStr === weddingDayStr) {
            const lang = window.translator ? window.translator.currentLang : 'es';
            const message = lang === 'es' ? '¡Hoy es el día!' : 'Today is the day!';
            
            // Replace entire card content to match other cards' structure
            const countdownCard = document.querySelector('.countdown-card');
            if (countdownCard) {
                const cardContent = countdownCard.querySelector('.feature-card-content');
                if (cardContent) {
                    cardContent.innerHTML = `
                        <span class="feature-card-icon" style="font-size: 3rem;">🎉</span>
                        <h3 class="feature-card-title celebration-text">${message}</h3>
                    `;
                }
            }
            return;
        }

        // Wedding has passed
        if (distance < 0) {
            const daysEl = document.getElementById('days');
            const hoursEl = document.getElementById('hours');
            const minutesEl = document.getElementById('minutes');
            const secondsEl = document.getElementById('seconds');
            
            if (daysEl) daysEl.textContent = '0';
            if (hoursEl) hoursEl.textContent = '0';
            if (minutesEl) minutesEl.textContent = '0';
            if (secondsEl) secondsEl.textContent = '0';
            return;
        }

        // Calculate time units
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        // Update the DOM
        const daysEl = document.getElementById('days');
        const hoursEl = document.getElementById('hours');
        const minutesEl = document.getElementById('minutes');
        const secondsEl = document.getElementById('seconds');
        
        if (daysEl) daysEl.textContent = days;
        if (hoursEl) hoursEl.textContent = hours.toString().padStart(2, '0');
        if (minutesEl) minutesEl.textContent = minutes.toString().padStart(2, '0');
        if (secondsEl) secondsEl.textContent = seconds.toString().padStart(2, '0');
    }

    // Start countdown if countdown timer exists (home page)
    if (document.querySelector('.countdown-timer')) {
        updateCountdown();
        setInterval(updateCountdown, 1000);
    }

    // ========================================
    // BUS MODAL - Wedding Day 18:30-19:30 Only
    // ========================================
    function checkBusModal() {
        const now = testDate ? new Date(testDate) : new Date();
        
        // Get current time in Spain
        const spainTime = new Date(now.toLocaleString('en-US', { timeZone: 'Europe/Madrid' }));
        
        const year = spainTime.getFullYear();
        const month = spainTime.getMonth(); // 0-indexed (5 = June)
        const day = spainTime.getDate();
        const hours = spainTime.getHours();
        const minutes = spainTime.getMinutes();
        
        // Check if it's June 6, 2026
        const isWeddingDay = (year === 2026 && month === 6 && day === 6);
        
        // Check if time is between 18:30 and 19:30
        const currentMinutes = hours * 60 + minutes;
        const startTime = 18 * 60 + 45; // 18:30
        const endTime = 19 * 60 + 30;   // 19:30
        const isCorrectTime = (currentMinutes >= startTime && currentMinutes <= endTime);
        
        // Show modal if both conditions met and not already dismissed
        if (isWeddingDay && isCorrectTime && !sessionStorage.getItem('busDismissed')) {
            const busModal = document.getElementById('bus-modal');
            if (busModal) {
                busModal.style.display = 'flex';
                busModal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        }
    }

    // Check bus modal on load
    checkBusModal();
    
    // Re-check every minute
    setInterval(checkBusModal, 60000);

    // Mark as dismissed when closed
    const busModal = document.getElementById('bus-modal');
    if (busModal) {
        busModal.querySelector('.modal-close').addEventListener('click', function() {
            sessionStorage.setItem('busDismissed', 'true');
        });
    }

    // ========================================
    // LANGUAGE CHANGE LISTENER
    // ========================================
    document.addEventListener('languageChanged', function (e) {
        console.log('Language changed to:', e.detail.language);
        
        // CHANGED: Update countdown message if on wedding day
        const countdownTimer = document.querySelector('.countdown-timer');
        if (countdownTimer) {
            const todayStr = (testDate ? new Date(testDate) : new Date()).toISOString().split('T')[0];
            if (todayStr === '2026-06-06') {
                updateCountdown(); // Re-render with new language
            }
        }
    });

    // ========================================
    // MODAL FUNCTIONALITY
    // ========================================
    const modals = document.querySelectorAll('.fullscreen-modal');
    const closeButtons = document.querySelectorAll('.modal-close');

    // Handle clickable cards
    document.querySelectorAll('.clickable-card').forEach(card => {
        card.addEventListener('click', function () {
            const href = this.getAttribute('data-href');
            if (href) {
                window.location.href = href;
            } else {
                const targetId = this.getAttribute('data-target') + '-modal';
                const modal = document.getElementById(targetId);

                if (modal) {
                    modal.style.display = 'flex';
                    modal.classList.add('active');
                    document.body.style.overflow = 'hidden';
                }
            }
        });
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

    // Close modal function
    function closeModal() {
        const modal = this.closest('.fullscreen-modal');
        modal.classList.remove('active');
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    // ========================================
    // GALLERY FUNCTIONALITY
    // ========================================
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
                document.body.style.overflow = 'hidden';
            });
        });

        // Close gallery modal
        const closeGalleryBtn = galleryModal.querySelector('.close-modal');
        if (closeGalleryBtn) {
            closeGalleryBtn.addEventListener('click', function () {
                galleryModal.style.display = 'none';
                document.body.style.overflow = '';
            });
        }

        // Close modal on outside click
        galleryModal.addEventListener('click', function (e) {
            if (e.target === this) {
                galleryModal.style.display = 'none';
                document.body.style.overflow = '';
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

    // ========================================
    // LANGUAGE SWITCHER VISIBILITY ON SCROLL
    // ========================================
    const languageSwitcher = document.querySelector('.language-switcher');
    if (languageSwitcher) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                languageSwitcher.style.opacity = '0';
                languageSwitcher.style.pointerEvents = 'none';
            } else {
                languageSwitcher.style.opacity = '1';
                languageSwitcher.style.pointerEvents = 'auto';
            }
        });
    }

});