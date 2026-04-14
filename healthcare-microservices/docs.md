# Healthcare Microservices

Du an nay mo phong mot use case dat lich kham benh don gian theo kien truc microservices.
He thong duoc dong goi bang Docker, cac backend viet bang Django REST Framework, du lieu dung chung
mot PostgreSQL tap trung, va nguoi dung truy cap qua mot API gateway co frontend tich hop.

## Muc tieu du an

He thong giai quyet flow co ban:
- Tao benh nhan
- Tao bac si
- Kiem tra su ton tai cua benh nhan va bac si
- Dat lich kham
- Chong dat trung lich cung doctor va cung thoi diem
- Hien thi danh sach lich hen tren giao dien web

## Kien truc tong quan

Du an gom 5 thanh phan chay trong Docker:

1. `gateway`
- La diem vao duy nhat cua he thong
- Dung `nginx`
- Vua phuc vu frontend tinh, vua reverse proxy request API ve cac service ben duoi
- Cong public: `http://localhost:8080`

2. `patient-service`
- Django service quan ly benh nhan
- Cung cap API tao benh nhan va xem danh sach/chi tiet benh nhan
- Chi chay trong Docker network, khong mo cong ra host

3. `doctor-service`
- Django service quan ly bac si
- Cung cap API tao bac si, xem danh sach/chi tiet, va endpoint availability don gian
- Chi chay trong Docker network, khong mo cong ra host

4. `appointment-service`
- Django service xu ly dat lich
- Goi HTTP den `patient-service` va `doctor-service` de validate du lieu
- Luu appointment vao PostgreSQL
- Chi chay trong Docker network, khong mo cong ra host

5. `postgres`
- PostgreSQL tap trung dung chung cho ca 3 backend service
- Chi chay trong Docker network, khong publish cong ra host

## Cau truc thu muc

```text
healthcare-microservices/
├── appointment-service/
├── doctor-service/
├── patient-service/
├── gateway/
│   ├── frontend/
│   └── nginx.conf
├── docker-compose.yaml
└── docs.md
```

## Giai thich tung thanh phan

### 1. Gateway

Thu muc:
- [gateway/Dockerfile](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/gateway/Dockerfile:1)
- [gateway/nginx.conf](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/gateway/nginx.conf:1)
- [gateway/frontend/index.html](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/gateway/frontend/index.html:1)
- [gateway/frontend/styles.css](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/gateway/frontend/styles.css:1)
- [gateway/frontend/app.js](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/gateway/frontend/app.js:1)

Vai tro:
- Phuc vu giao dien web
- Dinh tuyen request API:
  - `/api/patients/` -> `patient-service`
  - `/api/doctors/` -> `doctor-service`
  - `/api/appointments/` -> `appointment-service`

Y nghia:
- Frontend khong can biet tung service rieng le
- Trien khai thuc te se de mo rong hon vi chi co 1 diem vao

### 2. Patient Service

Thu muc goc:
- [patient-service/app/manage.py](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/patient-service/app/manage.py:1)
- [patient-service/app/config/settings.py](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/patient-service/app/config/settings.py:1)

Chuc nang:
- Tao patient moi
- Lay danh sach patient
- Lay chi tiet patient theo `uuid`

Bang du lieu:
- `patients`

Du lieu chinh:
- `id`
- `full_name`
- `phone`
- `created_at`

### 3. Doctor Service

Thu muc goc:
- [doctor-service/app/manage.py](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/doctor-service/app/manage.py:1)
- [doctor-service/app/config/settings.py](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/doctor-service/app/config/settings.py:1)

Chuc nang:
- Tao doctor moi
- Lay danh sach doctor
- Lay chi tiet doctor theo `uuid`
- Kiem tra availability don gian qua endpoint:
  - `/doctors/<uuid>/availability/`

Bang du lieu:
- `doctors`

Du lieu chinh:
- `id`
- `full_name`
- `specialty`
- `created_at`

### 4. Appointment Service

Thu muc goc:
- [appointment-service/app/manage.py](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/appointment-service/app/manage.py:1)
- [appointment-service/app/config/settings.py](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/appointment-service/app/config/settings.py:1)
- [appointment-service/app/appointment/application/use_cases.py](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/appointment-service/app/appointment/application/use_cases.py:1)

Chuc nang:
- Tao lich hen
- Lay danh sach appointment
- Lay chi tiet appointment

Business rules hien tai:
- `appointment_time` phai o tuong lai
- Patient phai ton tai
- Doctor phai ton tai
- Doctor phai available
- Khong duoc dat 2 appointment cung `doctor_id` va `appointment_time`

Bang du lieu:
- `appointments`

Du lieu chinh:
- `id`
- `patient_id`
- `doctor_id`
- `appointment_time`
- `status`
- `created_at`

### 5. PostgreSQL tap trung

Trong file [docker-compose.yaml](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/docker-compose.yaml:1), ca 3 backend cung dung:
- `DB_HOST=postgres`
- `DB_NAME=healthcare_db`
- `DB_USER=healthcare_user`
- `DB_PASSWORD=healthcare_pass`

Luu y:
- Day la mot DB tap trung, nhung moi service quan ly bang rieng cua no
- Khong co foreign key xuyen service
- Quan he giua cac service duoc kiem tra qua HTTP thay vi ORM join truc tiep

## Luong request trong he thong

Flow dat lich:

1. Nguoi dung mo `http://localhost:8080`
2. Frontend goi `POST /api/patients/` de tao benh nhan
3. Frontend goi `POST /api/doctors/` de tao bac si
4. Frontend goi `POST /api/appointments/` qua gateway
5. Gateway chuyen request toi `appointment-service`
6. `appointment-service` goi sang:
- `patient-service` de kiem tra patient co ton tai khong
- `doctor-service` de kiem tra doctor co ton tai va co available khong
7. Neu hop le, `appointment-service` luu du lieu vao PostgreSQL
8. Frontend refresh danh sach appointment va hien ket qua

## Huong dan chay du an

Yeu cau:
- Da cai Docker
- Da cai Docker Compose

### Cach 1: chay toan bo he thong

Trong thu muc du an:

```bash
cd /home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices
docker compose up --build
```

Neu muon chay nen:

```bash
docker compose up -d --build
```

Sau khi chay xong:
- Mo UI tai `http://localhost:8080`

### Dung he thong

```bash
docker compose down
```

Neu muon xoa ca volume DB:

```bash
docker compose down -v
```

## Cach su dung tren UI

Trang web co 3 khu vuc chinh:

1. Tao benh nhan
- Nhap ho ten va so dien thoai
- Bam `Tao patient`

2. Tao bac si
- Nhap ho ten va chuyen khoa
- Bam `Tao doctor`

3. Dat lich kham
- Chon patient
- Chon doctor
- Chon thoi gian
- Bam `Book appointment`

Man hinh se hien:
- Danh sach patient
- Danh sach doctor
- Danh sach appointment
- Log hoat dong va loi

## API hien co

Tat ca API public deu di qua gateway `http://localhost:8080`.

### Patient APIs

- `GET /api/patients/`
- `POST /api/patients/`
- `GET /api/patients/<uuid>/`

Payload tao patient:

```json
{
  "full_name": "Nguyen Van A",
  "phone": "0901234567"
}
```

### Doctor APIs

- `GET /api/doctors/`
- `POST /api/doctors/`
- `GET /api/doctors/<uuid>/`
- `GET /api/doctors/<uuid>/availability/?appointment_time=2026-04-22T08:30:00Z`

Payload tao doctor:

```json
{
  "full_name": "Tran Thi B",
  "specialty": "Cardiology"
}
```

### Appointment APIs

- `GET /api/appointments/`
- `POST /api/appointments/`
- `GET /api/appointments/<uuid>/`

Payload tao appointment:

```json
{
  "patient_id": "patient-uuid",
  "doctor_id": "doctor-uuid",
  "appointment_time": "2026-04-22T08:30:00Z"
}
```

## Test nhanh bang curl

### 1. Tao patient

```bash
curl -X POST http://localhost:8080/api/patients/ \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Nguyen Van A","phone":"0901234567"}'
```

### 2. Tao doctor

```bash
curl -X POST http://localhost:8080/api/doctors/ \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Tran Thi B","specialty":"Cardiology"}'
```

### 3. Dat lich

```bash
curl -X POST http://localhost:8080/api/appointments/ \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"<patient_uuid>","doctor_id":"<doctor_uuid>","appointment_time":"2026-04-22T08:30:00Z"}'
```

### 4. Xem danh sach appointment

```bash
curl http://localhost:8080/api/appointments/
```

## Cac file cau hinh quan trong

- [docker-compose.yaml](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/docker-compose.yaml:1)
  Ghep toan bo he thong lai thanh cac service Docker.

- [gateway/nginx.conf](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/gateway/nginx.conf:1)
  Cau hinh reverse proxy va static frontend.

- [patient-service/entrypoint.sh](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/patient-service/entrypoint.sh:1)
- [doctor-service/entrypoint.sh](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/doctor-service/entrypoint.sh:1)
- [appointment-service/entrypoint.sh](/home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices/appointment-service/entrypoint.sh:1)
  Moi service se tu `migrate` truoc khi chay `runserver`.

## Gioi han hien tai

- Chua co authentication va phan quyen
- Availability cua doctor moi o muc don gian
- Chua co API docs tu dong nhu Swagger
- Chua co test suite day du
- Chua co queue/event bus giua cac service

## Huong mo rong tiep theo

- Them `Swagger/OpenAPI`
- Them `pytest` hoac Django tests
- Them authentication cho le tan/admin
- Them lich lam viec thuc su cho doctor
- Them cancel/reschedule appointment
