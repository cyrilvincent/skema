import requests
import bs4
import re

with requests.Session() as s:
    response = s.get("http://annuairesante.ameli.fr/")
    print(response)
    print(response.cookies)
    print(response.content)
    soup = bs4.BeautifulSoup(response.content,"html.parser")
    #print(soup.prettify())
#    tag = soup.find(id="buttonPS")
#    href = tag.attrs["href"]
#    regex = r"/accessible-professionnels-de-sante-([\d\w]+).html"
#    match = re.match(regex, href)
#    id = match[1]
#    print(id)

    #response = s.get(f"http://annuairesante.ameli.fr/accessible-professionnels-de-sante-{id}.html")
    response = s.get(f"http://annuairesante.ameli.fr/accessible-professionnels-de-sante.html")
    print(response)
    soup = bs4.BeautifulSoup(response.content, "html.parser")

    data = {"ps_nom": "aa", "type": "ps"}
    #response = s.post(f"http://annuairesante.ameli.fr/recherche-{id}.html", data = data, allow_redirects=True)
    response = s.post(f"http://annuairesante.ameli.fr/recherche.html", data=data, allow_redirects=True)
    print(response.history[0])
    print(response.history[0].headers["Location"])
    response = s.get("http://annuairesante.ameli.fr/professionnels-de-sante/recherche/liste-resultats-page-1-par_page-20-tri-nom_asc.html")
    soup = bs4.BeautifulSoup(response.content, "html.parser")
    tag = soup.find("img", attrs={"alt":" - Aller à la dernière page"})
    href = tag.parent.attrs["href"]
    print(href)
    regex = r'/professionnels-de-sante/recherche/liste-resultats-page-([\d\w]+)-par_page-20-tri-nom_asc.html'
    match = re.match(regex, href)
    nb = int(match[1])
    print(f"Nb:{nb}")
    tags = soup.find_all("strong")
    print(len(tags))
    for tag in tags:
        print(tag.string)
        href= tag.parent.attrs["href"]
        response = s.get("http://annuairesante.ameli.fr"+href)
        print(response)
        soup = bs4.BeautifulSoup(response.content, "html.parser")
        tag = soup.find("h2", attrs = {"class":"item left tel"})
        if tag != None:
            tel = tag.contents[0].replace('\xa0', '')
            print(tel)
        tag = soup.find("div", attrs = {"class":"item right convention"})
        if tag != None:
            a = tag.findChildren("a")
            if len(a) > 0:
                print(a[0].contents[0])








