# 🌐 NetVision v2.0

NetVision is a high-performance, cyberpunk-themed local network scanner. It provides a real-time visual dashboard for monitoring active devices, identifying vendors, and auditing network security through port analysis.

<img width="1917" height="993" alt="image" src="https://github.com/user-attachments/assets/bbd5ab62-92ad-4bc9-b726-3aa908cfe2e3" />

## Features

*   **Recursive Discovery:** 254+ nodes analyzed in seconds using multi-threaded ICMP requests.
*   **OS Fingerprinting:** Advanced logic to guess operating systems (Windows, Linux, Mobile) via port signatures.
*   **Hardware Identification:** Automatic vendor detection (TP-Link, Apple, Samsung) using a built-in MAC-prefix database.
*   **Cyberpunk Dashboard:** Interactive dark-mode UI with a grid background, neon hover effects, and smooth animations.
*   **Live Latency Tracking:** Real-time ping monitoring to evaluate connection stability and node response time.
*   **Security Auditing:** Integrated port scanner to detect open services like SSH, HTTP, and SMB.
*   **Privacy Protected:** For security reasons, all sensitive hardware identifiers (MAC addresses) are masked in public previews.
*   **Zero-Dependency:** Built with pure Vanilla JS and standard Python libraries for maximum execution speed.

## How to run

1.  **Start the Backend:** Run `python server.py` to launch the multi-threaded scanning engine on port 5005.
2.  **Launch Dashboard:** Open `index.html` in any modern web browser (VS Code Live Server recommended).
3.  **Execute Scan:** Click the **RUN DEEP SCAN** button to begin mapping your local network environment.

**Note:** The scanner is optimized for the `192.168.0.x` range. Ensure your backend is running with appropriate permissions to access network utilities.

## Tech stack

*   **HTML5** — semantic structure and grid-based dashboard layout.
*   **CSS3** — custom cyberpunk theme with radial-gradient backgrounds and glow-on-hover effects.
*   **Vanilla JavaScript** — core engine for asynchronous data fetching and dynamic DOM rendering.
*   **Python 3** — algorithmic multi-threaded engine for ARP and TCP port scanning.

## Project structure

<img width="286" height="140" alt="image" src="https://github.com/user-attachments/assets/6480e2e4-710d-483d-bcef-5bb33791c7e5" />
