# JARVIS 2.0 - Docker Integration Plugin Documentation

## Overview

The Docker Integration Plugin provides comprehensive Docker container management and orchestration capabilities through Docker CLI integration. It enables JARVIS to manage containers, images, networks, volumes, and orchestrate multi-container applications.

## Features

### Container Management
- **List Containers**: View all containers (running and stopped)
- **Get Container Info**: Detailed container inspection
- **Create Containers**: Launch containers with custom configurations
- **Start/Stop/Restart**: Control container lifecycle
- **Remove Containers**: Clean up containers
- **Execute Commands**: Run commands inside containers
- **View Logs**: Access container logs
- **Monitor Stats**: Get real-time container performance metrics

### Image Management
- **List Images**: View all available images
- **Pull Images**: Download images from registries
- **Remove Images**: Clean up unused images
- **Inspect Images**: Get detailed image information

### Network & Volume Management
- **List Networks**: View Docker networks
- **List Volumes**: View Docker volumes
- **Network Inspection**: Get network details

### System Operations
- **Docker Info**: Get Docker system information
- **System Stats**: Monitor Docker resource usage

## Installation

### Requirements

```bash
# Docker must be installed and running
sudo apt-get install docker.io  # Ubuntu/Debian
# or
brew install docker  # macOS

# Verify Docker is running
docker info
```

The plugin requires:
- Docker CLI installed
- Docker daemon running
- Appropriate permissions to run Docker commands

## Usage Examples

### Container Operations

```python
from src.plugins.docker_integration import DockerIntegrationTool

tool = DockerIntegrationTool()

# List all containers (including stopped)
result = await tool.execute(action="list_containers", all=True)
print(result['containers'])

# Get specific container info
result = await tool.execute(
    action="get_container",
    container_id="my-container"
)
print(result['container'])

# Create and start a new container
result = await tool.execute(
    action="create_container",
    image="nginx:latest",
    name="my-nginx",
    ports=["8080:80"],
    env=["ENV_VAR=value"]
)
print(f"Container ID: {result['container_id']}")

# Start a stopped container
result = await tool.execute(
    action="start_container",
    container_id="my-container"
)

# Stop a running container
result = await tool.execute(
    action="stop_container",
    container_id="my-container"
)

# Remove a container
result = await tool.execute(
    action="remove_container",
    container_id="my-container",
    force=True
)
```

### Image Operations

```python
# List all images
result = await tool.execute(action="list_images")
print(result['images'])

# Pull an image from Docker Hub
result = await tool.execute(
    action="pull_image",
    image="postgres:15"
)

# Get image details
result = await tool.execute(
    action="get_image",
    image_id="nginx:latest"
)
print(result['image'])

# Remove an image
result = await tool.execute(
    action="remove_image",
    image_id="old-image:tag",
    force=True
)
```

### Container Execution & Logs

```python
# Execute command in running container
result = await tool.execute(
    action="execute_in_container",
    container_id="my-app",
    command="ls -la /app"
)
print(result['output'])

# Get container logs
result = await tool.execute(
    action="get_logs",
    container_id="my-app",
    tail=100
)
print(result['logs'])

# Get container statistics
result = await tool.execute(
    action="get_stats",
    container_id="my-app"
)
print(result['stats'])
```

### Network & Volume Operations

```python
# List networks
result = await tool.execute(action="list_networks")
print(result['networks'])

# List volumes
result = await tool.execute(action="list_volumes")
print(result['volumes'])
```

### System Information

```python
# Get Docker system info
result = await tool.execute(action="get_docker_info")
print(result['info'])
```

## API Reference

### Available Actions

| Action | Description | Required Parameters | Optional Parameters |
|--------|-------------|-------------------|-------------------|
| `list_containers` | List containers | - | `all` (bool) |
| `get_container` | Get container info | `container_id` | - |
| `create_container` | Create container | `image` | `name`, `ports`, `env` |
| `start_container` | Start container | `container_id` | - |
| `stop_container` | Stop container | `container_id` | - |
| `remove_container` | Remove container | `container_id` | `force` (bool) |
| `list_images` | List images | - | - |
| `get_image` | Get image info | `image_id` | - |
| `pull_image` | Pull image | `image` | - |
| `remove_image` | Remove image | `image_id` | `force` (bool) |
| `list_networks` | List networks | - | - |
| `list_volumes` | List volumes | - | - |
| `get_docker_info` | Get Docker info | - | - |
| `execute_in_container` | Execute command | `container_id`, `command` | - |
| `get_logs` | Get logs | `container_id` | `tail` (int) |
| `get_stats` | Get stats | `container_id` | - |

### Response Format

All actions return a dictionary with:
- `success` (bool): Whether the operation succeeded
- `error` (str, optional): Error message if failed
- Action-specific data fields

#### Success Response Example
```python
{
    "success": True,
    "container_id": "a1b2c3d4e5f6",
    "name": "my-nginx"
}
```

#### Error Response Example
```python
{
    "success": False,
    "error": "Container not found"
}
```

## CLI Integration

```bash
# List containers
JARVIS> docker list-containers

# Create and start container
JARVIS> docker create-container --image nginx:latest --name web --ports 8080:80

# View logs
JARVIS> docker get-logs --container-id web --tail 50

# Execute command
JARVIS> docker exec --container-id web --command "nginx -v"

# Get stats
JARVIS> docker get-stats --container-id web

# Pull image
JARVIS> docker pull-image --image redis:alpine

# List images
JARVIS> docker list-images

# Get Docker info
JARVIS> docker info
```

## Common Use Cases

### 1. Development Environment Setup

```python
# Pull development images
await tool.execute(action="pull_image", image="postgres:15")
await tool.execute(action="pull_image", image="redis:alpine")
await tool.execute(action="pull_image", image="node:18")

# Create database container
await tool.execute(
    action="create_container",
    image="postgres:15",
    name="dev-db",
    ports=["5432:5432"],
    env=["POSTGRES_PASSWORD=devpass"]
)

# Create Redis cache
await tool.execute(
    action="create_container",
    image="redis:alpine",
    name="dev-cache",
    ports=["6379:6379"]
)
```

### 2. Container Monitoring

```python
# List all running containers
containers = await tool.execute(action="list_containers")

# Check stats for each
for container in containers['containers'].split('\n')[1:]:
    container_id = container.split()[0]
    stats = await tool.execute(
        action="get_stats",
        container_id=container_id
    )
    print(f"Container {container_id}: {stats['stats']}")
```

### 3. Log Analysis

```python
# Get recent logs
logs = await tool.execute(
    action="get_logs",
    container_id="my-app",
    tail=1000
)

# Analyze for errors
if "ERROR" in logs['logs']:
    print("Errors found in logs!")
```

### 4. Cleanup

```python
# List all containers
containers = await tool.execute(action="list_containers", all=True)

# Remove stopped containers
for container in containers['containers'].split('\n')[1:]:
    if "Exited" in container:
        container_id = container.split()[0]
        await tool.execute(
            action="remove_container",
            container_id=container_id
        )

# Remove unused images
await tool.execute(action="remove_image", image_id="old-image", force=True)
```

## Best Practices

### 1. Container Naming
- Use descriptive names for containers
- Follow naming conventions (e.g., `app-env-service`)
- Avoid special characters

### 2. Resource Management
- Stop containers when not in use
- Remove unused containers and images regularly
- Monitor container resource usage

### 3. Security
- Don't expose sensitive ports publicly
- Use environment variables for secrets
- Keep images updated with security patches
- Use non-root users in containers when possible

### 4. Logging
- Configure appropriate log retention
- Use `tail` parameter to limit log output
- Implement log rotation for long-running containers

### 5. Error Handling
```python
result = await tool.execute(
    action="start_container",
    container_id="my-app"
)

if not result['success']:
    print(f"Failed to start container: {result.get('error')}")
    # Handle error appropriately
```

## Troubleshooting

### Common Issues

1. **"Docker daemon not running"**
   - Start Docker daemon: `sudo systemctl start docker`
   - Verify: `docker info`

2. **"Permission denied"**
   - Add user to docker group: `sudo usermod -aG docker $USER`
   - Logout and login again
   - Or use sudo with Docker commands

3. **"Container already exists"**
   - Remove existing container: `docker rm container-name`
   - Or use different name

4. **"Port already allocated"**
   - Use different host port
   - Stop container using that port
   - Check with `docker ps` and `netstat -tulpn`

5. **"Image not found"**
   - Pull image first: `docker pull image:tag`
   - Check image name spelling
   - Verify registry accessibility

## Limitations

- Requires Docker CLI installed and accessible
- Operations are asynchronous with 30-second timeout
- No direct Docker API integration (uses CLI)
- Limited to local Docker daemon (no remote Docker hosts)
- No Docker Compose orchestration in current version

## Future Enhancements

- [ ] Docker API integration (instead of CLI)
- [ ] Docker Compose support
- [ ] Container health checks
- [ ] Image building from Dockerfiles
- [ ] Volume management (create, inspect, remove)
- [ ] Network management (create, inspect, remove)
- [ ] Container resource limits
- [ ] Docker Swarm support
- [ ] Container backup and restore
- [ ] Multi-host Docker orchestration
- [ ] Registry authentication
- [ ] Image scanning for vulnerabilities

## Performance Considerations

- Container operations are async with configurable timeout
- Large log outputs may impact performance (use `tail` parameter)
- Image pulls can be slow depending on image size and network
- Stats collection is non-blocking (no-stream mode)

## Security Considerations

- Docker requires root or docker group privileges
- Be cautious with `force` parameter on remove operations
- Validate container names and IDs to prevent injection
- Don't expose Docker socket unnecessarily
- Use read-only volumes when possible
- Limit container capabilities

## Support

For issues and questions:
- Check Docker documentation
- Review JARVIS 2.0 documentation
- Check plugin test cases for usage examples
- Verify Docker daemon is running and accessible

---

**Version**: 2.6.0  
**Last Updated**: April 2026  
**Author**: JARVIS 2.0 Development Team
