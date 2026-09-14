document.addEventListener('DOMContentLoaded', function () {
    const cart = [];

    function formatMoney(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function getCartTotal() {
        return cart.reduce((acc, item) => acc + item.quantity * item.price, 0);
    }

    function renderCart() {
        const cartItems = document.getElementById('cart-items');
        const cartTotal = document.getElementById('cart-total');
        const checkoutTotal = document.getElementById('checkout-total');
        if (!cartItems || !cartTotal || !checkoutTotal) return;

        if (cart.length === 0) {
            cartItems.innerHTML = '<span class="cart-empty">Seu carrinho está vazio</span>';
            cartTotal.textContent = 'R$ 0,00';
            checkoutTotal.textContent = 'Total: R$ 0,00';
            return;
        }

        cartItems.innerHTML = '';
        cart.forEach(item => {
            const row = document.createElement('div');
            row.className = 'cart-item';
            row.innerHTML = `<span>${item.name} x${item.quantity}</span><span>${formatMoney(item.quantity * item.price)} <button data-remove="${item.id}">×</button></span>`;
            cartItems.appendChild(row);
        });

        const total = getCartTotal();
        cartTotal.textContent = formatMoney(total);
        checkoutTotal.textContent = 'Total: ' + formatMoney(total);
    }

    document.querySelectorAll('[data-product-id]').forEach(button => {
        button.addEventListener('click', function () {
            const product = {
                id: Number(this.dataset.productId),
                name: this.dataset.name,
                price: Number(this.dataset.price)
            };

            const existing = cart.find(item => item.id === product.id);
            if (existing) {
                existing.quantity += 1;
            } else {
                cart.push({ ...product, quantity: 1 });
            }

            renderCart();
        });
    });

    document.addEventListener('click', function (event) {
        if (event.target.matches('[data-remove]')) {
            const id = Number(event.target.dataset.remove);
            const item = cart.find(entry => entry.id === id);
            if (!item) return;
            if (item.quantity > 1) {
                item.quantity -= 1;
            } else {
                const index = cart.findIndex(entry => entry.id === id);
                cart.splice(index, 1);
            }
            renderCart();
        }
    });

    const checkoutButton = document.getElementById('checkout-button');
    const checkoutModal = document.getElementById('checkout-modal');
    const closeModal = document.getElementById('close-modal');
    const cancelCheckout = document.getElementById('cancel-checkout');

    if (checkoutButton && checkoutModal) {
        checkoutButton.addEventListener('click', function () {
            if (cart.length === 0) {
                alert('Adicione pelo menos um produto ao carrinho.');
                return;
            }
            checkoutModal.classList.remove('hidden');
        });
    }

    if (closeModal && checkoutModal) {
        closeModal.addEventListener('click', function () {
            checkoutModal.classList.add('hidden');
        });
    }

    if (cancelCheckout && checkoutModal) {
        cancelCheckout.addEventListener('click', function () {
            checkoutModal.classList.add('hidden');
        });
    }

    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function (event) {
            event.preventDefault();

            const restaurant_id = document.getElementById('restaurant_id')?.value;
            const customer_name = document.getElementById('customer_name').value.trim();
            const customer_phone = document.getElementById('customer_phone').value.trim();
            const order_type = document.getElementById('order_type').value;
            const payment_method = document.getElementById('payment_method').value;
            const address = document.getElementById('address').value.trim();
            const notes = document.getElementById('notes').value.trim();

            if (!customer_name || cart.length === 0) {
                alert('Preencha o nome e escolha pelo menos um produto.');
                return;
            }

            const payload = {
                restaurant_id: Number(restaurant_id),
                customer_name,
                customer_phone,
                order_type,
                address,
                payment_method,
                notes,
                items: cart.map(item => ({
                    product_id: item.id,
                    name: item.name,
                    price: item.price,
                    quantity: item.quantity
                }))
            };

            fetch('/api/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(result => {
                if (!result.success) {
                    alert(result.error || 'Erro ao criar pedido.');
                    return;
                }

                checkoutModal.classList.add('hidden');
                const message = 'Pedido #' + result.order_id + ' criado com sucesso!';
                alert(message);
                cart.length = 0;
                renderCart();
                checkoutForm.reset();
            })
            .catch(error => {
                alert('Erro ao criar pedido: ' + error);
            });
        });
    }

    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const term = this.value.toLowerCase().trim();
            document.querySelectorAll('.product-card').forEach(card => {
                const name = card.dataset.name.toLowerCase();
                const category = card.dataset.category.toLowerCase();
                card.style.display = (name.includes(term) || category.includes(term)) ? 'block' : 'none';
            });
        });
    }

    const statusSelects = document.querySelectorAll('[data-order-id]');
    statusSelects.forEach(select => {
        select.addEventListener('change', function () {
            const orderId = this.dataset.orderId;
            const status = this.value;
            fetch('/api/orders/' + orderId + '/status', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status })
            })
            .then(response => response.json())
            .then(result => {
                if (!result.success) {
                    alert(result.error || 'Erro ao atualizar pedido.');
                    return;
                }
                window.location.reload();
            });
        });
    });
});
