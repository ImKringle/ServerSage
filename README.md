# ServerSage - Discord-Based Game Server Management (Self-Hosted Only)

**ServerSage** is a self-hosted Discord bot built for managing game servers via the [BisectHosting ServerSpawn API](https://games.bisecthosting.com/docs). It provides a secure, centralized control interface directly within Discord — ideal for individuals or small teams who need remote server control without relying on web panels.

> ⚠️ This project is designed for self-hosted environments only. It is not available as a public or hosted bot instance.

---

## 🔧 Core Features
 
| Feature                            | Description                                                                              | Status |
|------------------------------------|------------------------------------------------------------------------------------------|--------|
| **Power Actions**                  | Start, stop, restart, or kill servers using Discord commands.                            | ✅     |
| **Server Listing**                 | View all accessible servers and their statuses.                                          | ✅     |
| **Resource Statistics**            | View real-time CPU, RAM, and disk usage.                                                 | ✅     |
| **Remote Command Execution**       | Send commands to a server's console directly through Discord.                            | ✅     |
| **Hidable Servers**                | Exclude specific servers from bot visibility using the `hide` flag during setup.         | ✅     |
| **Startup Tab Management**         | Modify Startup tab values remotely via Discord.                                          | ❌     |
| **Player List Management**         | Automatically track connected players and clean up inactive entries.                     | ✅     |
| **Panel → Discord Announcements**  | Route panel announcements (e.g. outages, game info, etc) to a dedicated Discord channel. | ❌     |
| **Log File Viewing**               | Auto-detect and display the most recent server logs, or prompt for input if needed.      | 🚧     |
| **File Management**                | Upload, remove, or fetch server files directly through Discord.                          | ❌     |
| **Activity Logs**                  | View historical panel-side actions through Discord for audit/logging purposes.           | 🚧     |

#### Status Legend
- ✅ **Complete** – Fully implemented and tested
- 🚧 **In Progress** – Feature is under development
- ❌ **Planned** – Not yet implemented

--- 

## 📎Requirements

---

### 🐍 Python 3.x or Higher
> 📥 [Click Me for the Python Downloads Page](https://www.python.org/downloads/)
> > To confirm your version: `python --version`
---

### 📦 Pip – Python Package Installer

Pip should come bundled with your Python installation. Verify with: `pip --version`

If it's missing, refer to the [official guide](https://pip.pypa.io/en/stable/installation/).

---

### 🤖 Discord Bot Token

You’ll need to register your own bot:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Generate a **Bot Token**, save this for later
4. Enable Message Intents

---

### 🎮 BisectHosting API Access

ServerSage connects with the [ServerSpawnAPI](https://games.bisecthosting.com/) to control your servers.
1. Log into your Games Panel account
2. Navigate to **Account → API**
3. Create a new API key
4. Use this key during first-time configuration of the bot
> 🔐 Keep your API key private. It provides access to all associated servers under your account.

---


## 🚀 Setup Instructions

1. **Clone the Repository**

    ```bash
    git clone https://github.com/ImKringle/serversage.git
    cd serversage
    ```

2. **Install Python Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Start the Bot**

    ```bash
    python bot.py
    ```

    > On first run, `config.yaml` will be generated via an interactive prompt. You’ll be asked to supply your API key and set up accessible servers. You can configure hidden servers at this stage as well.

---

## 📖 Command Reference

| Command        | Usage                                 | Description                                               |
|----------------|---------------------------------------|-----------------------------------------------------------|
| Start Server   | `!start <server_index>`               | Starts a selected server                                  |
| Stop Server    | `!stop <server_index>`                | Gracefully shuts down a server                            |
| Restart Server | `!restart <server_index>`             | Restarts the selected server                              |
| Kill Server    | `!kill <server_index>`                | Force kills the server (immediate shutdown)               |
| List Servers   | `!list`                               | Lists all accessible servers and their current status     |
| View Stats     | `!stats <server_index>`               | Shows CPU, memory, and disk usage for the server          |
| Run Command    | `!command <server_index> "<command>"` | Executes a command on the server console                  |

---

## 🤝 Contributing

Contributions, suggestions, and feature requests are welcome. Feel free to open an issue or submit a pull request.

---

## ⚠️ License

This project uses a **modified MIT License** with a **non-commercial use clause**.

- ✅ Personal use: Allowed
- ❌ Commercial use or resale: Prohibited without written permission

See the [LICENSE](LICENSE) file for full terms.

---

## 🧩 Support & Feedback

Need help? Open a ticket via GitHub [Issues](https://github.com/ImKringle/ServerSage/issues) or start a discussion. Your input helps guide future improvements.
