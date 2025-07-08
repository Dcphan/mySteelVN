# mySteelVN
# 🏗️ Steel Analysis Web App

Ứng dụng web hỗ trợ phân tích dữ liệu ngành thép, bao gồm các chức năng:

- 📤 Upload file dữ liệu (CSV/Excel)
- 📊 Hiển thị biểu đồ Pie và Line để trực quan hóa dữ liệu
- 📋 Bảng tổng hợp dữ liệu theo tháng

> 📁 Repo GitHub: https://github.com/Dcphan/mySteelVN

---

## 🌐 Các Trang Cần Test

| Chức năng | Địa chỉ URL |
|-----------|-------------|
| Upload dữ liệu | http://localhost:8000/upload |
| Biểu đồ Market Share (Pie Chart) | http://localhost:8000/chart/pie |
| Biểu đồ theo thời gian (Line Chart) | http://localhost:8000/chart/bar |
| Bảng tổng hợp theo tháng | http://localhost:8000/table/tonghopthang |

---

## 📦 Hướng Dẫn Cài Đặt

### 1. Clone repository

```bash
git clone https://github.com/Dcphan/mySteelVN.git
cd mySteelVN
```

### 2. Tạo Virtual Environment (môi trường ảo)
```bash
python -m venv venv
Kích hoạt môi trường ảo:```

Windows:
```bash
venv\Scripts\activate
```
✅ Khi kích hoạt thành công, bạn sẽ thấy dấu (venv) ở đầu dòng lệnh terminal.

### 3. Cài đặt các thư viện Python
```bash
pip install -r requirements.txt
```

### 4. Cài đặt Node.js

1. Cài đặt Node.js và npm
Tải tại: https://nodejs.org/

Kiểm tra cài đặt:

```bash
node -v
npm -v
```

2. Cài thư viện frontend (nếu có file package.json)
```bash
npm install
```

