In this doc. we are practicing deployments, configmaps + secrets, persistence, and statefulsets.

In the previous version the `app` Pod did not have any self-healing ability so the `app` Pod was replaced with a `Deployment`.

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
  DB_PORT: "5432"
  DB_HOST: "db"
  DB_NAME: "todos"
  DB_USER: "todo_user"
  DB_PASSWORD: "todo_pass"
```

apply config `kubectl apply -f apply-config.yaml`.

Then I applied settings metioned below to `consume ConfigMaps in my App`,

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

Basically what the newly added flow does is:

1. Kubernetes finds the `app-config` ConfigMap.

2. It uses that ConfigMap to populate the `config-volume` volume.

3. The container mounts config-volume at `/etc/config`.

4. The application can `read` the configuration files from that directory.

After applying the `app-deploy.yaml` file I hit my first issue and it was the I chose the wrong way:

I mounted the ConfigMap as files, not as environment variable,

basically each key became a file, which our app doesn't read,

The key needs to become an *environment variable*, which our app does read.

```
A volume is the right tool when the apps reads config *files*, which ours doesn't.
```

So we need to use method one i.e. `Environment Variables`.

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

# Load environment variables indivisually
          env:
          - name: DB_PORT
            valueFrom:
              configMapKeyRef:
                name: app-config
                name: app-config
                key: DB_PORT

          - name: DB_HOST
            valueFrom:
              configMapKeyRef:
                name: app-config
                key: DB_HOST

          - name: DB_NAME
            valueFrom:
              configMapKeyRef:
                name: app-config
                key: DB_NAME

          - name: DB_USER
            valueFrom:
              configMapKeyRef:
                name: app-config
                key: DB_USER

          - name: DB_PASSWORD
            valueFrom:
              configMapKeyRef:
                name: app-config
                key: DB_PASSWORD

# Or load all ConfigMap keys as environment variables          >
#         envFrom:
#         - configMapRef:
#             name: app-config
```

It worked sucessfully so I proceeded to create the `secret.yaml` file:

```
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: todo
type: Opaque #Generic secrets for arbitrary user data (default)
stringData: #instead of normal Data so is auto-encodes the data
  DB_USER: todo_user
  DB_PASSWORD: todo_pass
```

apply it.

Now I have to edit `app-deploy.yaml` so that it can consume it,

Edit `app-deploy.yaml`:

```
# Changes made:

          - name: DB_USER
            valueFrom:
              secretKeyRef:
                name: app-secrets
                key: DB_USER

          - name: DB_PASSWORD
            valueFrom:
              secretKeyRef:
                name: app-secrets
                key: DB_PASSWORD

# Or load all Secret keys as environment variables
#         envFrom:
#         - secretRef:
#             name: app-secrets
```

Other types of secrets are:

1. kubernetes.io/dockerconfigjson: Docker registry credentials
2. kubernetes.io/tls: TLS certificates and keys
3. kubernetes.io/service-account-token: Service account tokens

## One behaviour to know

Environment variables are read once, when the container starts. If you edit the ConfigMap later, running pods won’t see the change. Restart them with:

```
kubectl rollout restart deploy/todo-app-deployment
```

Volume-mounted ConfigMaps do update live, after a short delay.

```
Also whatever we did regarding configMaps and secrets, we have to do it for the db-pod.yaml as well.
```

## Next steps

1. Adding a persistent storage
2. Implementing Statefulsets
