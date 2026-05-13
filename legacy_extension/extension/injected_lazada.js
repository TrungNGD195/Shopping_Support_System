// Injected script cho Lazada - chạy trong MAIN world
// Có thể gọi fetch như chính trang web để bypass anti-bot

(function() {
    // Guard: chỉ inject 1 lần
    if (window.__LAZADA_CRAWLER_INJECTED__) {
        console.log('[Lazada Crawler] Already injected, skipping...');
        return;
    }
    window.__LAZADA_CRAWLER_INJECTED__ = true;
    
    // Flag để ngăn crawl trùng
    let isCrawling = false;
    
    // Lắng nghe request từ content script
    window.addEventListener('lazada_crawler_request', async (event) => {
        const { action, itemId, requestId } = event.detail;
        
        if (action === 'getReviewCount') {
            const result = await getReviewCount(itemId);
            window.dispatchEvent(new CustomEvent('lazada_crawler_response', {
                detail: { requestId, ...result }
            }));
        } else if (action === 'crawlReviews') {
            // Ngăn crawl trùng
            if (isCrawling) {
                window.dispatchEvent(new CustomEvent('lazada_crawler_response', {
                    detail: { requestId, success: false, error: 'Đang crawl, vui lòng đợi...' }
                }));
                return;
            }
            isCrawling = true;
            try {
                await crawlAndDownload(itemId);
                window.dispatchEvent(new CustomEvent('lazada_crawler_response', {
                    detail: { requestId, success: true, message: 'Download triggered' }
                }));
            } finally {
                isCrawling = false;
            }
        }
    });

    async function getReviewCount(itemId) {
        try {
            // Lazada API endpoint
            const url = `https://my.lazada.vn/pdp/review/getReviewList?itemId=${itemId}&pageSize=1&pageNo=1&filter=0&sort=0`;
            console.log('[Lazada Crawler] Fetching:', url);
            
            const response = await fetch(url, { 
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            console.log('[Lazada Crawler] Response status:', response.status);
            console.log('[Lazada Crawler] Response headers:', [...response.headers.entries()]);
            
            // Check nếu bị redirect/block
            const contentType = response.headers.get('content-type');
            const text = await response.text();
            console.log('[Lazada Crawler] Content-Type:', contentType);
            console.log('[Lazada Crawler] Response body (first 500):', text.substring(0, 500));
            
            if (!contentType || !contentType.includes('application/json')) {
                // Thử parse anyway vì có thể content-type sai
                try {
                    const data = JSON.parse(text);
                    console.log('[Lazada Crawler] Parsed JSON despite wrong content-type:', data);
                    if (data.model && data.model.paging) {
                        return { success: true, total: data.model.paging.totalResults || 0 };
                    }
                } catch (e) {
                    console.log('[Lazada Crawler] Failed to parse as JSON:', e.message);
                }
                return { success: false, error: 'Anti-bot detected (non-JSON response)' };
            }
            
            const data = JSON.parse(text);
            console.log('[Lazada Crawler] API response:', data);
            console.log('[Lazada Crawler] model:', data.model);
            console.log('[Lazada Crawler] model.paging:', data.model?.paging);
            console.log('[Lazada Crawler] model.ratings:', data.model?.ratings);
            
            // Try multiple possible locations for total count
            let total = 0;
            if (data.model) {
                // Check paging object
                if (data.model.paging) {
                    total = data.model.paging.totalItems || data.model.paging.totalResults || data.model.paging.total || 0;
                    console.log('[Lazada Crawler] Found in paging:', total);
                }
                // Check ratings object
                if (!total && data.model.ratings) {
                    total = data.model.ratings.reviewCount || data.model.ratings.rateCount || data.model.ratings.totalCount || 0;
                    console.log('[Lazada Crawler] Found in ratings:', total);
                }
                // Check item object
                if (!total && data.model.item) {
                    total = data.model.item.reviewCount || data.model.item.ratingCount || 0;
                    console.log('[Lazada Crawler] Found in item:', total);
                }
            }
            
            if (total > 0) {
                return { success: true, total };
            }
            
            if (data.success === false) {
                return { success: false, error: data.error?.message || 'API Error' };
            }
            return { success: false, error: 'Could not find review count in response' };
        } catch (e) {
            console.error('[Lazada Crawler] Exception:', e);
            return { success: false, error: e.message };
        }
    }

    async function crawlAndDownload(itemId) {
        const allReviews = [];
        const pageSize = 50;
        const seenIds = new Set();
        const starCounts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0};
        
        // Lấy tổng số reviews
        const countResult = await getReviewCount(itemId);
        if (!countResult.success) {
            alert(`[Lazada Crawler] Lỗi: ${countResult.error}`);
            return;
        }
        
        const total = countResult.total;
        if (total === 0) {
            alert('[Lazada Crawler] Sản phẩm chưa có reviews!');
            return;
        }
        
        console.log(`[Lazada Crawler] Bắt đầu crawl ${total} reviews...`);
        
        // Tạo notification element
        const notification = document.createElement('div');
        notification.id = 'lazada-crawler-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #0f146d 0%, #f85606 100%);
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: bold;
            z-index: 999999;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            font-family: 'Segoe UI', sans-serif;
        `;
        notification.innerHTML = `🚀 Đang crawl: 0/${total} reviews...`;
        document.body.appendChild(notification);
        
        // Lazada filters: 0=All, 1=5star, 2=4star, 3=3star, 4=2star, 5=1star, 6=with content, 7=with media
        // Crawl tất cả filters để lấy được nhiều reviews nhất
        const filters = [0, 1, 2, 3, 4, 5, 6, 7];
        const filterLabels = {
            0: 'Tất cả', 
            1: '5⭐', 2: '4⭐', 3: '3⭐', 4: '2⭐', 5: '1⭐',
            6: 'Có nội dung', 
            7: 'Có hình/video'
        };
        
        for (const filter of filters) {
            let page = 1;
            let emptyCount = 0;
            const maxEmpty = 2; // Giảm để nhanh hơn
            let noNewStreak = 0; // Đếm số page liên tiếp không có review mới
            
            console.log(`[Lazada Crawler] Crawl filter=${filter} (${filterLabels[filter]})...`);
            
            while (true) {
                try {
                    // Lazada dùng 'pageNo' cho pagination
                    const url = `https://my.lazada.vn/pdp/review/getReviewList?itemId=${itemId}&pageSize=${pageSize}&pageNo=${page}&filter=${filter}&sort=0`;
                    console.log(`[Lazada Crawler] Fetching page ${page}: ${url}`);
                    
                    const response = await fetch(url, { 
                        credentials: 'include',
                        headers: { 'Accept': 'application/json' }
                    });
                    
                    const contentType = response.headers.get('content-type');
                    if (!contentType || !contentType.includes('application/json')) {
                        console.log('[Lazada Crawler] Anti-bot detected, waiting...');
                        await new Promise(r => setTimeout(r, 3000));
                        emptyCount++;
                        if (emptyCount >= maxEmpty) break;
                        continue;
                    }
                    
                    const data = await response.json();
                    console.log(`[Lazada Crawler] Page ${page} response paging:`, data.model?.paging);
                    
                    if (!data.model || !data.model.items || data.model.items.length === 0) {
                        emptyCount++;
                        if (emptyCount >= maxEmpty) {
                            console.log(`[Lazada Crawler] Hết data filter=${filter}`);
                            break;
                        }
                        await new Promise(r => setTimeout(r, 1000));
                        continue;
                    }
                    
                    emptyCount = 0;
                    let batchAdded = 0;
                    
                    for (const item of data.model.items) {
                        // Lazada dùng reviewRateId làm unique ID
                        const uid = item.reviewRateId || item.id || item.reviewId || `${item.reviewTime}_${item.buyerName}_${item.reviewContent?.substring(0,20)}`;
                        if (!seenIds.has(uid)) {
                            seenIds.add(uid);
                            batchAdded++;
                            
                            const star = item.rating || 0;
                            if (star >= 1 && star <= 5) {
                                starCounts[star]++;
                            }
                            
                            allReviews.push({
                                id: item.reviewRateId || item.id || item.reviewId,
                                rating: item.rating,
                                content: item.reviewContent || '',
                                buyerName: item.buyerName || '',
                                reviewTime: item.reviewTime,
                                boughtDate: item.boughtDate || '',
                                skuInfo: item.skuInfo || '',
                                images: item.images || [],
                                videos: item.videos || [],
                                likeCount: item.likeCount || 0,
                                replyCount: item.replyCount || 0
                            });
                        }
                    }
                    
                    console.log(`[Lazada Crawler] Filter=${filter} page=${page}: +${batchAdded} new`);
                    
                    // Track số pages liên tiếp không có reviews mới
                    if (batchAdded === 0) {
                        noNewStreak++;
                        if (noNewStreak >= 3) {
                            console.log(`[Lazada Crawler] Skip filter=${filter}: 3 pages không có review mới`);
                            break;
                        }
                    } else {
                        noNewStreak = 0;
                    }
                    
                    const percent = Math.round((allReviews.length / total) * 100);
                    notification.innerHTML = `🚀 Crawl ${filterLabels[filter]}: ${allReviews.length}/${total} (${percent}%)`;
                    
                    // Check nếu đã hết pages
                    if (data.model.items.length < pageSize) {
                        console.log(`[Lazada Crawler] Hết pages filter=${filter}`);
                        break;
                    }
                    
                    page++;
                    // Random delay 500-1500ms để tránh rate limit
                    const delay = 500 + Math.random() * 1000;
                    await new Promise(r => setTimeout(r, delay));
                    
                } catch (e) {
                    console.log(`[Lazada Crawler] Error: ${e.message}`);
                    emptyCount++;
                    if (emptyCount >= maxEmpty) break;
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
        }
        
        // Log phân bố
        console.log(`[Lazada Crawler] === PHÂN BỐ THEO SAO ===`);
        for (let i = 5; i >= 1; i--) {
            console.log(`[Lazada Crawler] ${i}⭐: ${starCounts[i]}`);
        }
        console.log(`[Lazada Crawler] ========================`);
        
        // Download file
        const exportData = {
            platform: 'lazada',
            itemId: itemId,
            total_reviews: allReviews.length,
            star_distribution: starCounts,
            crawled_at: new Date().toISOString(),
            reviews: allReviews
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `lazada_reviews_${itemId}.json`;
        a.click();
        URL.revokeObjectURL(blobUrl);
        
        // Show complete
        const distText = `5⭐:${starCounts[5]} 4⭐:${starCounts[4]} 3⭐:${starCounts[3]} 2⭐:${starCounts[2]} 1⭐:${starCounts[1]}`;
        notification.innerHTML = `✅ Đã crawl ${allReviews.length}/${total}<br><small>${distText}</small>`;
        notification.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
        setTimeout(() => notification.remove(), 8000);
        
        console.log(`[Lazada Crawler] ✅ Hoàn thành! Đã crawl ${allReviews.length} reviews`);
    }
    
    console.log('[Lazada Crawler] Injected script ready!');
})();
