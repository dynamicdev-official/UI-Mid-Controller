FROM python:3.9-slim

WORKDIR /app

# ลง Library ที่จำเป็น (เพิ่ม pandas ให้แล้วเผื่อใช้ dashboard)
RUN pip install streamlit requests pandas pillow

# Copy ไฟล์โค้ดเข้าไป
COPY . .

# เปิด Port (8502 — ไม่ซ้ำกับ agent-ui ที่ใช้ 8501)
EXPOSE 8502

# รันแอป
CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]
