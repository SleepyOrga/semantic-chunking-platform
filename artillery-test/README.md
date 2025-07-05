# 📦 Artillery Test - File Upload (Multipart)

Thư mục này chứa các script dùng [Artillery](https://www.artillery.io/) để **load test API upload file** (multipart/form-data), mô phỏng nhiều người dùng đồng thời.

---

## 📁 Cấu trúc thư mục

artillery-test/
├── upload-test.yml # File cấu hình Artillery test
├── multipartUpload.js # Custom processor để gửi multipart/form-data giống frontend
├── test.pdf # File giả lập để upload
├── files.csv # Payload chứa danh sách username
└── README.md # Hướng dẫn sử dụng

### 1. Cài Artillery (nếu chưa có)

```bash
npm install -g artillery
```

### 2.  Chạy test

```bash
artillery run upload-test.yml
```

### 3. Mở http://54.92.209.245:15672/#/queues/%2F/file-process-queue để xem