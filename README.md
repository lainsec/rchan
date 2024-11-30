<h2 align="left">Imageboard engine, full written in python.</h2>

###
<a>How to install</a>
<pre align="left">
1. git clone https://github.com/lainsec/rchan
2. cd rchan
3. python3 -m venv rchanenv
4. source rchanenv/bin/activate
5. pip install -r requirements.txt
</pre>
<a>How to use</a>
<pre align="left">
python3 app.py
`The first account will automatically recive OWNER permissions.`
</pre>
# Features
- [x] Free creation of boards for all users.
- [x] Realtime posts with websocket.
- [x] Responsive style for mobile.
- [x] Tripcode system with SHA256.
- [x] Board pagination
- [x] Multi language. 🇯🇵 🇧🇷 🇺🇸 🇪🇸
- [x] Encrypted passwords with SHA256.
- [x] Anti-raid with internal captcha and timeout system.

<a>If you get any issue please comment</a>
###

# Frequently Asked Questions
- _How to use tripcode ?_
  - _You have to type your username and put an "#" and an random word all togheter:_
  - _It will generate an SHA256 hash and display the first 15 digits from it beside your name._
- _How to style my text ?_
  - **_>text_** _will display the >text but green painted._
  - **_<text_** _will display the <text but red painted._
  - _**==text==**_ _will display the text but red painted and BOLD._
  - _**[r]text[/r]**_ _will turn the text into a rainbow._
  - _**[spoiler]text[/spoiler]**_ _will hide the text with a black box and show with your mouse hover._
  - _**(((text)))**_ _will display the text but with a white background and blue color._


<img src="https://i.postimg.cc/nhkWNZTD/homepage.png" style="user-select:none; max-width:200; max-height:400;" alt="rein">
