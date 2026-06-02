# NETVISION 🌐
<img width="1915" height="993" alt="image" src="https://github.com/user-attachments/assets/f5dd948c-c836-47fa-9381-0e7d14f12605" />

**Asynchronous low-level home network scanner and service fingerprinting dashboard.**

NETVISION is a lightweight, zero-dependency network security auditor and monitoring dashboard designed to map local subnets in real-time. Instead of relying on heavy third-party scanning frameworks, it utilizes an asynchronous event-driven Python backend to coordinate concurrent ping sweeps, resolve local hostnames, and perform low-level TCP socket banner-grabbing to identify active services and operating system footprints.

---

## Features

*   **Asynchronous Event Streaming:** Implements Server-Sent Events (SSE) to stream active host discoveries to the web interface progressively, eliminating blocking render delays.
*   **Low-Level Service Fingerprinting:** Establishes raw TCP connections to common ports (SSH, HTTP, SMB) to read service banners directly from network sockets, exposing exact application versions.
*   **Intruder Mitigation System:** Leverages local browser storage (`localStorage`) to maintain a persistent hardware whitelist, instantly flagging unknown MAC addresses with a glowing visual alarm.
*   **Non-Blocking Concurrent Sweeping:** Coordinates a fast ping sweep of all 254 subnet addresses in parallel using a Python `ThreadPoolExecutor` worker pool.
*   **Dynamic Information Drawers:** Features smooth CSS-animated drawer transitions on the device cards, allowing users to expand nodes to inspect raw service banners.
*   **Standardized JSON Reporting:** Serializes mapped network nodes, resolved hostnames, and grabbed service metadata into a downloadable, structured JSON forensic report.
*   **Data Masking Standards:** Built with privacy in mind; sensitive physical hardware addresses (MACs) are masked inside public dashboard presentations to prevent physical network correlation.

---

## How to run

1.  **Administrative Access:** Open PowerShell, command prompt, or terminal as an Administrator to ensure full permissions for ARP table queries and system pings.
2.  **Clone the Repository:** Download the project files and place them in your local workspace directory:
    ```bash
    git clone https://github.com/d3fuse99/Netvision.git
    ```
3.  **Start the Backend Engine:** Execute the Python script using standard Python 3:
    ```bash
    python server.py
    ```
4.  **Launch Web Dashboard:** Open the `index.html` file in any modern web browser. For real-time updates and proper SSE execution, serving it via a local static server (like VS Code Live Server) is recommended.

## Project structure

<img width="286" height="140" alt="image" src="https://github.com/user-attachments/assets/6480e2e4-710d-483d-bcef-5bb33791c7e5" />
