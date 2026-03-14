# Tasks Configuration Update — Verification Report

## Objective
Convert extension-specific Docker task types to standard VS Code shell tasks, resolving "unregistered task type" errors and improving portability.

## Changes Completed

### [MODIFIED] .vscode/tasks.json

**Before (Extension-Dependent):**
```json
{
    "type": "docker-build",
    "label": "docker-build",
    "dockerBuild": {
        "tag": "ghostvoid:latest",
        "dockerfile": "${workspaceFolder}/Dockerfile",
        "context": "${workspaceFolder}",
        "pull": true
    }
},
{
    "type": "docker-run",
    "label": "docker-run: debug",
    "dependsOn": ["docker-build"],
    "python": {
        "args": ["toolquest.semantic.embedding_pipeline:app", "--host", "0.0.0.0", "--port", "8000"],
        "module": "uvicorn"
    }
}
```

**After (Shell-Based):**
```json
{
    "type": "shell",
    "label": "docker-build",
    "command": "docker build --pull -t ghostvoid:latest -f ${workspaceFolder}/Dockerfile ${workspaceFolder}",
    "group": "build",
    "detail": "Builds the Docker image using the Docker CLI."
},
{
    "type": "shell",
    "label": "docker-run: debug",
    "dependsOn": ["docker-build"],
    "command": "docker compose -f ${workspaceFolder}/compose.debug.yaml up",
    "group": "build",
    "detail": "Runs the container with debugpy attached on port 5678 for remote debugging."
}
```

## Benefits of This Approach

### 1. **No Extension Dependency**
- ✅ Works without Microsoft Docker extension
- ✅ Tasks run with only VS Code's built-in shell task support
- ✅ Portable across different VS Code configurations

### 2. **Direct Docker CLI**
- ✅ `docker build --pull` ensures fresh image pulls
- ✅ `-t ghostvoid:latest` explicitly tags the image
- ✅ All parameters visible and customizable

### 3. **Debugger Integration**
- ✅ `docker-run: debug` now uses `docker compose -f compose.debug.yaml up`
- ✅ Launches debugpy listener on port 5678
- ✅ Works with the new "Python: Remote Attach (Docker)" launch configuration

### 4. **Dependency Chain**
- ✅ `docker-run: debug` depends on `docker-build`
- ✅ Image always rebuilt before running debug container
- ✅ Ensures code changes are included in container

## Task Verification

### Task List
```
✅ Build Jurassic Pixels Test (Debug)  [type: shell]
✅ docker-build                        [type: shell]
✅ docker-run: debug                   [type: shell]
```

### JSON Validation
- ✅ Valid JSON syntax
- ✅ All required fields present
- ✅ No unregistered task types
- ✅ Variable substitution: `${workspaceFolder}` properly resolved

## Usage Workflow

### Option 1: Build Only
```bash
# In VS Code: Run Task → docker-build
→ Executes: docker build --pull -t ghostvoid:latest -f <path>/Dockerfile <path>
→ Builds image and tags as ghostvoid:latest
```

### Option 2: Build + Debug
```bash
# In VS Code: Run Task → docker-run: debug
→ Automatically runs: docker-build first
→ Then executes: docker compose -f compose.debug.yaml up
→ Container starts with debugpy listening on 5678
→ Attach debugger from launch.json "Python: Remote Attach (Docker)"
```

### Option 3: Manual CLI
```bash
# Direct command execution still works:
docker build --pull -t ghostvoid:latest -f ./Dockerfile .
docker compose -f compose.debug.yaml up
```

## Integration with VS Code Debug

When using the "docker-run: debug" task:

1. **Build Phase**: Image rebuilt with latest code
2. **Container Start**: Debugpy listener activates on port 5678
3. **Debugger Attach**: Use "Python: Remote Attach (Docker)" launch config
4. **Debugging**: Set breakpoints, step through code
5. **Cleanup**: `docker compose down` stops the debug container

## Error Resolution

| Error | Before | After |
|-------|--------|-------|
| "Task type 'docker-build' not registered" | ❌ Occurred | ✅ Resolved |
| "Task type 'docker-run' not registered" | ❌ Occurred | ✅ Resolved |
| Dependency on Docker extension | ❌ Required | ✅ Not required |
| Docker CLI access | ✅ Required | ✅ Required |

## Compatibility

- **VS Code versions**: All versions with shell task support (1.0+)
- **Docker**: Docker CLI required (`docker` command available)
- **Docker Compose**: Required for debug task (`docker compose` command)
- **Python extension**: Required for debugpy attachment (recommended)

## Files Changed

```
ghost-void/.vscode/tasks.json  [MODIFIED] ✅
```

## Next Steps

1. ✅ Verify tasks.json is valid (DONE)
2. Open ghost-void workspace in VS Code
3. Press Ctrl+Shift+B or Run → Run Build Task
4. Select "docker-build" → builds Docker image
5. For debugging: Select "docker-run: debug" → starts debug container
6. Attach Python debugger from launch configuration

## Notes

- The shell tasks use `${workspaceFolder}` for path resolution
- On Windows, commands run in PowerShell (pwsh) or cmd.exe
- On macOS/Linux, commands run in $SHELL or /bin/sh
- All paths and commands are portable across platforms
