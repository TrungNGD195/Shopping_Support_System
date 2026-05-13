// Content script cho Lazada - injects code vào MAIN world
// để bypass anti-bot của Lazada

(function() {
    // Guard: chỉ inject 1 lần
    if (window.__LAZADA_CONTENT_INJECTED__) {
        console.log('[Lazada Crawler] Content already injected, skipping...');
        return;
    }
    window.__LAZADA_CONTENT_INJECTED__ = true;
    
    // Inject script vào page MAIN world
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('injected_lazada.js');
    script.onload = function() {
        this.remove();
    };
    (document.head || document.documentElement).appendChild(script);
    
    // Pending requests  
    const pendingRequests = new Map();
    let requestId = 0;
    
    // Lắng nghe response từ injected script
    window.addEventListener('lazada_crawler_response', (event) => {
        const { requestId: rid, ...data } = event.detail;
        const resolve = pendingRequests.get(rid);
        if (resolve) {
            resolve(data);
            pendingRequests.delete(rid);
        }
    });
    
    // Lắng nghe progress từ injected script
    window.addEventListener('lazada_crawler_progress', (event) => {
        chrome.runtime.sendMessage({ action: 'progress', ...event.detail });
    });
    
    // Gửi request đến injected script
    function sendToPage(action, itemId) {
        return new Promise((resolve) => {
            const rid = ++requestId;
            pendingRequests.set(rid, resolve);
            
            window.dispatchEvent(new CustomEvent('lazada_crawler_request', {
                detail: { action, itemId, requestId: rid }
            }));
            
            // Timeout 120s cho Lazada (có thể chậm hơn)
            setTimeout(() => {
                if (pendingRequests.has(rid)) {
                    pendingRequests.delete(rid);
                    resolve({ success: false, error: 'Request timeout' });
                }
            }, 120000);
        });
    }
    
    // Lắng nghe message từ popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'getReviewCount') {
            sendToPage('getReviewCount', request.itemId).then(sendResponse);
            return true;
        } else if (request.action === 'crawlReviews') {
            sendToPage('crawlReviews', request.itemId).then(sendResponse);
            return true;
        }
    });
    
    console.log('[Lazada Crawler] Content script loaded');
})();
