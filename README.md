# ServerSage — Discord Game Server Manager  
**ServerSage** is a self-hosted Discord bot for managing game servers via the [BisectHosting ServerSpawn API](https://games.bisecthosting.com/docs). Control your servers securely from Discord.  
> ⚠️ This bot is only intended for SelfHosted use. There is not currently a build supporting otherwise.

<img src="assets/banner.jpeg" alt="ServerSage" width="720" />

---

## Features & Command Usage

| Feature                 | Description                                    | Example Command Usage                                |
|-------------------------|------------------------------------------------|------------------------------------------------------|
| Power Actions           | Start, stop, restart, kill servers             | `!start 63ce2hd8`                                    |
| Server Listing          | View servers accessible from the API           | `!list`                                              |
| Resource Stats          | Real time CPU, RAM, Disk and Uptime statistics | `!stats 63ce2hd8`                                    |
| Remote Command Exec     | Send commands to the Servers "Console" window  | `!command 63ce2hd8 "status"`                         |
| Hidable Servers         | Hide servers from bot listing + command use    | Configured via setup                                 |
| Player List Management  | Track and clear inactive players               | `!playerlist 63ce2hd8` / `!clearplayers 63ce2hd8 7d` |
| Log Viewing             | View latest or specified server logs           | `!logs 63ce2hd8` / `!logs 63ce2hd8 logs/server.log`  |
| Steam Query             | Query server status via Steam Query protocol   | `!query 63ce2hd8`                                           |
| Panel → Discord Announce| Forward panel announcements (🚧)               | —                                                    |
| Plugin/Mod Management   | Enable/Disable Mods/Plugins (🚧)               | —                                                    |
| Startup Tab Editing     | Modify Startup Options (⏳)                     | —                                                    |
| File Management         | Upload/Download Files (⏳)                      | —                                                    |
| Activity Logs           | Audit panel actions in Discord (⏳)             | —                                                    |

--- 

## 📎Requirements

---

### 🐍 Python 3.x or Higher
> 📥 [Click Me for the Python Downloads Page](https://www.python.org/downloads/)
> > To confirm your version: python --version
---

### 📦 Pip – Python Package Installer

Pip should come bundled with your Python installation. Verify with: pip --version

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

## Quick Start

1. **Clone the repository and enter the folder:** `git clone https://github.com/ImKringle/serversage.git && cd serversage`
2. **Install required Python packages:** `pip install -r requirements.txt`
3. **Start the bot:** `python bot.py`

> ❗ On first run, an interactive setup will create your `config.yaml`. Avoid manual edits to this file.

---

## Contributing & Support

Contributions, suggestions, bug reports, and support questions are all welcome!

- **Issues:** Report bugs, request features, or ask for help on [GitHub Issues](https://github.com/ImKringle/ServerSage/issues).  
- **Pull Requests:** Fork, make changes, and submit PRs following existing style and documentation.  
- **Discussions:** Share ideas, get community support, or brainstorm on [GitHub Discussions](https://github.com/ImKringle/ServerSage/discussions).  

Thank you for helping improve and support ServerSage!

---

## License

ServerSage is licensed under a **Modified MIT License** with a non-commercial clause:

- ✅ **Personal use:** You are free to use, modify, and distribute ServerSage for personal or educational purposes.  
- ❌ **Commercial use:** Use, sale, or distribution of ServerSage for commercial purposes is **not permitted** without explicit written permission from the project owner.  

See the full license details in the [LICENSE](LICENSE) file.
