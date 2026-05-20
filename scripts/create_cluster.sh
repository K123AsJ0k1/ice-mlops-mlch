#!/bin/bash

set -eoa pipefail

#######################################################################################
# Create and configure a cluster with Kind
#
# Usage: $ export HOST_IP=127.0.0.1; export CLUSTER_NAME="mlops-platform"; ./create_cluster.sh
#######################################################################################


if [ "$INSTALL_LOCAL_REGISTRY" = "true" ]; then
# create a cluster with the local registry enabled in containerd
cat <<EOF | kind create cluster --name $CLUSTER_NAME --image=kindest/node:v1.24.0 --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  ipFamily: dual
  apiServerAddress: ${HOST_IP}
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 31001
    hostPort: 7001
    protocol: TCP
  - containerPort: 31002
    hostPort: 7002
    protocol: TCP
  - containerPort: 31003
    hostPort: 7003
    protocol: TCP
  - containerPort: 31004
    hostPort: 7004
    protocol: TCP
  - containerPort: 31005
    hostPort: 7005
    protocol: TCP
  - containerPort: 31006
    hostPort: 7006
    protocol: TCP
  - containerPort: 31007
    hostPort: 7007
    protocol: TCP
  - containerPort: 31008
    hostPort: 7008
    protocol: TCP
  - containerPort: 31009
    hostPort: 7009
    protocol: TCP
  - containerPort: 31010
    hostPort: 7010
    protocol: TCP
  - containerPort: 31011
    hostPort: 7011
    protocol: TCP
  - containerPort: 31012
    hostPort: 7012
    protocol: TCP
  - containerPort: 31013
    hostPort: 7013
    protocol: TCP
  - containerPort: 31014
    hostPort: 7014
    protocol: TCP
  - containerPort: 31015
    hostPort: 7015
    protocol: TCP
  - containerPort: 31016
    hostPort: 7016
    protocol: TCP
  - containerPort: 31017
    hostPort: 7017
    protocol: TCP
  - containerPort: 31018
    hostPort: 7018
    protocol: TCP
  - containerPort: 31019
    hostPort: 7019
    protocol: TCP
  - containerPort: 31020
    hostPort: 7020
    protocol: TCP
  - containerPort: 31501
    hostPort: 7501
    protocol: TCP
  - containerPort: 31502
    hostPort: 7502
    protocol: TCP
  - containerPort: 31503
    hostPort: 7503
    protocol: TCP
  - containerPort: 31504
    hostPort: 7504
    protocol: TCP
  - containerPort: 31505
    hostPort: 7505
    protocol: TCP
  - containerPort: 31506
    hostPort: 7506
    protocol: TCP
  - containerPort: 31507
    hostPort: 7507
    protocol: TCP
  - containerPort: 31508
    hostPort: 7508
    protocol: TCP
  - containerPort: 31509
    hostPort: 7509
    protocol: TCP
  - containerPort: 31510
    hostPort: 7510
    protocol: TCP
  - containerPort: 31511
    hostPort: 7511
    protocol: TCP
  - containerPort: 31512
    hostPort: 7512
    protocol: TCP
  - containerPort: 31513
    hostPort: 7513
    protocol: TCP
  - containerPort: 31514
    hostPort: 7514
    protocol: TCP
  - containerPort: 31515
    hostPort: 7515
    protocol: TCP
  - containerPort: 31516
    hostPort: 7516
    protocol: TCP
  - containerPort: 31517
    hostPort: 7517
    protocol: TCP
  - containerPort: 31518
    hostPort: 7518
    protocol: TCP
  - containerPort: 31519
    hostPort: 7519
    protocol: TCP
  - containerPort: 31520
    hostPort: 7520
    protocol: TCP
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."${HOST_IP}:5001"]
    endpoint = ["http://kind-registry:5000"]
EOF

else
# create a cluster
cat <<EOF | kind create cluster --name $CLUSTER_NAME --image=kindest/node:v1.24.0 --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  ipFamily: dual
  apiServerAddress: ${HOST_IP}
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 31001
    hostPort: 7001
    protocol: TCP
  - containerPort: 31002
    hostPort: 7002
    protocol: TCP
  - containerPort: 31003
    hostPort: 7003
    protocol: TCP
  - containerPort: 31004
    hostPort: 7004
    protocol: TCP
  - containerPort: 31005
    hostPort: 7005
    protocol: TCP
  - containerPort: 31006
    hostPort: 7006
    protocol: TCP
  - containerPort: 31007
    hostPort: 7007
    protocol: TCP
  - containerPort: 31008
    hostPort: 7008
    protocol: TCP
  - containerPort: 31009
    hostPort: 7009
    protocol: TCP
  - containerPort: 31010
    hostPort: 7010
    protocol: TCP
  - containerPort: 31011
    hostPort: 7011
    protocol: TCP
  - containerPort: 31012
    hostPort: 7012
    protocol: TCP
  - containerPort: 31013
    hostPort: 7013
    protocol: TCP
  - containerPort: 31014
    hostPort: 7014
    protocol: TCP
  - containerPort: 31015
    hostPort: 7015
    protocol: TCP
  - containerPort: 31016
    hostPort: 7016
    protocol: TCP
  - containerPort: 31017
    hostPort: 7017
    protocol: TCP
  - containerPort: 31018
    hostPort: 7018
    protocol: TCP
  - containerPort: 31019
    hostPort: 7019
    protocol: TCP
  - containerPort: 31020
    hostPort: 7020
    protocol: TCP
  - containerPort: 31501
    hostPort: 7501
    protocol: TCP
  - containerPort: 31502
    hostPort: 7502
    protocol: TCP
  - containerPort: 31503
    hostPort: 7503
    protocol: TCP
  - containerPort: 31504
    hostPort: 7504
    protocol: TCP
  - containerPort: 31505
    hostPort: 7505
    protocol: TCP
  - containerPort: 31506
    hostPort: 7506
    protocol: TCP
  - containerPort: 31507
    hostPort: 7507
    protocol: TCP
  - containerPort: 31508
    hostPort: 7508
    protocol: TCP
  - containerPort: 31509
    hostPort: 7509
    protocol: TCP
  - containerPort: 31510
    hostPort: 7510
    protocol: TCP
  - containerPort: 31511
    hostPort: 7511
    protocol: TCP
  - containerPort: 31512
    hostPort: 7512
    protocol: TCP
  - containerPort: 31513
    hostPort: 7513
    protocol: TCP
  - containerPort: 31514
    hostPort: 7514
    protocol: TCP
  - containerPort: 31515
    hostPort: 7515
    protocol: TCP
  - containerPort: 31516
    hostPort: 7516
    protocol: TCP
  - containerPort: 31517
    hostPort: 7517
    protocol: TCP
  - containerPort: 31518
    hostPort: 7518
    protocol: TCP
  - containerPort: 31519
    hostPort: 7519
    protocol: TCP
  - containerPort: 31520
    hostPort: 7520
    protocol: TCP
EOF

fi


# see https://github.com/kubernetes-sigs/kind/issues/2586
CONTAINER_ID=$(docker ps -aqf "name=$CLUSTER_NAME-control-plane")
docker exec -t ${CONTAINER_ID} bash -c "echo 'fs.inotify.max_user_watches=1048576' >> /etc/sysctl.conf"
docker exec -t ${CONTAINER_ID} bash -c "echo 'fs.inotify.max_user_instances=512' >> /etc/sysctl.conf"
docker exec -i ${CONTAINER_ID} bash -c "sysctl -p /etc/sysctl.conf"


exit 0