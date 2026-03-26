/**
 * Transformations and helpers for the Smart Parking Frontend
 */

// Toast Notification
function showToast(message, type = 'info') {
    // Create toast container if needed
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    
    let bg = '#333';
    if (type === 'success') bg = 'var(--secondary-color)';
    if (type === 'error') bg = 'var(--danger-color)';

    toast.style.cssText = `
        background: ${bg};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-size: 0.9rem;
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 10px;
    `;
    
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        toast.style.transition = 'all 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Global Animation Styles injection for Toasts
const styleSheet = document.createElement("style");
styleSheet.innerText = `
@keyframes slideIn {
    from { opacity: 0; transform: translateY(20px) scale(0.9); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}`;
document.head.appendChild(styleSheet);

// Format Currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}
