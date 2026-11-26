# Ovision AI API — Visão Computacional & Biometria Animal

API REST desenvolvida com **Django**, **Django REST Framework** e **JWT (`djangorestframework-simplejwt`)** para estimativa autônoma de pose (17 keypoints AP-10K com **YOLO Pose**) e biometria corporal de caprinos (com arquitetura pronta para expansão multi-espécies, rebanhos e animais na Fase 2).

Os scripts CLI originais (`main.py`, `evaluate.py`, `estimate_distance.py` e `trainAP10k.py`) continuam funcionais e compartilham o mesmo núcleo de inferência em [`inferences/services/pipeline.py`](inferences/services/pipeline.py).

---

## Estrutura e Arquitetura (Fase 1 vs. Fase 2)

* **Fase 1 (implementada agora):**
  * Autenticação JWT por fazenda (`Farm` como conta autenticável via e-mail e senha).
  * Upload de imagem (`multipart/form-data`) com inferência YOLO Pose, geração e armazenamento local da imagem anotada (`MEDIA_ROOT` / `MEDIA_URL`) e persistência de `InferenceRecord` + `BiometricMeasurement` (1:1).
  * Listagem e consulta individual das inferências da fazenda autenticada com medidas biométricas e `image_url`.
* **Fase 2 (modelos já preparados no DER):**
  * `Herd` e `Animal` já modelados em `farms/models.py` (mantidos opcionais/nulos nesta etapa para evoluir sem quebra de schema).

---

## Instalação e Execução Local

1. Acesse a pasta do projeto e ative o ambiente virtual:
```powershell
cd C:\Users\PC-KIRO\Documents\Projetos\ovision-ai-api
.\.venv\Scripts\Activate.ps1
```

2. Instale as dependências (caso ainda não tenha instalado):
```powershell
pip install -r requirements.txt
```

3. Aplique as migrações e crie a fazenda de demonstração:
```powershell
python manage.py migrate
python manage.py seed_farm
```
Credenciais padrão criadas pelo `seed_farm`:
* **E-mail:** `demo@ovision.local`
* **Senha:** `ovision123`

4. Suba o servidor de desenvolvimento:
```powershell
python manage.py runserver 127.0.0.1:8000
```

---

## Endpoints da API (Fase 1)

### 1. Cadastro e Autenticação JWT

* **Registrar nova fazenda (opcional):** `POST /api/v1/auth/register/`
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fazenda Serra Verde",
    "owner_name": "Produtor Rural",
    "email": "contato@serraverde.local",
    "password": "MinhaSenhaSegura123",
    "species_focus": "caprinos"
  }'
```

* **Login (obter `access` e `refresh` token):** `POST /api/v1/auth/token/`
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@ovision.local", "password": "ovision123"}'
```

* **Renovar token (`refresh`):** `POST /api/v1/auth/token/refresh/`
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<REFRESH_TOKEN>"}'
```

* **Dados da fazenda autenticada:** `GET /api/v1/auth/me/`

---

### 2. Inferência por Upload de Imagem

`POST /api/v1/inferences/` (`multipart/form-data`, requer header `Authorization: Bearer <ACCESS_TOKEN>`)

Campos aceitos:
* `image` ou `file`: arquivo da imagem (`.jpg`, `.png`, etc.)
* `distance_cm` *(opcional)*: distância da câmera em cm (se omitida, tenta deduzir do padrão `dist(\d+)` no nome do arquivo ou assume `160.0` cm)
* `conf_threshold` *(opcional, padrão `0.25`)*
* `imgsz` *(opcional, padrão `1280`, múltiplo de 32)*

```bash
curl -X POST http://127.0.0.1:8000/api/v1/inferences/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "image=@inputs/010-dist160-v3.jpg" \
  -F "distance_cm=160"
```

Exemplo de resposta (`201 Created`):
```json
{
  "id": "b6d0d5a4-...",
  "farm_id": "2c8d1f3a-...",
  "animal_id": null,
  "original_filename": "010-dist160-v3.jpg",
  "image_url": "http://127.0.0.1:8000/media/inferences/<farm_id>/pose_010-dist160-v3_strict-clean_ab12cd34.jpg",
  "distance_cm": 160.0,
  "model_tag": "caprine-bovidae-v4-strict-clean (strict-clean)",
  "conf_threshold": 0.25,
  "imgsz": 1280,
  "created_at": "2026-11-25T22:15:00-03:00",
  "measurement": {
    "id": "9f3b...",
    "peso_kg": 44.12,
    "altura_cernelha": 73.5,
    "altura_garupa": 74.8,
    "comprimento": 71.2,
    "circ_torax": 93.71,
    "grossura_pescoco": 19.4,
    "raw_keypoints": [...]
  }
}
```

---

### 3. Listagem e Detalhe das Imagens Inferidas

* **Listar inferências da fazenda autenticada:** `GET /api/v1/inferences/`
```bash
curl -X GET http://127.0.0.1:8000/api/v1/inferences/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

* **Detalhar uma inferência específica:** `GET /api/v1/inferences/<uuid>/`

* **Visualizar a imagem anotada gerada:** acesse diretamente a URL retornada em `image_url` (ex.: `http://127.0.0.1:8000/media/inferences/...jpg`).

---

## Scripts CLI (Compatibilidade Preservada)

```powershell
# Inferência individual
python main.py --image inputs/010-dist160-v3.jpg --test-gt dados_biometria.json

# Avaliação em lote
python evaluate.py --inputs-dir inputs/

# Auditoria/estimativa de distância
python estimate_distance.py --inputs-dir inputs/
```

---

## Testes Automatizados

```powershell
python manage.py test -v 2
```
