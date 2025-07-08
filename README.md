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

Tạo Virtual Environment (môi trường ảo)
bash
Copy
Edit
python -m venv venv
Kích hoạt môi trường ảo:

Windows:

bash
Copy
Edit
venv\Scripts\activate
