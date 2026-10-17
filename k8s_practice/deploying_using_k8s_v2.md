In previous version the `app` Pod did not have any self-healing ability so the `app` Pod was replaced with a `Deployment`.

Create `app-deploy.yaml`:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-app-deployment
  labels:
    app: app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      enableServiceLinks: false
      containers:
        - name: todo-app-container
          image: esbilal/todo-app:1.0
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

then I understood the concept of `ConfigMap` and `Secrets` to separate configuration from application code.

Create `app-config.yaml`:

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: todo
data:
  PORT: "5432"
  DB_HOST: "db"
  DB_NAME: "todos"
  DB_USER: "todo_user"
  DB_PASS: "todo_pass"
```

apply config `kubectl apply -f apply-config.yaml`.

Then I applied setting to consume ConfigMaps in my App,

There were three primary ways to use ConfigMaps in my pods:

1. Environment Variables
2. Volume Mounts
3. Command Line Arguments

I went with the `Volume Mounting` method,

Edit `app-deploy.yaml`:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-app-deployment
  labels:
    app: app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app-pod
  template:
    metadata:
      labels:
        app: app-pod
    spec:
      enableServiceLinks: false
      containers:
        - name: todo-app-container
          image: esbilal/todo-app:1.0
          ports:
            - containerPort: 5000
          volumeMounts:
            - name: config-volume
              mountPath: /etc/config
              readOnly: true
      volumes:
      - name: config-volume
	configMap:
	  name: app-config
```


