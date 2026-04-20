# 🕌 دليل النشر

## كيفية نشر Athar

---

## 1. Production Setup

### 1.1 Docker

```bash
# Build
docker build -t athar-api .

# Run
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e QDRANT_HOST=qdrant \
  athar-api
```

---

## 2. Kubernetes

### 2.1 Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: athar-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: athar-api:latest
        ports:
        - containerPort: 8000
```

---

## 3. Monitoring

### 3.1 Prometheus

```yaml
- job_name: 'athar-api'
  static_configs:
  - targets: ['athar-api:8000']
```

---

## 4. Scaling

### 4.1 Horizontal

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: athar-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    name: athar-api
  minReplicas: 3
  maxReplicas: 10
```

---

**آخر تحديث**: أبريل 2026