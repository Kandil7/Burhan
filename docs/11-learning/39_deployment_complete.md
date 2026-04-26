# 🕌 دليل النشر

## كيفية نشر Burhan

---

## 1. Production Setup

### 1.1 Docker

```bash
# Build
docker build -t Burhan-api .

# Run
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e QDRANT_HOST=qdrant \
  Burhan-api
```

---

## 2. Kubernetes

### 2.1 Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: Burhan-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: Burhan-api:latest
        ports:
        - containerPort: 8000
```

---

## 3. Monitoring

### 3.1 Prometheus

```yaml
- job_name: 'Burhan-api'
  static_configs:
  - targets: ['Burhan-api:8000']
```

---

## 4. Scaling

### 4.1 Horizontal

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: Burhan-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    name: Burhan-api
  minReplicas: 3
  maxReplicas: 10
```

---

**آخر تحديث**: أبريل 2026