# E-commerce Server

Thư mục này chứa source code backend.

Compose chạy chính thức đã được chuyển lên thư mục gốc:

`/home/dezai/Documents/code/tieu_luan_01/e-commerce-microservice/docker-compose.yaml`

Nếu muốn chạy toàn hệ thống, hãy dùng:

```bash
cd /home/dezai/Documents/code/tieu_luan_01/e-commerce-microservice
docker compose up --build
```

README tổng hợp chi tiết nằm ở:

`/home/dezai/Documents/code/tieu_luan_01/e-commerce-microservice/readme.md`

## AI Service

`ai_service` hiện kết hợp 3 lớp chính:

1. **Local deep learning intent classifier**
   - Model neural network được train từ dataset dạng Kaggle/CSV/JSON/JSONL.
   - Dùng để phân loại intent của câu hỏi: `greeting`, `product_inquiry`, `order_status`, `complaint`, `farewell`, `customer_lookup`, `unknown`.
   - Model được lưu tại `ai_service/models/intent_mlp_model.npz`.

2. **RAG retrieval**
   - Dùng Neo4j để lưu graph dữ liệu e-commerce và vector embedding.
   - Truy xuất dữ liệu thật từ `user_service`, `product_service`, `order_service`.
   - Khi user hỏi về sản phẩm, đơn hàng hoặc khách hàng, service lấy context phù hợp rồi đưa vào LLM.

3. **LLM response generation**
   - Hỗ trợ Gemini hoặc OpenAI để sinh câu trả lời cuối cùng bằng tiếng Việt.
   - LLM chỉ được phép dựa vào context RAG cho dữ liệu cụ thể như đơn hàng, sản phẩm, khách hàng.

### Endpoint chính

1. `/api/ai/chat`
   - Chạy local neural intent classifier trước để xác định loại câu hỏi.
   - Tự động chuyển sang RAG khi intent là `product_inquiry`, `order_status`, `customer_lookup`, hoặc câu hỏi có nhắc tới `product`, `order`, `customer`, `email`, `sku`, `đơn hàng`, `khách hàng`, `sản phẩm`.
   - Giới hạn scope retrieval theo intent:
     - `product_inquiry` -> `products`
     - `order_status` -> `orders`
     - `customer_lookup` -> `users`
   - Sau đó gọi Gemini/OpenAI để sinh câu trả lời cuối cùng.

2. `/api/ai/search`
   - Trả về các bản ghi được xếp hạng gần nhất theo query.
   - Hữu ích để test lớp RAG độc lập trước khi ghép vào chatbot.

3. `/api/ai/health`
   - Kiểm tra provider, Neo4j, local intent model và metadata training.

4. `/api/ai/trends`
   - Demo dự đoán trend đơn giản từ chuỗi `historical_sales`.
   - Endpoint này hiện chưa dùng deep learning.

### Mô hình deep learning local

File train chính:

`ai_service/train_models_kaggle.py`

Model hiện tại là một neural network MLP tự triển khai bằng `NumPy`, không phụ thuộc TensorFlow/PyTorch:

```text
Input text
-> tokenize word/bigram/character n-gram
-> binary feature vector
-> Dense(128) + ReLU
-> Dense(64) + ReLU
-> Dense(number_of_intents) + Softmax
-> intent + confidence
```

Optimizer:

```text
Adam optimizer
cross-entropy loss
weight decay
```

Các artifact sinh ra sau khi train:

```text
ai_service/models/intent_mlp_model.npz
ai_service/models/training_metadata.json
ai_service/models/fine_tune_train.jsonl
ai_service/models/fine_tune_valid.jsonl
```

Trong runtime, `main.py` load `intent_mlp_model.npz` khi service startup. Khi gọi `/api/ai/chat`, response sẽ có thêm source dạng:

```json
{
  "entity_type": "intent_classifier",
  "entity_id": "local_neural_mlp",
  "title": "product_inquiry",
  "score": 0.9998
}
```

Điều này cho biết intent được dự đoán bởi model deep learning local.

### RAG với Neo4j

RAG dùng dữ liệu từ các service nghiệp vụ:

```text
user_service    -> customers/users
product_service -> products/catalog
order_service   -> orders/order items
```

Chạy ingest để đưa dữ liệu vào Neo4j:

```bash
cd /home/dezai/Documents/code/tieu_luan_01/e-commerce-microservice
docker compose exec ai_service python ingest_to_neo4j.py
```

Script `ingest_to_neo4j.py` sẽ tạo graph:

```text
(Customer)-[:PLACED]->(Order)-[:CONTAINS]->(Product)
(Product)-[:BELONGS_TO]->(Category)
(Product)-[:MADE_BY]->(Brand)
(Document)-[:ABOUT]->(Product/Customer/Order)
```

Đồng thời tạo vector index cho các node `Document`:

```text
document_embeddings
```

Khi user hỏi, ví dụ `show me products`, pipeline là:

```text
User message
-> local MLP predict intent: product_inquiry
-> scope RAG = products
-> vector search trong Neo4j
-> lấy top documents làm context
-> Gemini/OpenAI sinh câu trả lời
```

### Chọn AI provider

`ai_service` hỗ trợ cả OpenAI và Gemini qua biến môi trường:

```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
AI_EMBEDDING_PROVIDER=gemini
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
AI_EMBEDDING_DIMENSIONS=1536
```

Khi dùng Gemini cho embedding, hãy chạy lại `ingest_to_neo4j.py` để tạo lại vector trong Neo4j cùng số chiều embedding mới.

### Lưu ý về LLaMA

Train base model LLaMA từ đầu không thực tế trong repo này.
Nếu muốn dùng LLaMA, hướng khả thi là:

- dùng base model có sẵn,
- rồi fine-tune bằng LoRA/QLoRA trên dữ liệu hội thoại và Q&A nội bộ,
- sau đó dùng nó làm lớp sinh câu trả lời trên các context lấy về từ RAG.

Hiện tại repo này chỉ scaffold phần retrieval và prompt assembly, chưa có pipeline fine-tune LLaMA hoàn chỉnh.

### Training deep learning với dataset Kaggle

`ai_service/train_models_kaggle.py` train local neural intent classifier từ dataset thật thay vì chỉ dùng vài câu hardcode.

Script hỗ trợ:

- đọc `csv`, `json`, `jsonl`
- tự dò cột text từ các tên như `text`, `sentence`, `utterance`, `query`, `message`
- tự dò cột label từ các tên như `intent`, `label`, `category`, `class`
- map nhãn phổ biến về intent nội bộ của service
- train MLP deep learning local bằng NumPy
- lưu model vào `intent_mlp_model.npz`
- lưu thêm `training_metadata.json` để `GET /api/ai/health` trả ra thông tin train

Ví dụ train bằng dataset seed có sẵn trong Docker:

```bash
cd /home/dezai/Documents/code/tieu_luan_01/e-commerce-microservice
docker compose exec ai_service python train_models_kaggle.py \
  --dataset /app/data/intent_seed_dataset.csv \
  --text-column text \
  --label-column intent

docker compose restart ai_service
```

Nếu có file Kaggle trên máy host, copy vào container trước:

```bash
docker cp /path/to/kaggle_dataset.csv ecommerce-ai-service:/app/data/kaggle_dataset.csv
```

Sau đó train:

```bash
docker compose exec ai_service python train_models_kaggle.py \
  --dataset /app/data/kaggle_dataset.csv \
  --text-column text \
  --label-column intent

docker compose restart ai_service
```

Nếu dataset Kaggle dùng tên cột khác, kiểm tra cột bằng:

```bash
docker compose exec ai_service python -c "import pandas as pd; df = pd.read_csv('/app/data/kaggle_dataset.csv'); print(df.head()); print(df.columns.tolist())"
```

Ví dụ dataset có cột `utterance` và `category`:

```bash
docker compose exec ai_service python train_models_kaggle.py \
  --dataset /app/data/kaggle_dataset.csv \
  --text-column utterance \
  --label-column category

docker compose restart ai_service
```

Kiểm tra model đã load:

```bash
curl http://localhost:8005/api/ai/health
```

Kết quả cần có:

```json
{
  "local_intent_model_configured": true,
  "local_intent_model_path": "/app/models/intent_mlp_model.npz"
}
```

Test chatbot sau khi train:

```bash
curl -X POST http://localhost:8005/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"show me products"}'
```

Kết quả mong đợi:

```json
{
  "intent": "product_inquiry",
  "sources": [
    {
      "entity_type": "intent_classifier",
      "entity_id": "local_neural_mlp"
    }
  ]
}
```

Lưu ý: nếu train bằng dataset Kaggle lớn hơn, `validation_accuracy` trong `training_metadata.json` sẽ có ý nghĩa hơn. Dataset seed mặc định nhỏ nên accuracy validation có thể dao động mạnh.
