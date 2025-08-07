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
    const btnText = card.querySelector('.fav-btn-text');
    
    if (isFav) {
        heart.classList.add('favorite-active');
        heart.style.color = '#ff0000';
        heart.title = "Remove from Favorites";
        btnText.textContent = "Remove";
        btn.classList.add('btn-danger');
        btn.classList.remove('btn-outline-primary');
    } else {
        heart.classList.remove('favorite-active');
        heart.style.color = '#ccc';
        heart.title = "Add to Favorites";
        btnText.textContent = "Add";
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-outline-primary');
    }
}

// Set favorite button state
function setFavBtnState(btn, isFav) {
    const text = btn.querySelector('.fav-btn-text');
    const heart = btn.querySelector('.like-icon');
    if (isFav) {
        btn.classList.add('favorited', 'btn-danger');
        btn.classList.remove('btn-outline-primary');
        text.textContent = 'Remove';
        heart.style.color = '#ff0000';
        heart.classList.add('favorite-active');
    } else {
        btn.classList.remove('favorited', 'btn-danger');
        btn.classList.add('btn-outline-primary');
        text.textContent = 'Add';
        heart.style.color = '#ccc';
        heart.classList.remove('favorite-active');
    }
}

// Initialize all coupon cards on page load
function initFavoritesUI() {
    document.querySelectorAll('.discount-card[data-discount-id]').forEach(card => {
        const couponId = card.getAttribute('data-discount-id');
        const isFav = isFavorite(couponId);

        // Update UI
        updateCouponCardUI(card, isFav);

        // Add/Remove button click
        const favBtn = card.querySelector('.fav-btn');
        if (favBtn) {
            favBtn.onclick = async function() {
                const currentlyFav = isFavorite(couponId);
                try {
                    if (currentlyFav) {
                        await updateFavoriteOnServer(couponId, 'remove');
                        removeFavorite(couponId);
                        showSuccessMessage('Removed from favorites!');
                    } else {
                        await updateFavoriteOnServer(couponId, 'add');
                        addFavorite(couponId);
                        showSuccessMessage('Added to favorites!');
                    }
                    setFavBtnState(favBtn, !currentlyFav);
                } catch (e) {
                    console.error('Error updating favorites:', e);
                    // Don't show error alert, just log it
                }
            };
        }
    });
}

async function updateFavoriteOnServer(couponId, action) {
    const url = action === 'add'
        ? '/add_favorite/'
        : '/remove_favorite/';
    
    const requestBody = { discount_id: couponId };
    const csrfToken = getCSRFToken();
    
    console.log(`updateFavoriteOnServer: ${action} favorite for ${couponId}`);
    console.log('Request URL:', url);
    console.log('Request body:', requestBody);
    console.log('CSRF Token:', csrfToken);
    
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(requestBody)
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    
    if (!response.ok) {
        const msg = await response.text();
        console.error('Error response:', msg);
        
        // Handle authentication error gracefully
        if (response.status === 401) {
            console.log('User not authenticated, using localStorage only');
            // For non-authenticated users, just use localStorage
            if (action === 'add') {
                addFavorite(couponId);
            } else {
                removeFavorite(couponId);
            }
            return { status: 'success', message: 'Updated local favorites (not logged in)' };
        }
        
        throw new Error(`Failed to update favorites: HTTP ${response.status}: ${msg}`);
    }
    
    const responseData = await response.json();
    console.log('Success response:', responseData);
    return responseData;
}

function getCSRFToken() {
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

// Show success message
function showSuccessMessage(message) {
    // Remove any existing success message
    const existingMessage = document.querySelector('.success-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create success message element
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: bold;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
    `;
    successDiv.textContent = message;
    
    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    // Add to page
    document.body.appendChild(successDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.style.animation = 'slideOut 0.3s ease-in';
            successDiv.style.transform = 'translateX(100%)';
            successDiv.style.opacity = '0';
            setTimeout(() => {
                if (successDiv.parentNode) {
                    successDiv.remove();
                }
            }, 300);
        }
    }, 3000);
}

// Initialize favorites for dynamically added cards
function initFavoritesForNewCards() {
    document.querySelectorAll('.discount-card[data-discount-id]').forEach(card => {
        const couponId = card.getAttribute('data-discount-id');
        const favBtn = card.querySelector('.fav-btn');
        
        if (favBtn && !favBtn.hasAttribute('data-initialized')) {
            const isFav = isFavorite(couponId);
            setFavBtnState(favBtn, isFav);
            
            favBtn.onclick = async function() {
                const currentlyFav = isFavorite(couponId);
                try {
                    if (currentlyFav) {
                        await updateFavoriteOnServer(couponId, 'remove');
                        removeFavorite(couponId);
                        showSuccessMessage('Removed from favorites!');
                    } else {
                        await updateFavoriteOnServer(couponId, 'add');
                        addFavorite(couponId);
                        showSuccessMessage('Added to favorites!');
                    }
                    setFavBtnState(favBtn, !currentlyFav);
                } catch (e) {
                    console.error('Error updating favorites:', e);
                    // Don't show error alert, just log it
                }
            };
            
            favBtn.setAttribute('data-initialized', 'true');
        }
    });
}

// Run on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize favorites UI for all coupon cards
    initFavoritesUI();
    
    // Also handle individual fav-btn elements for backward compatibility
    document.querySelectorAll('.fav-btn').forEach(btn => {
        const couponId = btn.getAttribute('data-discount-id');
        if (couponId) {
            setFavBtnState(btn, isFavorite(couponId));

            btn.onclick = async function() {
                const currentlyFav = isFavorite(couponId);
                try {
                    if (currentlyFav) {
                        await updateFavoriteOnServer(couponId, 'remove');
                        removeFavorite(couponId);
                        showSuccessMessage('Removed from favorites!');
                    } else {
                        await updateFavoriteOnServer(couponId, 'add');
                        addFavorite(couponId);
                        showSuccessMessage('Added to favorites!');
                    }
                    setFavBtnState(btn, !currentlyFav);
                } catch (e) {
                    console.error('Error updating favorites:', e);
                    // Don't show error alert, just log it
                }
            };
        }
    });
    
    // Set up a MutationObserver to handle dynamically added cards
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                initFavoritesForNewCards();
            }
        });
    });
    
    // Start observing the document body for dynamically added content
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});
