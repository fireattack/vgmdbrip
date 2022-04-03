from sys import argv
import os
import json
import hashlib
import getpass
import pickle
import requests
from bs4 import BeautifulSoup

scriptdir = os.sep.join(argv[0].split("\\")[:-1])
config = os.path.join(scriptdir, 'vgmdbrip.pkl')
session = requests.Session()


def safeify(name):
    template = {u'\\': u'＼', u'/': u'／', u':': u'：', u'*': u'＊',
                u'?': u'？', u'"': u'＂', u'<': u'＜', u'>': u'＞', u'|': u'｜','\n':'','\r':'','\t':''}
    for illegal in template:
        name = name.replace(illegal, template[illegal])
    return name


def Soup(data):
    return BeautifulSoup(data, "html.parser")


def login():
    global session
    if os.path.isfile(config):
        session = pickle.load(open(config, "rb"))
    else:
        while True:
            username = input('VGMdb username:\t')
            password = getpass.getpass('VGMdb password:\t')
            base_url = 'https://vgmdb.net/forums/'
            x = session.post(base_url + 'login.php?do=login', {
                'vb_login_username':        username,
                'vb_login_password':        password,
                'vb_login_md5password':     hashlib.md5(password.encode()).hexdigest(),
                'vb_login_md5password_utf': hashlib.md5(password.encode()).hexdigest(),
                'cookieuser': 1,
                'do': 'login',
                's': '',
                'securitytoken': 'guest'
            })
            table = Soup(x.content).find(
                'table', class_='tborder', width="70%")
            panel = table.find('div', class_='panel')
            message = panel.text.strip()
            print(message)

            if message.startswith('You'):
                if message[223] == '5':
                    raise SystemExit(1)
                print(message)
                continue
            elif message.startswith('Wrong'):
                raise SystemExit(1)
            else:
                break


def remove(instring, chars):
    for i in range(len(chars)):
        instring = instring.replace(chars[i], "")
    return instring


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)


if(len(argv) < 2):
    print("usage: " + argv[0] + " vgmdb_album_id")
    raise SystemExit(1)


def process_page(soup, keyword=None):
    print('Title: ' + soup.title.text)
    title = soup.find('span', {'class': 'albumtitle', 'lang': 'ja'}).find(
        text=True, recursive=False)
    folder = safeify(title)
    if keyword:
      folder += f' ({keyword})'
    gallery = soup.find("div", attrs={"class": "covertab",
                                      "id": "cover_gallery"})
    for scan in gallery.find_all("a", attrs={"class": "highslide"}):
        url = scan["href"]
        title = remove(scan.text.strip(), "\"*/:<>?\|")
        image = session.get(url).content
        ensure_dir(folder + os.sep)
        filename = title + url[-4:]
        with open(os.path.join(folder, filename), "wb") as f:
            f.write(image)
        print(title + " downloaded")


login()
soup = ""
if all(keyword.isnumeric() for keyword in argv[1:]):
    for keyword in argv[1:]:
        soup = Soup(session.get("https://vgmdb.net/album/" + keyword).content)
        process_page(soup, keyword)
else:
    query = " ".join(argv[1:])
    soup = Soup(session.get(
        "https://vgmdb.net/search?q=\"" + query + "\"").content)
    if(soup.title.text[:6] == "Search"):
        print("stuck at search results")
        exit(1)
    else:
        process_page(soup, None)

pickle.dump(session, open(config, "wb"))
