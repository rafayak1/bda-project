provider "google" {
  credentials = file("../key.json")
  project     = var.project_id
  region      = var.region
}

resource "google_container_cluster" "primary" {
  name     = "my-cluster"
  location = "us-central1-a"  # Single zone (us-central1-a)
  
  initial_node_count = 1  # 1 node

  node_config {
    machine_type = "e2-small"  # Smaller machine type than e2-medium
    disk_size_gb = 50          # Set disk size to 50 GB or any desired size below your current quota
    disk_type    = "pd-standard"  # Standard disk, not SSD
    preemptible  = false
  }

  remove_default_node_pool = true  # Remove the default node pool
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "primary-node-pool"
  cluster    = google_container_cluster.primary.name
  location   = google_container_cluster.primary.location
  node_count = 1  # 1 node in the pool

  node_config {
    machine_type = "e2-small"  # Smaller machine type
    disk_size_gb = 50          # Smaller disk size
    disk_type    = "pd-standard"  # Standard persistent disk
    preemptible  = false
  }
}

output "kubeconfig" {
  value = google_container_cluster.primary.endpoint
}
