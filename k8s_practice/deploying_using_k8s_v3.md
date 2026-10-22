I couldn't continue in the previous doc. as it was getting complicated.

In this doc. we implement a `persistent storage`, because currently the db pod keeps its data inside the container, so deleting the pod loses every task.

We will also be using `StatefulSet` here instead of a bare Pod, so K8s recreates the pod automatically and creates the PVC for me.

Implementing persistent storage with Rook + Ceph first,

Current VMware setup:

k8s-master, k8s-worker1, k8s-worker2: 
- memory: 5GB # free -h
- VCPUs: 2 # nproc
- Disks: 25GB OS + 20GB raw # lsblk -f, sda with parts., plus sdb with no parts.

Prepare every node:

```
sudo apt-get update && sudo apt-get install -y lvm2
sudo modprobe rbd
echo rbd | sudo tee /etc/modules-load.d/rbd.conf
timedatectl | grep -i synchronized      # should say: System clock synchronized: yes
```
Prep. the cluster, check all nodes are ready:

```
kubectl get nodes -o wide
```
Normally, the master has a sign saying:
"Control-plane machine. Ordinary workloads stay away!"

The command:
```
kubectl taint nodes k8s-master node-role.kubernetes.io/control-plane:NoSchedule-
```
removes that restriction.

Now Kubernetes may schedule ordinary workloads, such as database or Ceph Pods, on the master too, subject to their other scheduling requirements.

Why do this? You have only three small VMs, so you may need to use all three for storage and workloads.

This does not turn the master into a worker node in every respect; it simply removes this particular scheduling restriction.

Install the Rook operator:

```
git clone --single-branch --branch v1.19.7 https://github.com/rook/rook.git
cd rook/deploy/examples
kubectl create -f crds.yaml -f common.yaml -f operator.yaml
kubectl -n rook-ceph get pod -w
```

Before you create a the ceph cluster, edit `cluster.yaml` and set a single manager to save memory on the 5GB nodes.

Create the cluster:

```
kubectl create -f cluster.yaml
kubectl -n rook-ceph get pod -w 
```

Checkpoint, in about this order:

1. rook-ceph-mon-a, -b, -c appear and become Running
2. rook-ceph-mgr-a Running
3. rook-ceph-osd-prepare-<node> jobs reach Completed (3 of them)
4. rook-ceph-osd-0, -1, -2 Running
5. CSI pods (rook-ceph.rbd.csi.ceph.com-ctrlplugin, -nodeplugin) Running

Verify with the toolbox:

```
kubectl create -f toolbox.yaml
kubectl -n rook-ceph rollout status deploy/rook-ceph-tools
kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph status
kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph osd tree
```

You want `HEALTH_OK`, `3 daemons, quorum a,b,c` under mon, and `3 osds: 3 up, 3 in`. `ceph osd tree` should show one OSD under each host.

Lower the OSD memory target to suit your VMs:

```
kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- \
  ceph config set osd osd_memory_target 2147483648
```

Create the `Pool` and `StorageClass`:

```
cd ~/rook/deploy/examples
kubectl create -f csi/rbd/storageclass.yaml
kubectl get storageclass
kubectl -n rook-ceph get cephblockpool
```

Remove the default flag from the local-path:

```
kubectl patch storageclass local-path \
  -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

Move the database to Ceph storage:

First I'll create a statefulset for the db.

removing the old pod:

```
kubectl -n todo delete pod db
```

Create `db-statefulset.yaml`:

```
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 1
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      enableServiceLinks: false
      containers:
        - name: postgres
          image: postgres:16
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: db-storage
              mountPath: /var/lib/postgresql/data
          env:
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_NAME
            - name: POSTGRES_USER
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: DB_PASSWORD
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata

  volumeClaimTemplates:
    - metadata:
        name: db-storage
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: rook-ceph-block
        resources:
          requests:
            storage: 1Gi
```

```
kubectl apply -f db-statefulset.yaml -n todo --dry-run=server     # validate first
kubectl apply -f db-statefulset.yaml -n todo
kubectl -n todo get pods,pvc,pv
```

Restart the app pod so they reconnect ot the fresh database:

```
kubectl -n todo rollout restart deploy/todo-app-deployment
kubectl -n todo logs deploy/todo-app-deployment
```

