# E-commerce Server

Thư mục này chứa source code backend.

Compose chạy chính thức đã được chuyển lên thư mục gốc:

`/home/dezai/Documents/code/AI/tieu-luan-que/e-commerce-microservice/docker-compose.yaml`

Nếu muốn chạy toàn hệ thống, hãy dùng:

```bash
cd /home/dezai/Documents/code/AI/tieu-luan-que/e-commerce-microservice
docker compose up --build
```

README tổng hợp chi tiết nằm ở:

`/home/dezai/Documents/code/AI/tieu-luan-que/e-commerce-microservice/readme.md`

## AI Service

`ai_service` hiện có 2 chế độ chính:

1. `/api/ai/chat`
   - Giữ lại intent classifier cũ cho các câu chào hỏi/chung chung.
   - Tự động chuyển sang retrieval khi câu hỏi có nhắc tới `product`, `order`, `customer`, `email`, `sku`, `đơn hàng`, `khách hàng`, `sản phẩm`.
   - Khi đó service sẽ gọi trực tiếp `user_service`, `product_service`, `order_service` để đọc dữ liệu thật.

2. `/api/ai/search`
   - Trả về các bản ghi được xếp hạng gần nhất theo query.
   - Hữu ích để test lớp RAG độc lập trước khi ghép vào chatbot.

### Lưu ý về LLaMA

Train base model LLaMA từ đầu không thực tế trong repo này.
Nếu muốn dùng LLaMA, hướng khả thi là:

- dùng base model có sẵn,
- rồi fine-tune bằng LoRA/QLoRA trên dữ liệu hội thoại và Q&A nội bộ,
- sau đó dùng nó làm lớp sinh câu trả lời trên các context lấy về từ RAG.

Hiện tại repo này chỉ scaffold phần retrieval và prompt assembly, chưa có pipeline fine-tune LLaMA hoàn chỉnh.

### Training với dataset Kaggle

`ai_service/train_models_kaggle.py` đã được nâng cấp để train từ dataset thật thay vì chỉ dùng vài câu hardcode.

Script hỗ trợ:

- đọc `csv`, `json`, `jsonl`
- tự dò cột text từ các tên như `text`, `sentence`, `utterance`, `query`, `message`
- tự dò cột label từ các tên như `intent`, `label`, `category`, `class`
- map nhãn phổ biến về intent nội bộ của service
- lưu thêm `training_metadata.json` để `GET /api/ai/health` trả ra thông tin train

Ví dụ train local:

```bash
cd /home/dezai/Documents/code/AI/tieu-luan-que/e-commerce-microservice/e-commerce-server/ai_service
python3 train_models_kaggle.py --dataset ./data/intent_seed_dataset.csv
```

Ví dụ train bằng file Kaggle:

```bash
cd /home/dezai/Documents/code/AI/tieu-luan-que/e-commerce-microservice/e-commerce-server/ai_service
python3 train_models_kaggle.py --dataset /path/to/kaggle_dataset.csv --text-column text --label-column intent
```

Nếu muốn dùng dataset Kaggle trong Docker, mount file dataset vào `ai_service` rồi build lại container.
