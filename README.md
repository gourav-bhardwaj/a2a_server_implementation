# A2A Server Implementation

## 🚀 Overview

The **A2A Server Implementation** is a modular backend framework designed to coordinate and bridge multi-agent ecosystems using modern communication protocols. Built on top of Python, it integrates **Model Context Protocol (MCP)** servers (`department_mcp_server.py`, `employee_mcp_server.py`, `notification_mcp_server.py`) with agentic communication interfaces (`a2a_client.py`, `agents_api.py`, `webhook.py`) to streamline secure interoperability between decentralized services and AI agents.

---

## 📂 Project Architecture & File Structure

```text
a2a_server_implementation/
├── a2a_client.py               # Client interface for agent-to-agent communication
├── a2a_server_config.py        # Central configuration settings for server and routing
├── agents_api.py               # Core API endpoints handling agent interactions
├── demo.py                     # Demonstration scripts and end-to-end usage examples
├── department_mcp_server.py    # MCP server managing department-specific context/tools
├── employee_mcp_server.py      # MCP server managing employee records/database context
├── notification_mcp_server.py  # MCP server handling notification services and messaging
├── webhook.py                  # Webhook handlers for external asynchronous event triggers
├── pyproject.toml              # Project metadata and build system configuration
├── requirements.txt            # Python dependencies list
└── uv.lock                     # Lock file for dependency reproducibility (uv manager)
```

---

## ✨ Key Features

* **Model Context Protocol (MCP) Integration:** Exposes structured enterprise data and contextual toolsets securely through standard MCP implementations (Departments, Employees, and Notifications).
* **Multi-Agent Coordination:** Facilitates seamless interaction and task delegation between autonomous agents via dedicated client and API modules.
* **Extensible Webhook Support:** Real-time event handling and asynchronous communication via custom webhook endpoints.
* **Modern Dependency Management:** Utilizes Python's modern tooling stack (`pyproject.toml`, `uv.lock`, and `requirements.txt`) for fast environment setup and reproducible builds.

---

## 🛠️ Getting Started

### Prerequisites

* **Python 3.12+** (as specified in `.python-version`)
* [`uv`](https://github.com/astral-sh/uv) or `pip` for dependency management.

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd a2a_server_implementation
   ```

2. Install dependencies using `uv` or `pip`:
   ```bash
   uv sync
   # or
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

Configure your environment variables and server routing preferences inside `a2a_server_config.py`. Ensure that necessary internal tokens, ports, and downstream API endpoints are properly mapped before launching.

---

## 🏃 Usage & Execution

* **Run the Main Server / API:**
  ```bash
  python agents_api.py
  ```

* **Run Individual MCP Servers:**
  ```bash
  python employee_mcp_server.py
  python department_mcp_server.py
  python notification_mcp_server.py
  ```

* **Execute Demo Walkthroughs:**
  ```bash
  python demo.py
  ```

* **Start Webhook Listener:**
  ```bash
  python webhook.py
  ```