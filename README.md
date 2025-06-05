# ServerSage - Your Wise Game Server Guardian

Welcome to **ServerSage**, your trusty companion in the realm of game server management! This Discord bot harnesses the power of the [BisectHosting ServerSpawn API](https://games.bisecthosting.com/docs) to help you command your game servers with ease.

---

## 🌟 Features

- **Server Management**  
  Effortlessly control your game servers using intuitive commands.  
  - **Power Actions**: Start, stop, restart, or kill servers with simple commands.  
  - **Server Listing**: View all accessible servers and their statuses at a glance.  
  - **Resource Statistics**: Fetch real-time CPU, RAM, and disk usage for your servers.
  - **Remote Command Use**: Run commands for your servers anywhere through your Discord Server
  - **Hidable Servers**: Don't want a server to be manageable through Discord? Set "hide" to True on Config Creation or Manual Addition!
---

## 🧙 Prerequisites

Before embarking on your quest, make sure you have:

- **Python 3.12 or later**  
  Download from [python.org](https://www.python.org/downloads/).  
- **Pip**  
  Usually included with Python, though can be checked with: `pip --version`
- **A Discord Bot Token**  
  Create your bot via the [Discord Developer Portal](https://discord.com/developers/applications) and invite it to your server.  
- **A BisectHosting Account with access to a Server**  
  This will provide access to the API, you can create a key [here](https://games.bisecthosting.com/account/api) on the Games Panel.

---

## ⚔️ Running Your Own ServerSage

1. **Clone the Repository**

    ```bash
    git clone https://github.com/ImKringle/serversage.git
    cd serversage
    ```

2. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Spawn the Sage!**

    ```bash
    python bot.py
    ```

    > **Note:** If `config.yaml` does not exist, the bot will prompt you to create one automatically. No prior configuration is necessary.
    It is recommended to enter *all* Servers accessible via your API Token on Setup, and setting any you don't want managed to hide on Setup.
---

## 📜 Command Usage

| Command        | Usage                                | Description                                                |
|----------------|--------------------------------------|------------------------------------------------------------|
| Start a Server | `!start <server_index>`              | Starts the specified server                                |
| Stop a Server  | `!stop <server_index>`               | Stops the specified server.                                |
| Restart Server | `!restart <server_index>`            | Restarts the specified server.                             |
| Kill a Server  | `!kill <server_index>`               | Force kills the specified server.                          |
| List Servers   | `!list`                              | Lists all accessible servers with their status.            |
| View Stats     | `!stats <server_index>`              | Shows resource usage stats (CPU, RAM, Disk) for the server. |
| Send a Command | `!command <server_index> "<command>"` | Sends the defined Command to the server Console            |

---

## 🛠️ Contributing

Contributions are very welcome! Feel free to submit pull requests or open issues for discussion and feature requests.

---

## 📞 Support

Encountered issues or have questions? Reach out via the GitHub repository's **Issues** section. Your feedback helps ServerSage grow stronger!
