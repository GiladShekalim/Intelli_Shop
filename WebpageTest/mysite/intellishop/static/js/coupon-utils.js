/**
 * Coupon Utilities - Reusable JavaScript functions for coupon functionality
 * This file contains common functions used across all coupon display pages
 */

// Global coupon utility functions
window.CouponUtils = {
    
    /**
     * Render a coupon card dynamically
     * @param {Object} coupon - The coupon object
     * @param {Object} options - Rendering options
     * @returns {HTMLElement} - The rendered coupon card element
     */
    renderCouponCard: function(coupon, options = {}) {
        const config = {
            showFavoriteControls: options.showFavoriteControls !== false,
            showRemoveFavorite: options.showRemoveFavorite || false,
            cardClass: options.cardClass || '',
            ...options
        };

        const div = document.createElement('div');
        div.className = `discount-card ${config.cardClass}`.trim();
        div.setAttribute('data-discount-id', coupon.discount_id);

        // Determine label and color
        let priceLabel = '';
        let priceColor = '';
        let type = coupon.discount_type || coupon.price_type || '';
        
        if (['fixed_amount', 'fixed_price', 'amount', 'fixed'].includes(type)) {
            priceLabel = 'מחיר סופי';
            priceColor = '#007bff'; // blue
        } else if (type === 'percentage' || type === '%') {
            priceLabel = '% הנחה';
            priceColor = '#28a745'; // green
        } else {
            priceLabel = '';
            priceColor = '#6c757d'; // gray
        }

        // Show more logic for description and terms
        function getShowMoreHtml(text, idPrefix) {
            const maxLength = 250;
            if (!text) return '';
            if (text.length <= maxLength) {
                return `<span>${text}</span>`;
            }
            const shortText = text.slice(0, maxLength) + '...';
            return `
                <span id="${idPrefix}-short">${shortText}</span>
                <span id="${idPrefix}-full" style="display:none;">${text}</span>
                <a href="#" class="show-more-link" data-id="${idPrefix}">הצג עוד</a>
            `;
        }

        // Build favorite controls HTML
        let favoriteControlsHtml = '';
        if (config.showFavoriteControls) {
            favoriteControlsHtml = `
                <div class="like-icon-col">
                    <button class="fav-btn btn btn-outline-primary" data-discount-id="${coupon.discount_id}" style="display: flex; align-items: center; gap: 4px; font-weight: 500; color: #ff6b6b; direction: ltr; border: none; background: none; padding: 8px 12px; border-radius: 6px; cursor: pointer;">
                        <span class="fav-btn-text">Add</span>
                        <span class="like-icon" style="font-size: 1.5em; color: #ccc; margin: 0 4px;">&#10084;</span>
                        <span>Favorites</span>
                    </button>
                </div>
            `;
        }

        div.innerHTML = `
            <div class="discount-flex-row">
                <div class="discount-image-col">
                    <img src="${coupon.image_link}" alt="${coupon.title}" style="max-width:400px; max-height:400px; border-radius:8px;">
                </div>
                <div class="discount-details-col">
                    <h4 class="discount-title">${coupon.title}
                        <span class="discount-meta">
                            ${coupon.valid_until ? (() => {
                                let expired = false;
                                let dateStr = coupon.valid_until;
                                let now = new Date();
                                let dateObj = new Date(dateStr);
                                if (!isNaN(dateObj.getTime()) && dateStr.length >= 8) {
                                    expired = dateObj < new Date(now.getFullYear(), now.getMonth(), now.getDate());
                                }
                                return `<span class='meta-item'><i class='bi bi-calendar-event'></i> בתוקף עד: ${dateStr}
                                    ${expired ? `<div class='expired-label'>פג תוקף</div>` : ''}
                                </span>`;
                            })() : ''}
                            ${coupon.usage_limit ? `<span class='meta-item'><i class='bi bi-ticket-perforated'></i> כמות הנחות שנותרה: ${coupon.usage_limit}</span>` : ''}
                        </span>
                    </h4>
                    <div class="desc-block">
                        <strong>תיאור:</strong>
                        <div>${getShowMoreHtml(coupon.description, `desc-${coupon.discount_id}`)}</div>
                    </div>
                    <div class="terms-block" style="margin-top:10px;">
                        <strong>תנאים והגבלות:</strong>
                        <div>${getShowMoreHtml(coupon.terms_and_conditions, `terms-${coupon.discount_id}`)}</div>
                    </div>
                </div>
            </div>
            <div class="discount-bottom-row">
                <div class="price-type-col">
                    <span class="price-label-big" style="background:${priceColor};color:white;padding:3px 9px;border-radius:16px;font-size:1em;font-weight:bold;display:inline-block;vertical-align:middle;">
                        ${priceLabel}
                    </span>
                    <span class="price-value-big">${coupon.price}</span>
                </div>
                ${coupon.coupon_code ? `
                    <div class="copy-code-btn" data-code="${coupon.coupon_code}">
                        Copy Code Coupon
                    </div>
                ` : ''}
                ${(typeof coupon.provider_link === 'string' && coupon.provider_link.trim().toLowerCase().startsWith('https')) ? `
                    <a href="${coupon.provider_link}" target="_blank" class="site-link-btn provider-link-btn">
                        Go To Provider
                    </a>
                ` : ''}
                ${(coupon.discount_link && typeof coupon.discount_link === 'string' && coupon.discount_link.trim().toLowerCase().startsWith('https')) ? `
                    <a href="${coupon.discount_link}" target="_blank" class="site-link-btn">
                        Discount Link
                    </a>
                ` : ''}
                ${favoriteControlsHtml}
            </div>
            <hr>
        `;

        return div;
    },

    /**
     * Render multiple coupon cards
     * @param {Array} coupons - Array of coupon objects
     * @param {HTMLElement} container - Container element to append cards to
     * @param {Object} options - Rendering options
     */
    renderCouponCards: function(coupons, container, options = {}) {
        if (!coupons || coupons.length === 0) {
            container.innerHTML = `
                <div class="no-results">
                    <i class="bi bi-emoji-frown"></i>
                    <p>No discounts found at the moment.</p>
                </div>
            `;
            return;
        }

        // Clear container
        container.innerHTML = '';

        // Render each coupon
        coupons.forEach(coupon => {
            const card = this.renderCouponCard(coupon, options);
            container.appendChild(card);
        });

        // Add event delegation for show more/less functionality
        this.addShowMoreEventDelegation(container);
        
        // Initialize favorites for the newly rendered cards
        if (typeof initFavoritesForNewCards === 'function') {
            initFavoritesForNewCards();
        }
    },

    /**
     * Add event delegation for show more/less functionality
     * @param {HTMLElement} container - Container element
     */
    addShowMoreEventDelegation: function(container) {
        container.addEventListener('click', function(e) {
            if (e.target.classList.contains('show-more-link')) {
                e.preventDefault();
                const id = e.target.getAttribute('data-id');
                const shortSpan = document.getElementById(`${id}-short`);
                const fullSpan = document.getElementById(`${id}-full`);
                if (shortSpan.style.display === 'none') {
                    shortSpan.style.display = '';
                    fullSpan.style.display = 'none';
                    e.target.textContent = 'הצג עוד';
                } else {
                    shortSpan.style.display = 'none';
                    fullSpan.style.display = '';
                    e.target.textContent = 'הצג פחות';
                }
            }
        });
    },

    /**
     * Debug function to log DOM structure around favorite icon
     * @param {HTMLElement} iconElement - The heart icon element
     */
    _debugFavoriteStructure: function(iconElement) {
        console.log('=== Favorite DOM Structure Debug ===');
        console.log('Icon element:', iconElement);
        console.log('Icon classes:', iconElement.className);
        console.log('Icon parent:', iconElement.parentElement);
        
        if (iconElement.parentElement) {
            console.log('Parent classes:', iconElement.parentElement.className);
            console.log('Parent text content:', iconElement.parentElement.textContent);
            console.log('Parent innerHTML:', iconElement.parentElement.innerHTML);
            console.log('Parent children:', iconElement.parentElement.children);
        }
        
        console.log('=== End Debug ===');
    },

    /**
     * Safely update favorite text in the DOM
     * @param {HTMLElement} iconElement - The heart icon element
     * @param {boolean} isFavorite - Whether the item should be marked as favorite
     */
    _updateFavoriteText: function(iconElement, isFavorite) {
        try {
            // Try multiple approaches to find and update the text
            const parentElement = iconElement.parentElement;
            if (!parentElement) {
                console.warn('No parent element found for favorite icon');
                this._debugFavoriteStructure(iconElement);
                return false;
            }

            // Approach 1: Update the entire parent element's text content
            if (parentElement.textContent) {
                if (isFavorite) {
                    parentElement.textContent = parentElement.textContent.replace('Add', 'Remove');
                } else {
                    parentElement.textContent = parentElement.textContent.replace('Remove', 'Add');
                }
                return true;
            }

            // Approach 2: Look for specific text nodes
            const textNodes = Array.from(parentElement.childNodes).filter(node => node.nodeType === Node.TEXT_NODE);
            for (const textNode of textNodes) {
                if (isFavorite && textNode.textContent.includes('Add')) {
                    textNode.textContent = textNode.textContent.replace('Add', 'Remove');
                    return true;
                } else if (!isFavorite && textNode.textContent.includes('Remove')) {
                    textNode.textContent = textNode.textContent.replace('Remove', 'Add');
                    return true;
                }
            }

            // Approach 3: Look for span elements with text
            const textSpans = parentElement.querySelectorAll('span');
            for (const span of textSpans) {
                if (span !== iconElement && span.textContent) {
                    if (isFavorite && span.textContent.includes('Add')) {
                        span.textContent = span.textContent.replace('Add', 'Remove');
                        return true;
                    } else if (!isFavorite && span.textContent.includes('Remove')) {
                        span.textContent = span.textContent.replace('Remove', 'Add');
                        return true;
                    }
                }
            }

            // Approach 4: Fallback - replace the entire parent element content
            const discountId = iconElement.getAttribute('data-discount-id');
            if (discountId) {
                const newContent = isFavorite ? 
                    `Favorites <span class="like-icon favorite-active" title="Click To Remove" data-discount-id="${discountId}">&#10084;</span> Remove` :
                    `Favorites <span class="like-icon" title="Click To Add" data-discount-id="${discountId}">&#10084;</span> Add`;
                
                parentElement.innerHTML = newContent;
                return true;
            }

            console.warn('Could not find text to update in favorite element');
            this._debugFavoriteStructure(iconElement);
            return false;
        } catch (error) {
            console.warn('Error updating favorite text:', error);
            this._debugFavoriteStructure(iconElement);
            return false;
        }
    },

    /**
     * Toggle favorite status for a coupon
     * @param {string} discountId - The discount ID
     * @param {HTMLElement} iconElement - The heart icon element
     */
    toggleFavorite: function(discountId, iconElement) {
        const isFavorite = iconElement.classList.contains('favorite-active');
        const url = isFavorite ? '/remove_favorite/' : '/add_favorite/';
        
        console.log(`toggleFavorite: ${isFavorite ? 'Removing' : 'Adding'} favorite for ${discountId}`);
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({discount_id: discountId})
        })
        .then(response => {
            console.log(`toggleFavorite: Response status: ${response.status}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`toggleFavorite: Response data:`, data);
            if (data.status === 'success') {
                // Safely update the DOM
                try {
                    if (isFavorite) {
                        iconElement.classList.remove('favorite-active');
                        this._updateFavoriteText(iconElement, false);
                    } else {
                        iconElement.classList.add('favorite-active');
                        this._updateFavoriteText(iconElement, true);
                    }
                    this.showNotification(data.message || 'Favorite updated successfully', 'success');
                } catch (domError) {
                    console.warn('DOM update failed, but operation was successful:', domError);
                    // Even if DOM update fails, show success message since the backend operation succeeded
                    this.showNotification(data.message || 'Favorite updated successfully', 'success');
                }
            } else {
                console.error('toggleFavorite: Server returned error:', data.error);
                // Don't show error notification for favorites - handled by favorites-manager.js
                console.log('Suppressing favorite error notification');
            }
        })
        .catch(error => {
            console.error('toggleFavorite: Fetch error:', error);
            // Don't show error notification for favorites - handled by favorites-manager.js
            console.log('Suppressing favorite error notification');
        });
    },

    /**
     * Check favorite status for a coupon
     * @param {string} discountId - The discount ID
     * @param {HTMLElement} iconElement - The heart icon element
     */
    checkFavoriteStatus: function(discountId, iconElement) {
        fetch(`/check_favorite/${discountId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.is_favorite) {
                try {
                    iconElement.classList.add('favorite-active');
                    this._updateFavoriteText(iconElement, true);
                } catch (domError) {
                    console.warn('DOM update failed during status check:', domError);
                }
            }
        })
        .catch(error => {
            console.error('Error checking favorite status:', error);
        });
    },

    /**
     * Remove favorite (specific to favorites page)
     * @param {string} discountId - The discount ID
     * @param {HTMLElement} iconElement - The heart icon element
     */
    removeFavorite: function(discountId, iconElement) {
        console.log(`removeFavorite: Removing favorite for ${discountId}`);
        
        fetch('/remove_favorite/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({discount_id: discountId})
        })
        .then(response => {
            console.log(`removeFavorite: Response status: ${response.status}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`removeFavorite: Response data:`, data);
            if (data.status === 'success') {
                // Safely update the DOM
                try {
                    // Remove the entire card from the page
                    const card = iconElement.closest('.favorite-item');
                    if (card) {
                        card.remove();
                        console.log('Card removed from DOM');
                    } else {
                        console.warn('Could not find .favorite-item card to remove');
                    }
                    
                    // Update favorite count
                    const countElement = document.querySelector('.user-welcome p:nth-child(3)');
                    if (countElement) {
                        const countMatch = countElement.textContent.match(/\d+/);
                        if (countMatch) {
                            const currentCount = parseInt(countMatch[0]);
                            countElement.innerHTML = `<strong>Total Favorites:</strong> ${currentCount - 1}`;
                            
                            // Show empty state if no more favorites
                            if (currentCount - 1 === 0) {
                                location.reload(); // Reload to show empty state
                            }
                        }
                    }
                    
                    this.showNotification(data.message || 'Removed from favorites', 'success');
                } catch (domError) {
                    console.warn('DOM update failed, but operation was successful:', domError);
                    // Even if DOM update fails, show success message since the backend operation succeeded
                    this.showNotification(data.message || 'Removed from favorites', 'success');
                }
            } else {
                console.error('removeFavorite: Server returned error:', data.error);
                // Don't show error notification for favorites - handled by favorites-manager.js
                console.log('Suppressing favorite error notification');
            }
        })
        .catch(error => {
            console.error('removeFavorite: Fetch error:', error);
            // Don't show error notification for favorites - handled by favorites-manager.js
            console.log('Suppressing favorite error notification');
        });
    },

    /**
     * Copy coupon code to clipboard
     * @param {string} text - The coupon code to copy
     * @param {HTMLElement} buttonElement - The copy button element
     */
    copyToClipboard: function(text, buttonElement) {
        navigator.clipboard.writeText(text).then(() => {
            const originalText = buttonElement.textContent;
            buttonElement.textContent = '! Copied';
            buttonElement.classList.add('copied');
            setTimeout(() => {
                buttonElement.textContent = originalText;
                buttonElement.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            this.showNotification('Failed to copy coupon code', 'error');
        });
    },

    /**
     * Get CSRF token from cookies
     * @param {string} name - Cookie name
     * @returns {string|null} - Cookie value or null
     */
    getCookie: function(name) {
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
        
        if (!cookieValue) {
            console.warn(`getCookie: CSRF token '${name}' not found in cookies`);
        }
        
        return cookieValue;
    },

    /**
     * Show notification message
     * @param {string} message - The message to display
     * @param {string} type - The type of notification (success, error, info)
     */
    showNotification: function(message, type = 'info') {
        // For favorite-related operations, use the new success message system
        if (message.includes('favorites') || message.includes('Favorite')) {
            if (type === 'success' && typeof showSuccessMessage === 'function') {
                showSuccessMessage(message);
                return;
            }
            // Don't show error messages for favorites - they're handled by favorites-manager.js
            if (type === 'error') {
                console.log('Suppressing favorite error notification:', message);
                return;
            }
        }
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
        `;
        
        // Set background color based on type
        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#28a745';
                break;
            case 'error':
                notification.style.backgroundColor = '#dc3545';
                break;
            case 'info':
            default:
                notification.style.backgroundColor = '#17a2b8';
                break;
        }
        
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    },

    /**
     * Initialize coupon functionality for a page
     * @param {Object} options - Configuration options
     */
    initialize: function(options = {}) {
        const config = {
            enableFavorites: options.enableFavorites !== false,
            enableCopyCode: options.enableCopyCode !== false,
            enableRemoveFavorite: options.enableRemoveFavorite || false,
            ...options
        };

        // Add CSS animations for notifications if not already added
        if (!document.getElementById('coupon-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'coupon-notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }

        // Initialize favorite functionality
        if (config.enableFavorites) {
            document.body.addEventListener('click', (e) => {
                if (e.target.classList.contains('like-icon')) {
                    const discountId = e.target.getAttribute('data-discount-id');
                    if (config.enableRemoveFavorite && e.target.classList.contains('favorite-active')) {
                        this.removeFavorite(discountId, e.target);
                    } else {
                        this.toggleFavorite(discountId, e.target);
                    }
                }
            });

            // Check favorite status for all coupons on page load
            document.querySelectorAll('.like-icon').forEach(icon => {
                const discountId = icon.getAttribute('data-discount-id');
                this.checkFavoriteStatus(discountId, icon);
            });
        }

        // Initialize copy code functionality
        if (config.enableCopyCode) {
            document.body.addEventListener('click', (e) => {
                if (e.target.classList.contains('copy-code-btn')) {
                    const code = e.target.getAttribute('data-code');
                    this.copyToClipboard(code, e.target);
                }
            });
        }
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    CouponUtils.initialize();
}); 