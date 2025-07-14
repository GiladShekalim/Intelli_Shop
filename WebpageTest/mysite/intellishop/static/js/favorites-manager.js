const FAVORITES_KEY = 'favoriteCoupons';

// Get favorites from localStorage
function getFavorites() {
    const favs = localStorage.getItem(FAVORITES_KEY);
    return favs ? JSON.parse(favs) : [];
}

// Save favorites to localStorage
function setFavorites(favs) {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favs));
}

// Check if a coupon is favorite
function isFavorite(couponId) {
    const favs = JSON.parse(localStorage.getItem('favoriteCoupons') || '[]');
    return favs.includes(couponId);
}

// Add a coupon to favorites
function addFavorite(couponId) {
    const favs = JSON.parse(localStorage.getItem('favoriteCoupons') || '[]');
    if (!favs.includes(couponId)) {
        favs.push(couponId);
        localStorage.setItem('favoriteCoupons', JSON.stringify(favs));
    }
}

// Remove a coupon from favorites
function removeFavorite(couponId) {
    let favs = JSON.parse(localStorage.getItem('favoriteCoupons') || '[]');
    favs = favs.filter(id => id !== couponId);
    localStorage.setItem('favoriteCoupons', JSON.stringify(favs));
}

// Update the UI for a single coupon card
function updateCouponCardUI(card, isFav) {
    const heart = card.querySelector('.like-icon');
    const btn = card.querySelector('.fav-btn');
    if (isFav) {
        heart.classList.add('favorite-active');
        heart.title = "Remove from Favorites";
        btn.textContent = "Remove";
        btn.classList.add('btn-danger');
        btn.classList.remove('btn-outline-primary');
    } else {
        heart.classList.remove('favorite-active');
        heart.title = "Add to Favorites";
        btn.textContent = "Add";
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-outline-primary');
    }
}

// Initialize all coupon cards on page load
function initFavoritesUI() {
    document.querySelectorAll('.discount-card[data-discount-id]').forEach(card => {
        const couponId = card.getAttribute('data-discount-id');
        const isFav = isFavorite(couponId);

        // Update UI
        updateCouponCardUI(card, isFav);

        // Heart icon click
        card.querySelector('.like-icon').onclick = function() {
            if (isFavorite(couponId)) {
                removeFavorite(couponId);
                updateCouponCardUI(card, false);
            } else {
                addFavorite(couponId);
                updateCouponCardUI(card, true);
            }
        };

        // Add/Remove button click
        card.querySelector('.fav-btn').onclick = function() {
            if (isFavorite(couponId)) {
                removeFavorite(couponId);
                updateCouponCardUI(card, false);
            } else {
                addFavorite(couponId);
                updateCouponCardUI(card, true);
            }
        };
    });
}

// Run on page load
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.fav-btn').forEach(btn => {
        const couponId = btn.getAttribute('data-discount-id');
        setFavBtnState(btn, isFavorite(couponId));

        btn.onclick = async function() {
            const currentlyFav = isFavorite(couponId);
            try {
                if (currentlyFav) {
                    await updateFavoriteOnServer(couponId, 'remove');
                    removeFavorite(couponId);
                } else {
                    await updateFavoriteOnServer(couponId, 'add');
                    addFavorite(couponId);
                }
                setFavBtnState(btn, !currentlyFav);
            } catch (e) {
                alert(e.message);
            }
        };
    });
});

function setFavBtnState(btn, isFav) {
    const text = btn.querySelector('.fav-btn-text');
    const heart = btn.querySelector('.like-icon');
    if (isFav) {
        btn.classList.add('favorited', 'btn-danger');
        btn.classList.remove('btn-outline-primary');
        text.textContent = 'Remove';
        heart.style.color = '#ff2d55';
    } else {
        btn.classList.remove('favorited', 'btn-danger');
        btn.classList.add('btn-outline-primary');
        text.textContent = 'Add';
        heart.style.color = '#bbb';
    }
}

async function updateFavoriteOnServer(couponId, action) {
    const url = action === 'add'
        ? '/add_favorite/'
        : '/remove_favorite/';
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(), // if using Django
        },
        body: JSON.stringify({ discount_id: couponId })
    });
    if (!response.ok) {
        const msg = await response.text();
        throw new Error(`Failed to update favorites: HTTP ${response.status}: ${msg}`);
    }
}

function getCSRFToken() {
    // Django: get from cookie
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return '';
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toggle favorite status for a coupon
function toggleFavorite(discountId, iconElement) {
    const isFavorite = iconElement.classList.contains('favorite-active');
    const url = isFavorite ? '/remove_favorite/' : '/add_favorite/';
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({discount_id: discountId})
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            if (isFavorite) {
                iconElement.classList.remove('favorite-active');
                iconElement.style.color = '#ccc';
                if (iconElement.nextElementSibling) iconElement.nextElementSibling.textContent = 'Add';
            } else {
                iconElement.classList.add('favorite-active');
                iconElement.style.color = '#ff0000';
                if (iconElement.nextElementSibling) iconElement.nextElementSibling.textContent = 'Remove';
            }
        } else {
            alert('Failed to update favorites: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to update favorites');
    });
}

// Check favorite status for all coupons on the page
function checkAllFavoriteStatus() {
    document.querySelectorAll('.like-icon[data-discount-id]').forEach(icon => {
        const discountId = icon.getAttribute('data-discount-id');
        checkFavoriteStatus(discountId, icon);
    });
}

// Check favorite status for a single coupon
function checkFavoriteStatus(discountId, iconElement) {
    fetch(`/check_favorite/${discountId}/`)
    .then(response => response.json())
    .then(data => {
        if (data.is_favorite) {
            iconElement.classList.add('favorite-active');
            iconElement.style.color = '#ff0000';
            if (iconElement.nextElementSibling) iconElement.nextElementSibling.textContent = 'Remove';
        } else {
            iconElement.classList.remove('favorite-active');
            iconElement.style.color = '#ccc';
            if (iconElement.nextElementSibling) iconElement.nextElementSibling.textContent = 'Add';
        }
    })
    .catch(error => {
        console.error('Error checking favorite status:', error);
    });
}

// Attach event listeners and initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Attach click event to all like icons
    document.querySelectorAll('.like-icon[data-discount-id]').forEach(icon => {
        icon.addEventListener('click', function() {
            const discountId = this.getAttribute('data-discount-id');
            const label = this.parentElement.querySelector('.like-fav-label');
            const isFavorite = this.classList.contains('favorite-active');
            const url = isFavorite ? '/remove_favorite/' : '/add_favorite/';
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({discount_id: discountId})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (isFavorite) {
                        this.classList.remove('favorite-active');
                        this.style.color = '#ccc';
                        if (label) label.textContent = 'Add';
                    } else {
                        this.classList.add('favorite-active');
                        this.style.color = '#ff0000';
                        if (label) label.textContent = 'Remove';
                    }
                } else {
                    alert('Failed to update favorites: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to update favorites');
            });
        });
    });

    // Check favorite status for all coupons
    document.querySelectorAll('.like-icon[data-discount-id]').forEach(icon => {
        const discountId = icon.getAttribute('data-discount-id');
        const label = icon.parentElement.querySelector('.like-fav-label');
        fetch(`/check_favorite/${discountId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.is_favorite) {
                icon.classList.add('favorite-active');
                icon.style.color = '#ff0000';
                if (label) label.textContent = 'Remove';
            } else {
                icon.classList.remove('favorite-active');
                icon.style.color = '#ccc';
                if (label) label.textContent = 'Add';
            }
        })
        .catch(error => {
            console.error('Error checking favorite status:', error);
        });
    });
});
