# Model Context Protocol (MCP) Architecture Proof of Concept

This project demonstrates a microservices architecture using the Model Context Protocol (MCP) for AI communication with a central registry. The architecture separates MCP servers from API servers (REST and GraphQL) to provide better separation of concerns.

## Architecture Overview

![MCP Architecture](https://mermaid.ink/img/pako:eNqFkk1PwzAMhv9KlBMgdYceuExs4sQFcUHiEDVeG9TmQ0lQJ6H-d9KuXdkHcLOd5_XrxPYJCq0QMrDWNLrVJLrGWIOdJvHJkfhQa0eiJGe1Ib9XpDqyJMrWGCR_VB2JTpPoW-3QkCgcGdKFI9FbVZMoHJUkKtRIYjDakOhb1ZEo0VoSG9QOxUqhJVGiVY5EZ3RNYjDWkCgdVSSGVjsSpdEdibVCEoXVhkTfqI7EGrUjsVLYkSjRKBJFq1sSa4UdiZVCS6JEqxyJzuiaxGCsIVE6qkgMrXYkSqM7EmvVPxPFYLQhUTqqSAytdiRKozsS5Qs-QIZXaKDEHDLYoWrxgbmCDDaoFJZQYA4ZbNE0-MRcQQYlKoUFFJhDBjvVNj4xV5DBFpXCAgrMIYNKtY1PzBVkUKJSWECBOWRQqbbxibmCDLaoFBZQYA4Z7FTb-MRcQQZbVAoLKPAMGVSqbXxiruAXZvgFhQ?type=png)

### Components

1. **Central Registry Service**
   - Manages registration of all services
   - Provides service discovery
   - Tracks service status

2. **MCP Server 1**
   - Implements MCP protocol
   - Communicates with other MCP servers
   - Connects to REST API server

3. **MCP Server 2**
   - Implements MCP protocol
   - Communicates with other MCP servers
   - Connects to GraphQL API server

4. **REST API Server**
   - Provides REST endpoints
   - Serves data to MCP Server 1
   - Can be accessed directly by clients

5. **GraphQL API Server**
   - Provides GraphQL API
   - Serves data to MCP Server 2
   - Can be accessed directly by clients

6. **MCP Client**
   - Demonstration client
   - Can connect to MCP servers via registry
   - Can access API servers directly

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Running the Services

1. Clone the repository:
   ```
   git clone <repository-url>
   cd MCPPoc
   ```

2. Start all services using Docker Compose:
   ```
   docker-compose up --build
   ```

3. Access the services:
   - Registry Service: http://localhost:8000
   - REST API Server: http://localhost:8001
   - GraphQL API Server: http://localhost:8002
   - MCP Server 1 (REST): http://localhost:8003
   - MCP Server 2 (GraphQL): http://localhost:8004
   - MCP Client: http://localhost:8005

## API Documentation

### Registry Service

- `POST /registry/services` - Register a new service
- `DELETE /registry/services/{service_id}` - Deregister a service
- `GET /registry/services` - List all registered services
- `GET /registry/services/{service_id}` - Get service details
- `PUT /registry/services/{service_id}/status` - Update service status

### REST API Server

- `POST /api/generate` - Generate text
- `GET /api/status` - Get server status

### GraphQL API Server

- GraphQL endpoint: `/graphql`
- Queries:
  - `generateText(prompt: String!, maxTokens: Int): GenerateResponse`
  - `getStatus: ServerStatus`

### MCP Servers

- `POST /mcp/message` - MCP protocol endpoint
- `POST /mcp/generate` - Generate text
- `GET /mcp/status` - Get server status

## MCP Protocol

The MCP protocol is implemented as a JSON-based message format:

```json
{
  "message_id": "unique-message-id",
  "source_id": "source-server-id",
  "target_id": "target-server-id",
  "content": {
    "action": "generate_text",
    "prompt": "Sample prompt",
    "max_tokens": 100
  },
  "timestamp": "2023-04-06T12:00:00Z"
}
```

## Architecture Benefits

1. **Separation of Concerns**
   - MCP servers focus on protocol implementation
   - API servers focus on their specific API interfaces

2. **Flexibility**
   - Clients can access API servers directly
   - MCP servers can communicate with each other

3. **Scalability**
   - Each component can be scaled independently
   - New API servers can be added without changing MCP protocol

4. **Maintainability**
   - Clear boundaries between components
   - Each component has a single responsibility

## License

This project is licensed under the MIT License - see the LICENSE file for details.
