# Installation

## How to install
### linux
```bash
1. git clone https://github.com/lainsec/rchan
2. cd rchan
3. python3 -m venv rchanenv
4. source rchanenv/bin/activate
5. pip install -r requirements.txt
```
### windows
```bash
1. git clone https://github.com/lainsec/rchan
2. cd rchan
3. python3 -m venv rchanenv
4. rchanenv\Scripts\activate.bat
5. pip install -r requirements.txt python-magic-bin
```
## How to use
```bash
python3 app.py
`The first account will automatically recive OWNER permissions.`
```

# Live instances (Unofficial)
- 🇧🇷 [karty](https://kekw.party) 
- 🇷🇺 [pejchan](https://pejchan.mooo.com) (currently offline)

# Features
- [x] Fully configurable through the dashboard, allowing real-time adjustments without code changes.
- [x] Free creation of boards for all users (Toggleable).
- [x] Lightweight source code.
- [x] Fully usable without JS enabled.
- [x] Real-time posts with websocket.
- [x] Responsive style for mobile.
- [x] Tripcode system with SHA256.
- [x] Encrypted passwords and IP with bcrypt.
- [x] CSRF Protection for all routes.
- [x] Uploads validated by file extension, mimetype and python-magic and metadata removal.
- [x] Board pagination.
- [x] Multi language i18n support. 🇯🇵 🇧🇷 🇺🇸 🇪🇸
- [x] Media Pending Approval system (Toggleable per board).
- [x] Word filters system editable on the dashboard.
- [X] Server-side text decoration for posts.
- [x] Spoiler and filename strip (poster's choice) 
- [x] Anti-spam with built-in toggleable captcha per board, timeout and evade ban system.

# License
GNU AGPLv3, see [LICENSE](https://github.com/lainsec/rchan/blob/master/LICENSE)

# Help
For those who wants to help keep the project up:
Ethereum: `0x6107BD27BcCB4305224320Ca03057E192b18fa75`
