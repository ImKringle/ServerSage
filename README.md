# ServerSage - Your Wise Game Server Guardian
Welcome to **ServerSage**, your trusty companion in the realm of game server management! This Discord bot harnesses the power of the [BisectHosting ServerSpawn API](https://games.bisecthosting.com/docs) to help you command your game servers with ease.

## 🌟 Features
- **Server Management**: Effortlessly control your game servers using intuitive commands.
    - **Power Actions**: Invoke powerful commands to start, stop, restart, or terminate servers with the flick of a wrist.
    - **Server Listing**: Summon a list of all accessible servers, revealing their secrets and status.
    - **Resource Statistics**: Retrieve and display real-time resource usage statistics for your servers, including CPU and RAM utilization.

## 🧙 Prerequisites
Before embarking on your quest, ensure you have the following:
- **Python 3.12 or later**: Make sure Python is installed on your machine. You can download it from [python.org](https://www.python.org/downloads/).
- **Pip**: Pip is usually included with Python installations. You can verify its installation with `pip --version`.
- **A Discord bot token**: Create your bot via the [Discord Developer Portal](https://discord.com/developers/applications) and invite it to your server.
- **A BisectHosting account**: Ensure you have access to the ServerSpawn API.

## ⚔️ Running your own
1. **Clone the Repository**: Bring the ServerSage to your domain:\
   ~ `git clone https://github.com/ImKringle/serversage.git`\
   ~ `cd serversage`
2. **Install dependencies**: Use pip to install required packages:\
   ~ `pip install -r requirements.txt`
3. **Spawn the Sage!**: Start the bot with the following command:\
   ~ `python bot.py`\
   **Note:** On startup, if the `config.yaml` does not exist, the bot will prompt you to create one. You are not required to rename or set up the configuration file prior to running the bot; it will handle this automatically.

## 📜 Command Usage
| Command          | Usage                     | Description                                                                 |
|------------------|---------------------------|-----------------------------------------------------------------------------|
| Start a Server   | `!start <server_index>`   | Starts the specified server in your list (as defined by the config.yaml).   |
| Stop a Server    | `!stop <server_index>`    | Stops the specified server.                                                 |
| Restart a Server | `!restart <server_index>` | Restarts the specified server.                                              |
| Kill a Server    | `!kill <server_index>`    | Kills the specified server.                                                 |
| List Servers     | `!list`                   | Displays all accessible servers.                                            |
| View Stats       | `!stats <server_index>`   | Retrieves and displays the resource statistics of the specified server.     |

## 🛠️ Contributing
Contributions are welcome! If you'd like to help improve ServerSage, feel free to submit a pull request or open an issue to discuss potential enhancements.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support
If you encounter any issues or have questions, feel free to reach out through the GitHub repository via the "Issues" section