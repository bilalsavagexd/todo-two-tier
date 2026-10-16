## Step#01: Initial Setup;

- 2 Pods, one for the app container and other for the db,
- 2 Services:
	- Nodeport for external access through browser,
	- ClusterIP for internal communication between pods.

## Step#02: Create Manifest files;

Create `db-pod.yaml`:

```
apiVersion: v1
kind: Pod
metadata:
  name: db
  labels:
    app: db
spec:
  containers:
    - name: postgres
      image: postgres:16
      ports:
        - containerPort: 5432
      env:
        - name: POSTGRES_DB
          value: todos
        - name: POSTGRES_USER
          value: todo_user
        - name: POSTGRES_PASSWORD
          value: todo_pass
```

Create `db-service.yaml`:

```
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  type: ClusterIP          # the default; written out so you can see it
  selector:
    app: db                # matches the pod's label
  ports:
    - port: 5432
      targetPort: 5432
```

Create `app-pod.yaml`:

```
apiVersion: v1
kind: Pod
metadata:
  name: app
  labels:
    app: app
spec:
  containers:
    - name: app
      image: <you>/todo-app:1.0
      ports:
        - containerPort: 5000
      env:
        - name: DB_HOST
          value: db
        - name: DB_NAME
          value: todos
        - name: DB_USER
          value: todo_user
        - name: DB_PASSWORD
          value: todo_pass
	- name: DB_PORT
	  value: "5432"
	
```

Create `app-service.yaml`:

```
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  type: NodePort
  selector:
    app: app
  ports:
    - port: 5000
      targetPort: 5000
      nodePort: 30080
```

## Step#03: Apply Settings

```
kubectl apply -f db-pod.yaml db-service.yaml app-pod.yaml app-service.yaml
kubectl get pods -o wide
kubectl get svc
kubectl get endpoints db            # should show the db pod's IP:5432
kubectl logs app                    # watch it connect to the db
```

Open `http://<any-node-IP>:30080`

## Step#04: Issues with this Setup

1. No persistence
2. Bare pods don't heal
3. Startup order: Postgres needs to be up and ready before the app starts to ensure proper connectivity.

## Step#05: Next Steps:

1. Replace the app Pod with a Deployment
2. Move the env values into a ConfigMap and Secret.
3. Add a PersistentVolumeClaim for the db.
4. Swap the db Pod for a StatefulSet.
