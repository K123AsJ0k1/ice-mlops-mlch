#!/bin/bash
#SBATCH --job-name=ray-cluster
#SBATCH --account=[CSC_PROJECT_2]
#SBATCH --partition=large
#SBATCH --time=00:10:00
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=10GB

module load pytorch/2.9

echo "Loaded modules:"

module list

echo "Activating venv"

source /projappl/[CSC_PROJECT_2]/tutorial-venv/bin/activate

echo "Venv active"

echo "Installed packages"

pip list

echo "Packages listed"

echo "Setting connection variables"

key_path="/users/[CSC_USERNAME]/cloud-hpc.pem"
cloud_ip="[CPOUTA_VM_RF_IP_1]"
cloud_user="[CPOUTA_VM_RF_USER_1]"
cloud_fip="[CPOUTA_VM_RF_FIP_1]"

cloud_dash_port=8125

echo "Setting Ray ports"

hpc_head_port=8050
hpc_dash_port=8265

echo "Setting Ray settings"

nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
nodes_array=($nodes)
head_node=${nodes_array[0]}
head_node_ip=$(srun --nodes=1 --ntasks=1 -w "$head_node" hostname --ip-address)

echo "Setting up Ray head"

ip_head=$head_node_ip:$hpc_head_port
export ip_head
echo "IP Head: $ip_head"

echo "Starting HEAD at $head_node"
srun --nodes=1 --ntasks=1 -w "$head_node" \
    singularity_wrapper exec ray start --head --node-ip-address="$head_node_ip" --port=$hpc_head_port \
    --dashboard-host="$head_node_ip" --dashboard-port=$hpc_dash_port \
    --num-cpus "${SLURM_CPUS_PER_TASK}" --block &

echo "Setting up SSH tunnel for head dash"

ssh -f -o StrictHostKeyChecking=no -i $key_path -N -R $cloud_ip:$cloud_dash_port:$head_node_ip:$hpc_dash_port $cloud_user@$cloud_fip

echo "Setting up Ray workers"

worker_num=$((SLURM_JOB_NUM_NODES - 1))

for ((i = 1; i <= worker_num; i++)); do
    node_i=${nodes_array[$i]}
    echo "Starting WORKER $i at $node_i"
    srun --nodes=1 --ntasks=1 -w "$node_i" \
        singularity_wrapper exec ray start --address="$ip_head" \
	    --num-cpus "${SLURM_CPUS_PER_TASK}" --block &
done

echo "Starting wait"

sleep 540
