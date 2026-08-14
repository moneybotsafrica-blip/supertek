// Main JavaScript file for Mustek East Africa site

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any carousels
    const carousels = document.querySelectorAll('.carousel');
    if (carousels.length) {
        carousels.forEach(carousel => {
            new bootstrap.Carousel(carousel, {
                interval: 5000
            });
        });
    }

    // Setup AJAX for adding items to cart
    setupCartActions();
    
    // Setup currency switcher
    setupCurrencySwitcher();

    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltips.length) {
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
});

function setupCartActions() {
    // Add to cart using AJAX
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    if (addToCartForms.length) {
        addToCartForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const productId = this.getAttribute('data-product-id');
                const formData = new FormData(this);
                
                fetch(`/add-to-cart/${productId}/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update cart count in the header
                        updateCartCount(data.item_count);
                        
                        // Show success message
                        showMessage('Product added to cart successfully!', 'success');
                    } else {
                        showMessage('Failed to add product to cart.', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('An error occurred. Please try again.', 'danger');
                });
            });
        });
    }

    // Update cart item quantity
    const updateCartForms = document.querySelectorAll('.update-cart-form');
    if (updateCartForms.length) {
        updateCartForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const itemId = this.getAttribute('data-item-id');
                const formData = new FormData(this);
                
                fetch(`/update-cart-item/${itemId}/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update cart count in the header
                        updateCartCount(data.item_count);
                        
                        // Reload the page to update cart
                        location.reload();
                    } else {
                        showMessage('Failed to update cart.', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('An error occurred. Please try again.', 'danger');
                });
            });
        });
    }

    // Remove from cart
    const removeButtons = document.querySelectorAll('.remove-from-cart-btn');
    if (removeButtons.length) {
        removeButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const itemId = this.getAttribute('data-item-id');
                
                fetch(`/remove-from-cart/${itemId}/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update cart count in the header
                        updateCartCount(data.item_count);
                        
                        // Remove the item row
                        const itemRow = document.querySelector(`.cart-item-${itemId}`);
                        if (itemRow) {
                            itemRow.remove();
                        }
                        
                        // If cart is empty, reload to show empty cart message
                        if (data.item_count === 0) {
                            location.reload();
                        }
                    } else {
                        showMessage('Failed to remove item from cart.', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('An error occurred. Please try again.', 'danger');
                });
            });
        });
    }
}

function updateCartCount(count) {
    const cartCountElements = document.querySelectorAll('.cart-count');
    if (cartCountElements.length) {
        cartCountElements.forEach(element => {
            element.textContent = count;
        });
    }
}

function showMessage(message, type) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertsContainer.appendChild(alert);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
        }, 300);
    }, 3000);
}

// Helper function to get CSRF token
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

// Currency conversion functionality
function setupCurrencySwitcher() {
    // Get the currency options and selected currency element
    const currencyOptions = document.querySelectorAll('.currency-option');
    const selectedCurrency = document.getElementById('selected-currency');
    const selectedCurrencyFlag = document.getElementById('selected-currency-flag');
    
    // Check if there's a saved currency in local storage
    const savedCurrency = localStorage.getItem('selectedCurrency') || 'KES';
    const savedRate = parseFloat(localStorage.getItem('currencyRate')) || 1;
    const savedFlagCode = localStorage.getItem('currencyFlagCode') || 'ke';
    
    // Update the selected currency on page load
    if (selectedCurrency) {
        selectedCurrency.textContent = savedCurrency;
        if (selectedCurrencyFlag) {
            selectedCurrencyFlag.className = `flag-icon flag-icon-${savedFlagCode.toLowerCase()}`;
        }
        convertAllPrices(savedRate, savedCurrency);
    }
    
    // Add click event to currency options
    if (currencyOptions.length) {
        currencyOptions.forEach(option => {
            option.addEventListener('click', function(e) {
                e.preventDefault();
                
                const currency = this.getAttribute('data-currency');
                const rate = parseFloat(this.getAttribute('data-rate'));
                const flagCode = this.getAttribute('data-flag-code');
                
                if (selectedCurrency) {
                    selectedCurrency.textContent = currency;
                }
                
                if (selectedCurrencyFlag && flagCode) {
                    selectedCurrencyFlag.className = `flag-icon flag-icon-${flagCode.toLowerCase()}`;
                }
                
                // Save to local storage
                localStorage.setItem('selectedCurrency', currency);
                localStorage.setItem('currencyRate', rate);
                localStorage.setItem('currencyFlagCode', flagCode);
                
                // Convert all prices on the page
                convertAllPrices(rate, currency);
            });
        });
    }
}

function convertAllPrices(rate, currency) {
    // Find all elements with price class
    const priceElements = document.querySelectorAll('.price, .product-price, .total-price');
    
    priceElements.forEach(element => {
        // Check if we've already processed this element
        if (!element.hasAttribute('data-original-price')) {
            // Store the original price
            const originalText = element.textContent.trim();
            const priceMatch = originalText.match(/KES\s*([\d,]+)(\.\d+)?/);
            
            if (priceMatch) {
                const originalPrice = parseFloat(priceMatch[1].replace(/,/g, '')) + (priceMatch[2] ? parseFloat(priceMatch[2]) : 0);
                element.setAttribute('data-original-price', originalPrice);
            }
        }
        
        // Get the original price
        const originalPrice = parseFloat(element.getAttribute('data-original-price'));
        
        if (!isNaN(originalPrice)) {
            // Convert the price
            const convertedPrice = originalPrice * rate;
            
            // Format the converted price
            let formattedPrice;
            if (currency === 'KES') {
                formattedPrice = Math.round(convertedPrice).toLocaleString();
            } else {
                formattedPrice = convertedPrice.toFixed(2).toLocaleString();
            }
            
            // Update the element text
            const originalText = element.textContent;
            element.textContent = originalText.replace(/[A-Z]{3}\s*[\d,]+(\.\d+)?/, `${currency} ${formattedPrice}`);
        }
    });
} 