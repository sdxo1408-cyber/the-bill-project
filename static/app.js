// State Manager
let state = {
    inventory: [],
    cart: {},
    notionConfigured: false,
    checkingCustomer: false,
    editingProductId: null,
    editingCustomerId: null,
    customers: []
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

// Product Management UI Elements
const manageProductsBtn = document.getElementById("manage-products-btn");
const productManagementModal = document.getElementById("product-management-modal");
const closeCatalogBtn = document.getElementById("close-catalog-btn");
const catalogSearch = document.getElementById("catalog-search");
const addProductBtn = document.getElementById("add-product-btn");
const catalogTableBody = document.getElementById("catalog-table-body");

const productFormModal = document.getElementById("product-form-modal");
const productFormTitle = document.getElementById("product-form-title");
const closeProductFormBtn = document.getElementById("close-product-form-btn");
const cancelProductFormBtn = document.getElementById("cancel-product-form-btn");
const productForm = document.getElementById("product-form");
const formGroupId = document.getElementById("form-group-id");
const prodId = document.getElementById("prod-id");
const prodName = document.getElementById("prod-name");
const prodUnit = document.getElementById("prod-unit");
const prodPrice = document.getElementById("prod-price");

// Customer Management UI Elements
const manageCustomersBtn = document.getElementById("manage-customers-btn");
const customerManagementModal = document.getElementById("customer-management-modal");
const closeCustomerCatalogBtn = document.getElementById("close-customer-catalog-btn");
const customerCatalogSearch = document.getElementById("customer-catalog-search");
const addCustomerBtn = document.getElementById("add-customer-btn");
const customerCatalogTableBody = document.getElementById("customer-catalog-table-body");

const customerFormModal = document.getElementById("customer-form-modal");
const customerFormTitle = document.getElementById("customer-form-title");
const closeCustomerFormBtn = document.getElementById("close-customer-form-btn");
const cancelCustomerFormBtn = document.getElementById("cancel-customer-form-btn");
const customerForm = document.getElementById("customer-form");
const custPhone = document.getElementById("cust-phone");
const custName = document.getElementById("cust-name");
const custAddress = document.getElementById("cust-address");

// Suggestions dropdown elements
const customerPhoneSuggestions = document.getElementById("customer-phone-suggestions");
const customerNameSuggestions = document.getElementById("customer-name-suggestions");

// Generic Confirmation Modal Elements
const confirmModal = document.getElementById("confirm-modal");
const confirmModalMessage = document.getElementById("confirm-modal-message");
const confirmModalOkBtn = document.getElementById("confirm-modal-ok-btn");
const confirmModalCancelBtn = document.getElementById("confirm-modal-cancel-btn");

// Replaces native window.confirm(), which is unreliable/blocked in some kiosk & embedded browser setups.
function confirmAction(message) {
    return new Promise((resolve) => {
        confirmModalMessage.textContent = message;
        confirmModal.classList.add("show");

        function onOk() { cleanup(true); }
        function onCancel() { cleanup(false); }
        function cleanup(result) {
            confirmModal.classList.remove("show");
            confirmModalOkBtn.removeEventListener("click", onOk);
            confirmModalCancelBtn.removeEventListener("click", onCancel);
            resolve(result);
        }

        confirmModalOkBtn.addEventListener("click", onOk);
        confirmModalCancelBtn.addEventListener("click", onCancel);
    });
}

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

    // Product Catalog Management Modals
    if (manageProductsBtn) manageProductsBtn.addEventListener("click", openCatalogModal);
    if (closeCatalogBtn) closeCatalogBtn.addEventListener("click", closeCatalogModal);
    if (catalogSearch) catalogSearch.addEventListener("input", renderCatalog);
    if (addProductBtn) addProductBtn.addEventListener("click", openAddProductForm);
    if (closeProductFormBtn) closeProductFormBtn.addEventListener("click", closeProductFormModal);
    if (cancelProductFormBtn) cancelProductFormBtn.addEventListener("click", closeProductFormModal);
    if (productForm) productForm.addEventListener("submit", handleProductFormSubmit);

    // Customer Catalog Management Modals
    if (manageCustomersBtn) manageCustomersBtn.addEventListener("click", openCustomerCatalogModal);
    if (closeCustomerCatalogBtn) closeCustomerCatalogBtn.addEventListener("click", closeCustomerCatalogModal);
    if (customerCatalogSearch) customerCatalogSearch.addEventListener("input", renderCustomerCatalog);
    if (addCustomerBtn) addCustomerBtn.addEventListener("click", openAddCustomerForm);
    if (closeCustomerFormBtn) closeCustomerFormBtn.addEventListener("click", closeCustomerFormModal);
    if (cancelCustomerFormBtn) cancelCustomerFormBtn.addEventListener("click", closeCustomerFormModal);
    if (customerForm) customerForm.addEventListener("submit", handleCustomerFormSubmit);

    // Dropdown suggestions autocomplete handlers
    if (customerPhone) customerPhone.addEventListener("input", handleCustomerAutocomplete);
    if (customerName) customerName.addEventListener("input", handleCustomerAutocomplete);
    
    // Click outside handler to close dropdowns
    document.addEventListener("click", (e) => {
        if (customerPhone && !customerPhone.contains(e.target) && customerPhoneSuggestions && !customerPhoneSuggestions.contains(e.target)) {
            customerPhoneSuggestions.style.display = "none";
        }
        if (customerName && !customerName.contains(e.target) && customerNameSuggestions && !customerNameSuggestions.contains(e.target)) {
            customerNameSuggestions.style.display = "none";
        }
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

// ── PRODUCT CATALOG CRUD MANAGEMENT ──

function openCatalogModal() {
    productManagementModal.classList.add("show");
    renderCatalog();
}

function closeCatalogModal() {
    productManagementModal.classList.remove("show");
}

function renderCatalog() {
    catalogTableBody.innerHTML = "";
    const query = (catalogSearch.value || "").trim().toLowerCase();
    
    const filtered = state.inventory.filter(item => 
        item.name.toLowerCase().includes(query) || item.id.toLowerCase().includes(query)
    );
    
    if (filtered.length === 0) {
        catalogTableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">
                    No products found.
                </td>
            </tr>
        `;
        return;
    }
    
    filtered.forEach(item => {
        const tr = document.createElement("tr");
        tr.style.borderBottom = "1px solid var(--border-color)";
        
        tr.innerHTML = `
            <td style="padding: 12px 16px; font-family: monospace; font-size: 13px; color: var(--text-secondary);">${item.id}</td>
            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: var(--text-primary);">${item.name}</td>
            <td style="padding: 12px 16px; font-size: 14px; color: var(--text-secondary);">${item.unit}</td>
            <td style="padding: 12px 16px; font-size: 14px; font-weight: 600; color: var(--text-primary);">Rs. ${item.price}</td>
            <td style="padding: 12px 16px; text-align: right; display: flex; justify-content: flex-end; gap: 8px;">
                <button class="qty-btn" onclick="openEditProductForm('${item.id}')" title="Edit" style="background: var(--primary-bg); color: var(--primary); border: 1px solid rgba(242,78,30,0.15); width: 30px; height: 30px; border-radius: 6px; cursor: pointer;"><i class="fa-solid fa-pen"></i></button>
                <button class="qty-btn" onclick="deleteProduct('${item.id}')" title="Delete" style="background: var(--danger-bg); color: var(--danger); border: 1px solid rgba(220,38,38,0.15); width: 30px; height: 30px; border-radius: 6px; cursor: pointer;"><i class="fa-solid fa-trash-can"></i></button>
            </td>
        `;
        catalogTableBody.appendChild(tr);
    });
}

function openAddProductForm() {
    state.editingProductId = null;
    productFormTitle.textContent = "Add Product";
    formGroupId.style.display = "block";
    prodId.value = "";
    prodId.required = true;
    prodName.value = "";
    prodUnit.value = "kg";
    prodPrice.value = "";
    productFormModal.classList.add("show");
}

function openEditProductForm(id) {
    const item = state.inventory.find(p => p.id === id);
    if (!item) return;
    
    state.editingProductId = id;
    productFormTitle.textContent = "Edit Product";
    formGroupId.style.display = "none";
    prodId.value = item.id;
    prodId.required = false;
    prodName.value = item.name;
    prodUnit.value = item.unit;
    prodPrice.value = item.price;
    productFormModal.classList.add("show");
}

function closeProductFormModal() {
    productFormModal.classList.remove("show");
}

async function handleProductFormSubmit(e) {
    e.preventDefault();
    
    const id = prodId.value.trim();
    const name = prodName.value.trim();
    const unit = prodUnit.value;
    const price = parseFloat(prodPrice.value);
    
    if (!name || !unit || isNaN(price)) {
        showToast("Validation Error", "All fields are required.", "error");
        return;
    }
    
    const isEdit = state.editingProductId !== null;
    const url = isEdit ? `/api/products/${encodeURIComponent(state.editingProductId)}` : "/api/products";
    const method = isEdit ? "PUT" : "POST";
    
    const body = isEdit ? { name, unit, price } : { id, name, unit, price };
    
    try {
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast("Catalog Updated", data.message || "Product saved successfully.", "success");
            closeProductFormModal();
            await fetchInventory();
            renderCatalog();
        } else {
            showToast("Error saving product", data.error || "Operation failed.", "error");
        }
    } catch (e) {
        showToast("Connection Error", "Failed to contact database service.", "error");
    }
}

async function deleteProduct(id) {
    const confirmed = await confirmAction(`Are you sure you want to delete product "${id}"?`);
    if (!confirmed) return;
    
    try {
        const res = await fetch(`/api/products/${encodeURIComponent(id)}`, {
            method: "DELETE"
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast("Product Deleted", "Product removed from database catalog.", "success");
            if (state.cart[id]) {
                delete state.cart[id];
                renderCart();
            }
            await fetchInventory();
            renderCatalog();
        } else {
            showToast("Error deleting product", data.error || "Operation failed.", "error");
        }
    } catch (e) {
        showToast("Connection Error", "Failed to contact database service.", "error");
    }
}

// ── CUSTOMER AUTOCOMPLETE & RECOMMENDATIONS ──

let autocompleteTimeout;
function handleCustomerAutocomplete(e) {
    const input = e.target;
    const value = input.value.trim();
    const isPhone = input.id === "customer-phone";
    const dropdown = isPhone ? customerPhoneSuggestions : customerNameSuggestions;
    const otherDropdown = isPhone ? customerNameSuggestions : customerPhoneSuggestions;
    
    if (otherDropdown) otherDropdown.style.display = "none";
    
    if (value.length < 2) {
        if (dropdown) dropdown.style.display = "none";
        return;
    }
    
    clearTimeout(autocompleteTimeout);
    autocompleteTimeout = setTimeout(async () => {
        try {
            const res = await fetch(`/api/customers/search?q=${encodeURIComponent(value)}`);
            const suggestions = await res.json();
            
            if (suggestions.length === 0) {
                if (dropdown) dropdown.style.display = "none";
                return;
            }
            
            renderSuggestions(suggestions, dropdown);
        } catch (err) {
            console.error("Autocomplete fetch error:", err);
        }
    }, 250);
}

function renderSuggestions(suggestions, dropdown) {
    if (!dropdown) return;
    dropdown.innerHTML = "";
    suggestions.forEach(customer => {
        const item = document.createElement("div");
        item.className = "suggestion-item";
        item.innerHTML = `
            <div class="suggestion-header">
                <span class="suggestion-item-name">${escapeHTML(customer.name)}</span>
                <span class="suggestion-item-phone">${escapeHTML(customer.phone)}</span>
            </div>
            <div class="suggestion-item-address">${escapeHTML(customer.address || "No address")}</div>
        `;
        item.addEventListener("click", () => {
            customerPhone.value = customer.phone;
            customerName.value = customer.name;
            customerAddress.value = customer.address || "";
            dropdown.style.display = "none";
            
            searchStatusText.innerHTML = `<span style="color: var(--success)"><i class="fa-solid fa-user-check"></i> Customer profile loaded!</span>`;
            showToast("Customer Selected", `Profile for ${customer.name} loaded.`, "success");
            validateCheckoutState();
        });
        dropdown.appendChild(item);
    });
    dropdown.style.display = "block";
}

function escapeHTML(str) {
    if (!str) return "";
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

// ── CUSTOMER CATALOG CRUD ──

async function fetchCustomers() {
    try {
        const res = await fetch("/api/customers");
        state.customers = await res.json();
    } catch (e) {
        showToast("Error", "Could not fetch customers list.", "error");
    }
}

async function openCustomerCatalogModal() {
    if (customerManagementModal) {
        customerManagementModal.classList.add("show");
        await fetchCustomers();
        renderCustomerCatalog();
    }
}

function closeCustomerCatalogModal() {
    if (customerManagementModal) {
        customerManagementModal.classList.remove("show");
    }
}

function renderCustomerCatalog() {
    if (!customerCatalogTableBody) return;
    customerCatalogTableBody.innerHTML = "";
    const query = (customerCatalogSearch.value || "").trim().toLowerCase();
    
    const filtered = state.customers.filter(item => 
        (item.name || "").toLowerCase().includes(query) || (item.phone || "").toLowerCase().includes(query)
    );
    
    if (filtered.length === 0) {
        customerCatalogTableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">
                    No customers found.
                </td>
            </tr>
        `;
        return;
    }
    
    filtered.forEach(item => {
        const tr = document.createElement("tr");
        tr.style.borderBottom = "1px solid var(--border-color)";
        
        tr.innerHTML = `
            <td style="padding: 12px 16px; font-family: monospace; font-size: 13px; color: var(--text-secondary);">${item.id}</td>
            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: var(--text-primary);">${escapeHTML(item.name)}</td>
            <td style="padding: 12px 16px; font-size: 14px; color: var(--text-secondary);">${escapeHTML(item.phone)}</td>
            <td style="padding: 12px 16px; font-size: 14px; color: var(--text-secondary); max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHTML(item.address || "-")}</td>
            <td style="padding: 12px 16px; text-align: right; display: flex; justify-content: flex-end; gap: 8px;">
                <button class="qty-btn btn-edit-customer" title="Edit" style="background: var(--primary-bg); color: var(--primary); border: 1px solid rgba(242,78,30,0.15); width: 30px; height: 30px; border-radius: 6px; cursor: pointer;"><i class="fa-solid fa-pen"></i></button>
                <button class="qty-btn btn-delete-customer" title="Delete" style="background: var(--danger-bg); color: var(--danger); border: 1px solid rgba(220,38,38,0.15); width: 30px; height: 30px; border-radius: 6px; cursor: pointer;"><i class="fa-solid fa-trash-can"></i></button>
            </td>
        `;
        
        tr.querySelector(".btn-edit-customer").addEventListener("click", () => openEditCustomerForm(item.id));
        tr.querySelector(".btn-delete-customer").addEventListener("click", () => deleteCustomer(item.id));
        
        customerCatalogTableBody.appendChild(tr);
    });
}

function openAddCustomerForm() {
    state.editingCustomerId = null;
    customerFormTitle.textContent = "Add Customer";
    custPhone.value = "";
    custName.value = "";
    custAddress.value = "";
    customerFormModal.classList.add("show");
}

function openEditCustomerForm(id) {
    const item = state.customers.find(c => Number(c.id) === Number(id));
    if (!item) return;
    
    state.editingCustomerId = id;
    customerFormTitle.textContent = "Edit Customer";
    custPhone.value = item.phone;
    custName.value = item.name;
    custAddress.value = item.address || "";
    customerFormModal.classList.add("show");
}

function closeCustomerFormModal() {
    customerFormModal.classList.remove("show");
}

async function handleCustomerFormSubmit(e) {
    e.preventDefault();
    
    const phone = custPhone.value.trim();
    const name = custName.value.trim();
    const address = custAddress.value.trim();
    
    if (!name || !phone) {
        showToast("Validation Error", "Name and Phone are required.", "error");
        return;
    }
    
    const isEdit = state.editingCustomerId !== null;
    const url = isEdit ? `/api/customers/${encodeURIComponent(state.editingCustomerId)}` : "/api/customers";
    const method = isEdit ? "PUT" : "POST";
    
    try {
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, phone, address })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast("Customer Saved", data.message || "Customer saved successfully.", "success");
            closeCustomerFormModal();
            await fetchCustomers();
            renderCustomerCatalog();
        } else {
            showToast("Error saving customer", data.error || "Operation failed.", "error");
        }
    } catch (e) {
        showToast("Connection Error", "Failed to contact database service.", "error");
    }
}

async function deleteCustomer(id) {
    const confirmed = await confirmAction("Are you sure you want to delete this customer?");
    if (!confirmed) return;
    
    try {
        const res = await fetch(`/api/customers/${encodeURIComponent(id)}`, {
            method: "DELETE"
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast("Customer Deleted", "Customer removed from database.", "success");
            await fetchCustomers();
            renderCustomerCatalog();
        } else {
            showToast("Error deleting customer", data.error || "Operation failed.", "error");
        }
    } catch (e) {
        showToast("Connection Error", "Failed to contact database service.", "error");
    }
}

// Make functions accessible globally for onclick triggers
window.openEditProductForm = openEditProductForm;
window.deleteProduct = deleteProduct;
window.openEditCustomerForm = openEditCustomerForm;
window.deleteCustomer = deleteCustomer;
