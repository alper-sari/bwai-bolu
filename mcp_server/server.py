"""
MCP Server: GCP Compute Tools
Provides tools to create VMs and install software via SSH.
"""

import os
import subprocess
from fastmcp import FastMCP

mcp = FastMCP("gcp-compute-tools")


@mcp.tool()
def create_vm(
    project_id: str,
    instance_name: str,
    zone: str = "europe-west1-b",
    machine_type: str = "e2-micro",
) -> dict:
    """
    Creates a GCP Compute Engine VM instance with HTTP firewall tag.

    Args:
        project_id: GCP project ID
        instance_name: Name for the new VM (e.g. 'workshop-vm-1')
        zone: GCP zone (default: europe-west1-b)
        machine_type: Machine type (default: e2-micro)

    Returns:
        dict with status, instance_name, zone, and external_ip
    """
    print(f"[MCP] Creating VM: {instance_name} in {zone}...")

    create_cmd = [
        "gcloud", "compute", "instances", "create", instance_name,
        f"--project={project_id}",
        f"--zone={zone}",
        f"--machine-type={machine_type}",
        "--image-family=debian-12",
        "--image-project=debian-cloud",
        "--tags=http-server",
        "--metadata=startup-script=#! /bin/bash\napt-get update\napt-get install -y nginx\nsystemctl enable nginx\nsystemctl start nginx",
        "--async",
        "--format=get(name)",
    ]

    result = subprocess.run(create_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {
            "status": "error",
            "message": result.stderr.strip(),
        }

    # Ensure firewall rule exists
    fw_cmd = [
        "gcloud", "compute", "firewall-rules", "create", "allow-http",
        f"--project={project_id}",
        "--allow=tcp:80",
        "--target-tags=http-server",
        "--direction=INGRESS",
        "--quiet",
    ]
    subprocess.run(fw_cmd, capture_output=True, text=True)  # ignore if already exists

    return {
        "status": "provisioning",
        "instance_name": instance_name,
        "zone": zone,
        "machine_type": machine_type,
        "note": "VM creation started. Use get_vm_status to check when it's ready and get the IP.",
    }


@mcp.tool()
def get_vm_status(
    project_id: str,
    instance_name: str,
    zone: str = "europe-west1-b",
) -> dict:
    """
    Gets the current status and external IP of a VM instance.

    Args:
        project_id: GCP project ID
        instance_name: Name of the VM instance
        zone: GCP zone (default: europe-west1-b)

    Returns:
        dict with status, external_ip, and nginx_url
    """
    cmd = [
        "gcloud", "compute", "instances", "describe", instance_name,
        f"--project={project_id}",
        f"--zone={zone}",
        "--format=json(status,networkInterfaces[0].accessConfigs[0].natIP)",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {"status": "error", "message": result.stderr.strip()}

    import json
    data = json.loads(result.stdout)
    external_ip = data.get("networkInterfaces", [{}])[0].get("accessConfigs", [{}])[0].get("natIP", "unknown")

    return {
        "status": data.get("status", "UNKNOWN"),
        "instance_name": instance_name,
        "external_ip": external_ip,
        "nginx_url": f"http://{external_ip}",
    }


@mcp.tool()
def delete_vm(
    project_id: str,
    instance_name: str,
    zone: str = "europe-west1-b",
) -> dict:
    """
    Deletes a GCP Compute Engine VM instance.

    Args:
        project_id: GCP project ID
        instance_name: Name of the VM to delete
        zone: GCP zone (default: europe-west1-b)

    Returns:
        dict with status and message
    """
    print(f"[MCP] Deleting VM: {instance_name}...")

    cmd = [
        "gcloud", "compute", "instances", "delete", instance_name,
        f"--project={project_id}",
        f"--zone={zone}",
        "--quiet",
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return {
        "status": "deleting",
        "message": f"VM '{instance_name}' deletion started. Use get_vm_status to confirm it's gone.",
    }


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        port = int(os.getenv("PORT", "8080"))
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
