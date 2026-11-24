// Mỗi bộ ảnh hoạt động độc lập. Các nút thumbnail dùng được cả bằng bàn phím.
document.querySelectorAll('[data-product-gallery]').forEach(gallery => {
    const mainImage = gallery.querySelector('[data-gallery-main]');
    const thumbnails = gallery.querySelectorAll('[data-gallery-thumbnail]');
    const positionLabel = gallery.querySelector('[data-gallery-position]');

    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', () => {
            mainImage.src = thumbnail.dataset.imageUrl;
            mainImage.alt = thumbnail.dataset.imageAlt;

            thumbnails.forEach(button => {
                button.setAttribute('aria-pressed', String(button === thumbnail));
            });

            if (positionLabel) {
                positionLabel.textContent = `${thumbnail.dataset.imageNumber} / ${thumbnails.length}`;
            }
        });
    });
});
