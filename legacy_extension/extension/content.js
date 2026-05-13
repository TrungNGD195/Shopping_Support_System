// Content script - injects code vào MAIN world của page
// để bypass extension detection của Shopee

(function() {
    // Inject script vào page MAIN world
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('injected.js');
    script.onload = function() {
        this.remove();
    };
    (document.head || document.documentElement).appendChild(script);
    
    // Pending requests
    const pendingRequests = new Map();
    let requestId = 0;
    
    // Lắng nghe response từ injected script
    window.addEventListener('shopee_crawler_response', (event) => {
        const { requestId: rid, ...data } = event.detail;
        const resolve = pendingRequests.get(rid);
        if (resolve) {
            resolve(data);
            pendingRequests.delete(rid);
        }
    });
    
    // Lắng nghe progress từ injected script
    window.addEventListener('shopee_crawler_progress', (event) => {
        chrome.runtime.sendMessage({ action: 'progress', ...event.detail });
    });
    
    // Gửi request đến injected script
    function sendToPage(action, shopid, itemid) {
        return new Promise((resolve) => {
            const rid = ++requestId;
            pendingRequests.set(rid, resolve);
            
            window.dispatchEvent(new CustomEvent('shopee_crawler_request', {
                detail: { action, shopid, itemid, requestId: rid }
            }));
            
            // Timeout 60s
            setTimeout(() => {
                if (pendingRequests.has(rid)) {
                    pendingRequests.delete(rid);
                    resolve({ success: false, error: 'Request timeout' });
                }
            }, 60000);
        });
    }
    
    // Lắng nghe message từ popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'getReviewCount') {
            sendToPage('getReviewCount', request.shopid, request.itemid).then(sendResponse);
            return true;
        } else if (request.action === 'crawlReviews') {
            sendToPage('crawlReviews', request.shopid, request.itemid).then(sendResponse);
            return true;
        }
    });
    
    console.log('[Shopee Crawler] Content script loaded');
})();
