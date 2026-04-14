# Healthcare Microservices - Installation Guide

Du an nay chay theo mo hinh Docker Compose. Cach cai dat on dinh nhat la chay toan bo stack tu thu muc `healthcare-microservices`.

## Yeu cau

- Docker 24+.
- Docker Compose v2.

## Cau truc chay

- `gateway`: diem vao duy nhat cua he thong, phuc vu frontend va proxy API.
- `patient-service`: quan ly benh nhan.
- `doctor-service`: quan ly bac si.
- `appointment-service`: dat lich va validate nghiep vu.
- `postgres`: co so du lieu chung cho 3 backend service.

## Cai dat va chay

1. Mo terminal tai thu muc goc repo.
2. Chuyen vao du an healthcare.

```bash
cd /home/dezai/Documents/code/AI/tieu-luan-que/healthcare-microservices
```

3. Build va khoi dong toan bo he thong.

```bash
docker compose up --build
```

4. Neu muon chay nen.

```bash
docker compose up -d --build
```

5. Mo trinh duyet va truy cap UI.

```text
http://localhost:8080
```

## Cau hinh mac dinh

- PostgreSQL:
  - database: `healthcare_db`
  - user: `healthcare_user`
  - password: `healthcare_pass`
- Gateway public port: `8080`

## Dung he thong

```bash
docker compose down
```

Neu muon xoa luon du lieu database:

```bash
docker compose down -v
```

## Ghi chu

- Backend service khong mo cong ra host; chi gateway duoc publish.
- Tat ca lien ket giua service duoc resolve trong Docker network qua ten service.
- Neu thay doi source code, chi can chay lai `docker compose up --build`.

