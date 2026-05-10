## Kaoruko (moe moe moe)

![License](https://img.shields.io/github/license/Creeper011/kaoruko)
![Stars](https://img.shields.io/github/stars/Creeper011/kaoruko)
![Forks](https://img.shields.io/github/forks/Creeper011/kaoruko)
![Issues](https://img.shields.io/github/issues/Creeper011/kaoruko)

<img src="https://count.getloli.com/get/@kaoruko?theme=rule34" width="500">

Kaoruko is a lovable Discord bot built with discord.py (Python) featuring cute cute personal project.

**Features:**
- Download command (with cache, remote storage and timed download) [Not all features is implemented]
- Speed changer command (Not implemented yet)

**Requirements:**
- [Python 3.12.5+](https://www.python.org/downloads/release/python-3125/)
- [Make](https://www.gnu.org/software/make/)

**Documentation:**
- The documentation for Kaoruko can be found in ./docs folder. [See the docs](./docs/)

**Installation:**
1. Clone the repository
2. Navigate to the project directory
3. Create a virtual environment
4. Activate the virtual environment
5. Install dependencies and run

```bash
git clone https://github.com/Creeper011/kaoruko
cd kaoruko
make venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
make install
make run
```

**Note:** If you use **pyenv**, run these commands first:
```bash
pyenv install 3.12.5
pyenv local 3.12.5  # in project folder
```

**Docker (optional):**
- You can also run Kaoruko using Docker. Make sure you have Docker installed and run the following command:
```bash
docker build -t kaoruko .
docker run -d --name kaoruko -e TOKEN=your_discord_bot_token -p 8080:8080 kaoruko
```

Made with fear and love by yumeeeeeeeeene (yumene)