# HƯỚNG DẪN GÁN NHÃN DỮ LIỆU (LABELING GUIDELINES)

## 1. Hệ thống nhãn (Labeling System)
Mỗi comment sẽ được đọc và gán số cho 4 cột: `Quality` (Chất lượng), `Price` (Giá cả), `Delivery` (Giao hàng), `Service` (Dịch vụ).
Sử dụng hệ thống 4 nhãn sau:
- **2 (Tích cực):** Có nhắc đến tiêu chí đó và khen ngợi, hài lòng.
- **1 (Trung tính):** Có nhắc đến nhưng chỉ mô tả khách quan, bình thường, không khen chê.
- **0 (Tiêu cực):** Có nhắc đến và chê bai, phàn nàn, thất vọng.
- **-1 (Không nhắc tới):** Câu comment hoàn toàn không đề cập đến tiêu chí này.

## 2. Chi tiết các khía cạnh (Aspects)
### A. Chất lượng (Quality)
- **Khen (2):** Vải mát, form chuẩn, dùng bền, xài mượt, thơm, xịn, chính hãng...
- **Chê (0):** Hàng fake, vải mỏng, rách, hỏng hóc, dùng mau hư, form xấu...

### B. Giá cả (Price)
- **Khen (2):** Rẻ, giá hợp lý, săn sale hời, đáng đồng tiền...
- **Chê (0):** Đắt, giá cao, không xứng đáng với giá tiền, phí tiền...

### C. Giao hàng (Delivery)
- **Khen (2):** Ship siêu nhanh, nhận hàng ngay trong ngày, đóng gói cẩn thận/kỹ càng...
- **Chê (0):** Giao quá lâu, ngâm đơn, hộp móp méo, rách bao bì, shipper thái độ...

### D. Dịch vụ (Service)
- **Khen (2):** Shop tư vấn nhiệt tình, có quà tặng kèm, cho kiểm hàng, đổi trả dễ dàng...
- **Chê (0):** Rep tin nhắn chậm, shop chảnh, gửi sai mẫu nhưng không giải quyết, lừa đảo...

## 3. Quy tắc xử lý xung đột (Conflict Resolution)
- **Nguyên tắc 1:** Nếu một câu khen chê lẫn lộn trong cùng 1 tiêu chí (VD: "Vải đẹp nhưng đường may hơi ẩu"), ưu tiên gán nhãn **0 (Tiêu cực)** để hệ thống cảnh báo cho người mua sau.
- **Nguyên tắc 2:** Nếu câu comment quá ngắn và chung chung (VD: "Tuyệt vời", "Chán"), hãy gán nhãn **2** hoặc **0** cho `Quality`, các cột khác đánh **-1**.