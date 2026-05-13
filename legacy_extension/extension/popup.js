document.addEventListener('DOMContentLoaded', async () => {
    const platformEl = document.getElementById('platform');
    const platformBadge = document.getElementById('platformBadge');
    const shopIdRow = document.getElementById('shopIdRow');
    const shopidEl = document.getElementById('shopId');
    const itemidEl = document.getElementById('itemId');
    const totalEl = document.getElementById('totalReviews');
    const statusEl = document.getElementById('status');
    const progressEl = document.getElementById('progressBar');
    const progressContainer = document.getElementById('progressContainer');
    const crawlBtn = document.getElementById('crawlBtn');
    
    // Lấy tab hiện tại
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab.url;
    const tabId = tab.id;
    
    // Detect platform và parse IDs
    let platform = null;
    let shopid = null;
    let itemid = null;
    
    // Shopee: https://shopee.vn/...i.{shopid}.{itemid}
    const shopeeMatch = url.match(/shopee\.vn.*i\.(\d+)\.(\d+)/);
    // Lazada: https://www.lazada.vn/products/...-i{itemid}(-s{sellerId})?.html
    const lazadaMatch = url.match(/lazada\.vn\/products\/.*-i(\d+)/);
    
    if (shopeeMatch) {
        platform = 'shopee';
        shopid = shopeeMatch[1];
        itemid = shopeeMatch[2];
        document.body.className = 'shopee';
        platformEl.textContent = 'Shopee';
        platformBadge.textContent = 'SHOPEE';
        platformBadge.className = 'platform-badge shopee';
        shopIdRow.style.display = 'block';
        shopidEl.textContent = shopid;
        itemidEl.textContent = itemid;
    } else if (lazadaMatch) {
        platform = 'lazada';
        itemid = lazadaMatch[1];
        document.body.className = 'lazada';
        platformEl.textContent = 'Lazada';
        platformBadge.textContent = 'LAZADA';
        platformBadge.className = 'platform-badge lazada';
        shopIdRow.style.display = 'none';
        itemidEl.textContent = itemid;
    } else {
        statusEl.textContent = '❌ Không phải trang sản phẩm Shopee/Lazada!';
        statusEl.className = 'status error';
        crawlBtn.disabled = true;
        return;
    }

    // Gửi message đến content script để lấy review count
    async function getReviewCount() {
        try {
            const message = platform === 'shopee' 
                ? { action: 'getReviewCount', shopid, itemid }
                : { action: 'getReviewCount', itemId: itemid };
            
            // Thử inject content script nếu chưa có
            try {
                await chrome.scripting.executeScript({
                    target: { tabId },
                    files: [platform === 'shopee' ? 'content.js' : 'content_lazada.js']
                });
                // Đợi script load
                await new Promise(r => setTimeout(r, 500));
            } catch (injectErr) {
                // Có thể đã inject rồi, ignore
                console.log('Script inject attempt:', injectErr.message);
            }
                
            const response = await chrome.tabs.sendMessage(tabId, message);
            console.log('getReviewCount response:', response);
            if (response && response.success) {
                return { total: response.total, success: true };
            }
            return { total: 0, success: false, error: response?.error, raw: response?.raw };
        } catch (e) {
            console.error('getReviewCount error:', e);
            return { total: 0, success: false, error: e.message + '. Hãy refresh trang (F5) và thử lại.' };
        }
    }
    
    const result = await getReviewCount();
    totalEl.textContent = result.total;
    
    if (!result.success) {
        statusEl.textContent = `❌ Lỗi: ${result.error || 'Unknown'}`;
        if (result.raw) {
            console.log('Raw response:', result.raw);
        }
        statusEl.className = 'status error';
    } else if (result.total === 0) {
        statusEl.textContent = '⚠️ Sản phẩm chưa có reviews!';
        statusEl.className = 'status';
    } else {
        statusEl.textContent = `✅ Sẵn sàng crawl ${result.total} reviews`;
        statusEl.className = 'status success';
    }
    
    // Lắng nghe progress updates từ content script
    chrome.runtime.onMessage.addListener((message) => {
        if (message.action === 'progress') {
            const percent = Math.min(100, Math.round((message.current / message.total) * 100));
            progressContainer.style.display = 'block';
            progressEl.style.width = percent + '%';
            statusEl.textContent = `⏳ ${message.status}`;
        }
    });
    
    // Hàm crawl tất cả reviews qua content script
    async function crawlAllReviews() {
        statusEl.textContent = '⏳ Đang crawl...';
        statusEl.className = 'status';
        crawlBtn.disabled = true;
        progressContainer.style.display = 'block';
        progressEl.style.width = '0%';
        
        try {
            const message = platform === 'shopee'
                ? { action: 'crawlReviews', shopid, itemid }
                : { action: 'crawlReviews', itemId: itemid };
            
            const result = await chrome.tabs.sendMessage(tabId, message);
            
            if (!result || !result.success) {
                throw new Error(result?.error || 'Không nhận được response');
            }
            
            // Download được handle bởi injected.js (on-page notification)
            progressEl.style.width = '100%';
            statusEl.textContent = `✅ Hoàn thành! File đã được tải xuống`;
            statusEl.className = 'status success';
            crawlBtn.textContent = '🚀 Thử lại';
            crawlBtn.disabled = false;
            
        } catch (e) {
            statusEl.textContent = '❌ Lỗi: ' + e.message;
            statusEl.className = 'status error';
            crawlBtn.disabled = false;
        }
    }
    
    crawlBtn.addEventListener('click', crawlAllReviews);
});
