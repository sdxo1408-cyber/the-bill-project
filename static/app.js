// State Manager
let state = {
    inventory: [],
    cart: {},
    notionConfigured: false,
    checkingCustomer: false
};

// UI Elements
const menuContainer = document.getElementById("menu-container");
const menuSearch = document.getElementById("menu-search");
const cartItemsBody = document.getElementById("cart-items-body");
const clearCartBtn = document.getElementById("clear-cart-btn");
const customerPhone = document.getElementById("customer-phone");
const customerName = document.getElementById("customer-name");
const customerAddress = document.getElementById("customer-address");
const summaryItemsCount = document.getElementById("summary-items-count");
const summaryTotalAmount = document.getElementById("summary-total-amount");
const checkoutBtn = document.getElementById("checkout-btn");
const searchSpinner = document.getElementById("search-spinner");
const searchStatusText = document.getElementById("search-status-text");
const notionBadge = document.getElementById("notion-badge");
const modalBackdrop = document.getElementById("notion-warning-modal");

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
    fetchConfigStatus();
    fetchInventory();
    setupEventListeners();
});

// Event Listeners Setup
function setupEventListeners() {
    clearCartBtn.addEventListener("click", resetCart);
    checkoutBtn.addEventListener("click", handleCheckout);
    
    // Dynamic Form Validation & Auto-search
    customerPhone.addEventListener("input", handlePhoneInput);
    customerName.addEventListener("input", validateCheckoutState);
    customerAddress.addEventListener("input", validateCheckoutState);
    
    // Menu Search Input
    menuSearch.addEventListener("input", () => {
        renderMenu(menuSearch.value);
    });
}

// Config & Status Checking
async function fetchConfigStatus() {
    try {
        const res = await fetch("/api/config-status");
        const status = await res.json();
        
        state.notionConfigured = status.notion_connected;
        updateNotionStatusUI();

        if (!state.notionConfigured) {
            // Show modal notification for local-only printing warning
            setTimeout(() => {
                modalBackdrop.classList.add("show");
            }, 800);
        }
    } catch (e) {
        showToast("Error", "Could not check server configuration status.", "error");
    }
}

function updateNotionStatusUI() {
    const indicator = notionBadge.querySelector(".status-indicator");
    const label = notionBadge.querySelector(".status-label");
    
    if (state.notionConfigured) {
        indicator.className = "status-indicator green";
        label.textContent = "Notion Connected";
    } else {
        indicator.className = "status-indicator yellow";
        label.textContent = "Local Print Mode";
    }
}

function closeModal() {
    modalBackdrop.classList.remove("show");
}

// Inventory Fetch & Render
async function fetchInventory() {
    try {
        const res = await fetch("/api/inventory");
        state.inventory = await res.json();
        renderMenu();
    } catch (e) {
        showToast("Error", "Could not fetch inventory items.", "error");
    }
}

function renderMenu(filterQuery = "") {
    menuContainer.innerHTML = "";
    const query = filterQuery.trim().toLowerCase();
    
    const filtered = state.inventory.filter(item => 
        item.name.toLowerCase().includes(query)
    );
    
    if (filtered.length === 0) {
        menuContainer.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 48px 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;">
                <i class="fa-solid fa-magnifying-glass-minus" style="font-size: 28px; opacity: 0.4;"></i>
                <p style="font-size: 14px; font-weight: 500;">No items match "${filterQuery}"</p>
            </div>
        `;
        return;
    }
    
    filtered.forEach(item => {
        const div = document.createElement("div");
        div.className = "menu-item";
        div.addEventListener("click", () => addToCart(item));
        
        div.innerHTML = `
            <div class="menu-item-name">${item.name}</div>
            <div class="menu-item-bottom">
                <span class="menu-item-price">Rs. ${item.price}</span>
                <span class="menu-item-unit">per ${item.unit}</span>
            </div>
        `;
        menuContainer.appendChild(div);
    });
}

// Cart Management Operations
function addToCart(item) {
    if (state.cart[item.id]) {
        state.cart[item.id].qty += (item.unit === "pc") ? 1 : 0.25; // Whole pc increments by 1, kg by 0.25
    } else {
        state.cart[item.id] = {
            id: item.id,
            name: item.name,
            unit: item.unit,
            price: item.price,
            qty: (item.unit === "pc") ? 1 : 1
        };
    }
    renderCart();
    showToast("Added to Cart", `${item.name} added to your selection.`, "success");
}

function updateQty(itemId, amount) {
    if (!state.cart[itemId]) return;
    
    const item = state.cart[itemId];
    const step = (item.unit === "pc") ? 1 : 0.25;
    
    item.qty += amount * step;
    
    if (item.qty <= 0) {
        delete state.cart[itemId];
        showToast("Removed", `${item.name} removed from cart.`, "warning");
    }
    
    renderCart();
}

function removeCartItem(itemId) {
    if (state.cart[itemId]) {
        const name = state.cart[itemId].name;
        delete state.cart[itemId];
        renderCart();
        showToast("Removed", `${name} removed from cart.`, "warning");
    }
}

function resetCart() {
    state.cart = {};
    renderCart();
    showToast("Cart Reset", "All items removed from receipt.", "warning");
}

function renderCart() {
    const keys = Object.keys(state.cart);
    cartItemsBody.innerHTML = "";
    
    if (keys.length === 0) {
        cartItemsBody.innerHTML = `
            <tr class="empty-cart-row">
                <td colspan="5" class="empty-cart-message">
                    <i class="fa-solid fa-basket-shopping"></i>
                    <p>Cart is empty. Click menu items to add.</p>
                </td>
            </tr>
        `;
        summaryItemsCount.textContent = "0 items";
        summaryTotalAmount.textContent = "Rs. 0";
        validateCheckoutState();
        return;
    }
    
    let totalItems = 0;
    let totalValue = 0;
    
    keys.forEach(key => {
        const item = state.cart[key];
        const itemTotal = item.price * item.qty;
        totalItems += item.qty;
        totalValue += itemTotal;
        
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${item.name}</strong></td>
            <td>Rs. ${item.price}</td>
            <td>
                <div class="qty-controls">
                    <button class="qty-btn" onclick="updateQty('${item.id}', -1)"><i class="fa-solid fa-minus"></i></button>
                    <input type="text" class="qty-input" value="${item.qty}" readonly>
                    <button class="qty-btn" onclick="updateQty('${item.id}', 1)"><i class="fa-solid fa-plus"></i></button>
                    <span style="font-size: 13px; color: var(--text-secondary); margin-left: 2px;">${item.unit}</span>
                </div>
            </td>
            <td><strong>Rs. ${itemTotal.toFixed(0)}</strong></td>
            <td style="text-align: right;">
                <button class="delete-btn" onclick="removeCartItem('${item.id}')"><i class="fa-solid fa-xmark"></i></button>
            </td>
        `;
        cartItemsBody.appendChild(tr);
    });
    
    summaryItemsCount.textContent = `${totalItems.toFixed(2).replace(/\.00$/, '')} units`;
    summaryTotalAmount.textContent = `Rs. ${totalValue.toFixed(0)}`;
    validateCheckoutState();
}

// Phone auto-search query
let searchTimeout;
function handlePhoneInput() {
    const rawVal = customerPhone.value.trim();
    
    // Validate checkout states on change
    validateCheckoutState();
    
    if (rawVal.length >= 10) {
        // Clear previous timeouts to debounce search input
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => searchNotionCustomer(rawVal), 400);
    } else {
        searchSpinner.style.display = "none";
        searchStatusText.textContent = "Existing profile will auto-load on phone input.";
        searchStatusText.className = "form-help";
    }
}

async function searchNotionCustomer(phone) {
    if (!state.notionConfigured) return;
    
    state.checkingCustomer = true;
    searchSpinner.style.display = "inline-block";
    searchStatusText.textContent = "Searching Notion database...";
    searchStatusText.className = "form-help yellow";
    
    try {
        const res = await fetch(`/api/customer-search?phone=${encodeURIComponent(phone)}`);
        const result = await res.json();
        
        if (result.found) {
            customerName.value = result.name;
            customerAddress.value = result.address;
            
            searchStatusText.innerHTML = `<span style="color: var(--success)"><i class="fa-solid fa-user-check"></i> Customer profile found! Auto-loaded.</span>`;
            showToast("Customer Found", `Profile for ${result.name} loaded from Notion.`, "success");
        } else {
            searchStatusText.innerHTML = `<span><i class="fa-solid fa-user-plus"></i> No profile found. A new one will be created.</span>`;
        }
    } catch (e) {
        searchStatusText.textContent = "Could not reach database search endpoint.";
    } finally {
        searchSpinner.style.display = "none";
        state.checkingCustomer = false;
        validateCheckoutState();
    }
}

// UI State Validation
function validateCheckoutState() {
    const cartKeys = Object.keys(state.cart);
    const phone = customerPhone.value.trim();
    const name = customerName.value.trim();
    
    const cartValid = cartKeys.length > 0;
    const customerValid = phone.length >= 10 && name.length > 0;
    
    checkoutBtn.disabled = !(cartValid && customerValid && !state.checkingCustomer);
}

// Checkout Submit Handler
async function handleCheckout() {
    const phone = customerPhone.value.trim();
    const name = customerName.value.trim();
    const address = customerAddress.value.trim();
    const cartItems = Object.values(state.cart);
    
    if (!name || !phone || cartItems.length === 0) {
        showToast("Validation Error", "Please fill in Name, Phone and add items.", "error");
        return;
    }
    
    // Disable action states
    checkoutBtn.disabled = true;
    checkoutBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Processing...`;
    
    showToast("Processing Order", "Sending sync data to Notion and printing...", "warning");
    
    try {
        const response = await fetch("/api/print-and-save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                customer_name: name,
                customer_phone: phone,
                customer_address: address,
                items: cartItems
            })
        });
        
        const resData = await response.json();
        
        if (response.status === 200) {
            // Success alerts
            let notifyMsg = `Bill ${resData.bill_no} printed successfully.`;
            let notifyType = "success";
            
            if (state.notionConfigured && resData.notion_saved) {
                notifyMsg += " Saved in Notion database!";
            } else if (state.notionConfigured && !resData.notion_saved) {
                notifyMsg += " Notion sync failed.";
                notifyType = "warning";
                showToast("Notion Warning", resData.notion_error || "Failed to log entry.", "warning");
            }
            
            showToast("Order Placed", notifyMsg, notifyType);
            
            // Success reset
            resetCart();
            customerPhone.value = "";
            customerName.value = "";
            customerAddress.value = "";
            menuSearch.value = "";
            renderMenu();
            searchStatusText.textContent = "Existing profile will auto-load on phone input.";
            
        } else {
            showToast("Server Error", resData.error || "Order placement failed.", "error");
        }
    } catch (e) {
        showToast("Connection Error", "Network interface request failed.", "error");
    } finally {
        checkoutBtn.disabled = false;
        checkoutBtn.innerHTML = `<i class="fa-solid fa-print"></i> Save & Print Bill`;
        validateCheckoutState();
    }
}

// Custom Premium Toast Notification System
function showToast(title, message, type = "success") {
    const container = document.getElementById("notification-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    
    let iconClass = "fa-circle-check";
    if (type === "warning") iconClass = "fa-triangle-exclamation";
    if (type === "error") iconClass = "fa-circle-xmark";
    
    toast.innerHTML = `
        <div class="toast-icon"><i class="fa-solid ${iconClass}"></i></div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Trigger slide-in transition
    setTimeout(() => toast.classList.add("show"), 10);
    
    // Auto-remove after 4.5 seconds
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 350);
    }, 4500);
}
