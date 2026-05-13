// Injected script chạy trong MAIN world của page
// Có thể gọi fetch như chính trang web

(function() {
    // Lắng nghe request từ content script
    window.addEventListener('shopee_crawler_request', async (event) => {
        const { action, shopid, itemid, requestId } = event.detail;
        
        if (action === 'getReviewCount') {
            const result = await getReviewCount(shopid, itemid);
            window.dispatchEvent(new CustomEvent('shopee_crawler_response', {
                detail: { requestId, ...result }
            }));
        } else if (action === 'crawlReviews') {
            // Crawl và tự download - không cần popup
            await crawlAndDownload(shopid, itemid);
            window.dispatchEvent(new CustomEvent('shopee_crawler_response', {
                detail: { requestId, success: true, message: 'Download triggered' }
            }));
        }
    });

    async function getReviewCount(shopid, itemid) {
        try {
            const url = `https://shopee.vn/api/v2/item/get_ratings?filter=0&flag=1&itemid=${itemid}&limit=1&offset=0&shopid=${shopid}&type=0`;
            const response = await fetch(url, { credentials: 'include' });
            const data = await response.json();
            console.log('[Shopee Crawler] API response:', data);
            
            if (data.data && data.data.item_rating_summary) {
                return {
                    success: true,
                    total: data.data.item_rating_summary.rating_total || 0
                };
            }
            if (data.error) {
                return { success: false, error: `API Error: ${data.error}` };
            }
            return { success: false, error: 'No rating data' };
        } catch (e) {
            return { success: false, error: e.message };
        }
    }

    async function crawlAndDownload(shopid, itemid) {
        const allReviews = [];
        const limit = 50;
        const maxEmptyRetries = 3;
        const seenIds = new Set(); // Để tránh duplicate
        const starCounts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}; // Đếm theo rating_star THỰC TẾ
        
        // Lấy tổng số reviews
        const countResult = await getReviewCount(shopid, itemid);
        if (!countResult.success) {
            alert(`[Shopee Crawler] Lỗi: ${countResult.error}`);
            return;
        }
        
        const total = countResult.total;
        if (total === 0) {
            alert('[Shopee Crawler] Sản phẩm chưa có reviews!');
            return;
        }
        
        console.log(`[Shopee Crawler] Bắt đầu crawl ${total} reviews...`);
        
        // Tạo notification element
        const notification = document.createElement('div');
        notification.id = 'shopee-crawler-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #ee4d2d 0%, #ff6633 100%);
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
        
        // Shopee API: GIỚI HẠN CỨNG ~5000 reviews "pool" cho mỗi sản phẩm
        // Bất kể filter/type nào, API chỉ trả về reviews từ cùng 1 pool
        // Đây là thiết kế chống crawl của Shopee, không thể bypass qua API
        const filters = [0, 1, 2, 3, 4, 5]; // All + từng sao
        const filterLabels = {0: 'Tất cả', 1: '5⭐', 2: '4⭐', 3: '3⭐', 4: '2⭐', 5: '1⭐'};
        const sortTypes = [0, 1]; // Liên quan + Mới nhất
        
        for (const filter of filters) {
            for (const sortType of sortTypes) {
                let offset = 0;
                let emptyCount = 0;
                let filterTotal = 0;
                let addedCount = 0;
                let noNewReviewsStreak = 0; // Đếm số batch liên tiếp không có review mới
                
                console.log(`[Shopee Crawler] Đang crawl reviews ${filterLabels[filter]} (filter=${filter}, type=${sortType})...`);
                notification.innerHTML = `🚀 Crawl ${filterLabels[filter]} (sort=${sortType}): ${allReviews.length}/${total} tổng`;
                
                while (true) {
                    try {
                        const url = `https://shopee.vn/api/v2/item/get_ratings?filter=${filter}&flag=1&itemid=${itemid}&limit=${limit}&offset=${offset}&shopid=${shopid}&type=${sortType}`;
                    const response = await fetch(url, { credentials: 'include' });
                    const data = await response.json();
                    
                    if (data.error) {
                        console.log(`[Shopee Crawler] API error (${filterLabels[filter]}, offset ${offset}): ${data.error}`);
                        await new Promise(r => setTimeout(r, 2000));
                        emptyCount++;
                        if (emptyCount >= maxEmptyRetries) break;
                        continue;
                    }
                    
                    if (data.data && data.data.ratings && data.data.ratings.length > 0) {
                        emptyCount = 0;
                        let batchAdded = 0;
                        for (const r of data.data.ratings) {
                            // Dùng cmtid hoặc orderid làm unique ID (không bị trùng)
                            const uid = r.cmtid || r.orderid || `${r.ctime}_${r.author_username}_${r.comment?.substring(0,20)}`;
                            if (!seenIds.has(uid)) {
                                seenIds.add(uid);
                                batchAdded++;
                                addedCount++;
                                // Track theo rating_star THỰC TẾ (không phải filter)
                                const actualStar = r.rating_star;
                                if (actualStar >= 1 && actualStar <= 5) {
                                    starCounts[actualStar]++;
                                }
                                allReviews.push({
                                    cmtid: r.cmtid,
                                    orderid: r.orderid,
                                    rating_star: r.rating_star,
                                    comment: r.comment || '',
                                    author_username: r.author_username || '',
                                    ctime: r.ctime,
                                    date: new Date(r.ctime * 1000).toISOString(),
                                    product_items: r.product_items || [],
                                    images: r.images || [],
                                    videos: r.videos || []
                                });
                            }
                        }
                        filterTotal += data.data.ratings.length;
                        console.log(`[Shopee Crawler] ${filterLabels[filter]} (sort=${sortType}) batch: +${batchAdded} new (${data.data.ratings.length - batchAdded} dups)`);
                        
                        // Nếu không có review mới, đếm streak
                        if (batchAdded === 0) {
                            noNewReviewsStreak++;
                            if (noNewReviewsStreak >= 5) {
                                console.log(`[Shopee Crawler] Skip sort=${sortType}: 5 batches liên tiếp không có review mới`);
                                break;
                            }
                        } else {
                            noNewReviewsStreak = 0;
                        }
                    } else {
                        emptyCount++;
                        if (emptyCount >= maxEmptyRetries) {
                            console.log(`[Shopee Crawler] Hết data ${filterLabels[filter]} (sort=${sortType}): API=${filterTotal}, added=${addedCount}`);
                            break;
                        }
                        await new Promise(r => setTimeout(r, 1000));
                        continue;
                    }
                    
                    offset += limit;
                    const percent = Math.round((allReviews.length / total) * 100);
                    notification.innerHTML = `🚀 Crawl ${filterLabels[filter]} (sort=${sortType}): ${allReviews.length}/${total} (${percent}%)`;
                    
                    await new Promise(r => setTimeout(r, 100)); // Giảm delay để crawl nhanh hơn
                    
                } catch (e) {
                    console.log(`[Shopee Crawler] Error: ${e.message}`);
                    emptyCount++;
                    if (emptyCount >= maxEmptyRetries) break;
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
            
            console.log(`[Shopee Crawler] Xong ${filterLabels[filter]} (sort=${sortType}): from API=${filterTotal}, added=${addedCount}, total unique=${allReviews.length}`);
        } // end for sortType
        } // end for filter
        
        // Log phân bố theo sao thực tế
        console.log(`[Shopee Crawler] === PHÂN BỐ THEO SAO ===`);
        console.log(`[Shopee Crawler] 5⭐: ${starCounts[5]}`);
        console.log(`[Shopee Crawler] 4⭐: ${starCounts[4]}`);
        console.log(`[Shopee Crawler] 3⭐: ${starCounts[3]}`);
        console.log(`[Shopee Crawler] 2⭐: ${starCounts[2]}`);
        console.log(`[Shopee Crawler] 1⭐: ${starCounts[1]}`);
        console.log(`[Shopee Crawler] ========================`);
        
        // Tạo và download file
        const exportData = {
            shopid: shopid,
            itemid: itemid,
            total_reviews: allReviews.length,
            star_distribution: starCounts,
            crawled_at: new Date().toISOString(),
            reviews: allReviews
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `shopee_reviews_${shopid}_${itemid}.json`;
        a.click();
        URL.revokeObjectURL(blobUrl);
        
        // Hiển thị phân bố trên notification
        const distText = `5⭐:${starCounts[5]} 4⭐:${starCounts[4]} 3⭐:${starCounts[3]} 2⭐:${starCounts[2]} 1⭐:${starCounts[1]}`;
        notification.innerHTML = `✅ Đã crawl ${allReviews.length}/${total}<br><small>${distText}</small>`;
        notification.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
        setTimeout(() => notification.remove(), 8000);
        
        console.log(`[Shopee Crawler] ✅ Hoàn thành! Đã crawl ${allReviews.length}/${total} reviews`);
    }
    
    console.log('[Shopee Crawler] Injected script ready!');
})();
