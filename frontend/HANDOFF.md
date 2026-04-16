# 🚀 FreshRoute - Technical Handoff Document

Tài liệu này dành cho Backend Developer và AI Engineer để nắm bắt cấu trúc UI/UX Front-end hiện tại và các module cần tích hợp API.

## 1. Tình trạng Front-end (FE)
- **Tech Stack**: Next.js 16 (App Router), React 19, Tailwind CSS 4, Framer Motion, Lucide React/React Icons.
- **Tình trạng dữ liệu**: Hiện tại đang sử dụng **MOCK DATA** (dữ liệu giả) được fix cứng trong các component.
- **Nhiệm vụ của BE/AI**: Cung cấp API trả về đúng cấu trúc JSON bên dưới để FE thay thế dữ liệu giả.

---

## 2. Các luồng cần Backend (BE) xử lý

### 2.1. Quản lý Sản phẩm & Combo (Customer Page)
- **Vị trí FE**: `src/app/customer/page.js`
- **API cần thiết**: `GET /api/v1/combos`
- **Output mong đợi**: BE cần trả về list các Combo giải cứu với cấu trúc:
  ```json
  {
    "id": 1,
    "name": "Combo Phở Bò Chóp",
    "description": "Đủ khẩu phần 2 người ăn...",
    "originalPrice": 185000,
    "newPrice": 139000,
    "impactKg": 0.5, // Số kg rác thải giảm được
    "image": "url_anh",
    "ingredients": [
      { "name": "Thịt bò 500g", "status": "warning" } // warning = sắp hết hạn
    ]
  }
  ```

### 2.2. Luồng Thanh Toán (Cart & Checkout)
- **Vị trí FE**: `src/app/customer/cart/page.js`
- **API cần thiết**: `POST /api/v1/orders/checkout`
- **Nhiệm vụ BE**: 
  - Tiếp nhận danh sách Cart Items.
  - Tích hợp cổng thanh toán Sandbox (MoMo / VNPay). Xử lý call webhook.
  - Lưu vào DB và cộng dồn điểm `Impact` (Giải cứu Kim cương / Kg CO2) cho User.

### 2.3. Dashboard Admin (Hệ thống Analytics)
- **Vị trí FE**: `src/app/admin/page.js` và `src/components/admin/AnalyticsDashboard.jsx`
- **API cần thiết**: `GET /api/v1/admin/analytics`
- **Nhiệm vụ BE**: Trả về thống kê thực tế: Số lượng thực phẩm cứu được, phân tích lợi nhuận, biểu đồ chart doanh thu theo khung thời gian.

---

## 3. Các luồng cần AI Engineer xử lý

### 3.1. Chatbot Trợ lý Ẩm thực (AI Chat)
- **Vị trí FE**: `src/app/customer/ai-chat/page.js`
- **API cần thiết**: `POST /api/v1/ai/chat`
- **Nhiệm vụ AI**: Chatbot không chỉ trả về **text** (văn bản) thông thường, mà FE cần AI mô phỏng việc trả về **Structured Data** (JSON) để FE render UI.
- **Ví dụ luồng tương tác**:
  - *User chat*: "Nhà tôi còn thịt bò, đang đói quá"
  - *AI API Response*:
    ```json
    {
      "reply_text": "Tuyệt vời, tôi tìm thấy một số combo đi kèm với thịt bò đang giảm giá:",
      "ui_component_type": "BUNDLE_CARD",
      "data": { 
         "name": "Gia vị Phở trọn gói", 
         "price": 45000, 
         "instructions": ["Bước 1", "Bước 2..."] 
      }
    }
    ```
  - *Lưu ý cho AI*: Cần có model NLP để bóc tách ý định (Intent: tìm công thức, tìm hàng sắp hết date) và truy vấn Vector DB (nếu có) để match với số lượng nguyên liệu thừa trong kho của cửa hàng.

### 3.2. Thuật toán tối ưu Giá (Dynamic Pricing)
- **Nhiệm vụ AI**: Viết thuật toán (ví dụ Reinforcement Learning) dựa trên số lượng tuần kho, % còn lại hạn sử dụng để tự động tính ra `newPrice` tối ưu mức lợi nhuận lớn nhất mà vẫn thanh lý được hàng. Lúc đó BE lưu lại kết quả và xuất ra cho FE.