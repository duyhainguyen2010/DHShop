// Mở/đóng ô tìm kiếm trong header, hỗ trợ đóng bằng phím Escape.
const searchToggle = document.getElementById('search-toggle');
const searchPanel = document.getElementById('search-panel');
searchToggle?.addEventListener('click', () => {
    const open = searchPanel.hidden;
    searchPanel.hidden = !open;
    searchToggle.setAttribute('aria-expanded', String(open));
    if (open) document.getElementById('site-search').focus();
});
document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && searchPanel && !searchPanel.hidden) {
        searchPanel.hidden = true;
        searchToggle.setAttribute('aria-expanded', 'false');
        searchToggle.focus();
    }
});
// Thêm nhanh một sản phẩm và cập nhật số lượng giỏ mà không tải lại trang.
document.addEventListener('submit', async event => {
    const form = event.target.closest('.js-add-to-cart');
    if (!form) return;
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    const toastElement = document.getElementById('cart-toast');
    button.disabled = true;
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.message || 'Chưa thể thêm sản phẩm. Vui lòng thử lại.');
        document.querySelectorAll('.badge-cart').forEach(badge => badge.textContent = result.cart_count);
        toastElement.classList.replace('text-bg-danger', 'text-bg-success');
        toastElement.querySelector('.toast-body').textContent = result.message;
    } catch (error) {
        toastElement.classList.replace('text-bg-success', 'text-bg-danger');
        toastElement.querySelector('.toast-body').textContent = error.message;
    } finally {
        button.disabled = false;
        bootstrap.Toast.getOrCreateInstance(toastElement).show();
    }
});
// Dùng chung nút +/- cho trang sản phẩm và giỏ hàng.
document.addEventListener('click', event => {
    const button = event.target.closest('[data-quantity-step]');
    if (!button) return;
    const input = button.closest('.quantity-control').querySelector('input[type="number"]');
    const min = Number(input.min) || 1;
    const max = Number(input.max) || 999;
    input.value = Math.min(max, Math.max(min, (Number(input.value) || min) + Number(button.dataset.quantityStep)));
    if (input.closest('form').hasAttribute('data-auto-update')) input.closest('form').requestSubmit();
});
