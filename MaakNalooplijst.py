#!/usr/bin/python3

"""
inspired by:
    get_usercontribs.py

    MediaWiki API Demos
    Demo of `Usercontribs` module: List user contributions.

    MIT License
"""
groep = 'TPP'
accounts = ('Torval', 'PeterKeijsers', 'Paolingstein' )
sjabloonnaam = 'Gerichte aanpak artikelen TPP'

test = True

if test:
  maxaantal = 3
else:
  maxaantal = 9999999

import requests
import pywikibot
from pywikibot import User
import sqlite3
import re
import nl_tabellen as tabledefs
from datetime import datetime, timedelta
import time


accountnaam = ''
for account in accounts:
  if accountnaam == '':
    accountnaam += account
  else:
    accountnaam += '/* '+account
accountnaam = ' of '.join(accountnaam.rsplit('/* ', 1))
accountnaam = accountnaam.replace('/* ',', ')

site = pywikibot.Site('nl', 'wikipedia')

def verzamelbewerkt(conn, gebruikersnaam):
  PARAMS = {
    "action": "query",
    "format": "json",
    "list": "usercontribs",
    "ucuser": gebruikersnaam,
    "ucnamespace": "0",
    "uclimit": "max",
    "ucdir": "newer",
    "ucprop": "title|size|ids"
  }
  sqlpagina = 'INSERT INTO `editedpaginas` VALUES (?,?,?,?,?, ?,?,?)'
  sqlpaginabestaat = 'SELECT COUNT(*) AS `Aantal` FROM `nieuwepaginas` WHERE `titel` = ?'
  sqlpaginabestaat2 = 'SELECT COUNT(*) AS `Aantal` FROM `editedpaginas` WHERE `titel` = ?'
  verzamel(conn, PARAMS, sqlpagina, sqlpaginabestaat, sqlpaginabestaat2, 0)

def verzamelnieuw(conn, gebruikersnaam):
  PARAMS = {
    "action": "query",
    "format": "json",
    "list": "usercontribs",
    "ucuser": gebruikersnaam,
    "ucnamespace": "0",
    "ucshow": "new",
    "uclimit": "max",
    "ucdir": "newer",
    "ucprop": "title|size|ids"
  }
  sqlpagina = 'INSERT INTO `nieuwepaginas` VALUES (?,?,?,?,?, ?,?,?)'
  sqlpaginabestaat = sqlpaginabestaat2 = ''
  verzamel(conn, PARAMS, sqlpagina, sqlpaginabestaat, sqlpaginabestaat2, 1)
  
def verzamel(conn, PARAMS, sqlpagina, sqlpaginabestaat, sqlpaginabestaat2, isnieuw):
  curs = conn.cursor()
  knight = 1
  dvp = redirect = verwijderd = 0
  S = requests.Session()

  URL = "https://nl.wikipedia.org/w/api.php"

  sqlpagbew = 'INSERT INTO `paginabewerkers` VALUES (?,?,?,?)'
  lastContinue = {}
  while True:
    req = PARAMS.copy()
    req.update(lastContinue)
    R = S.get(url=URL, params=req)
    DATA = R.json()
    
    USERCONTRIBS = DATA["query"]["usercontribs"]
    for uc in USERCONTRIBS:
      title = uc["title"] 
      pbparam = [title,]
      if sqlpaginabestaat != '':
        curs.execute(sqlpaginabestaat, pbparam)
        row = curs.fetchone()
        if row['Aantal']!=0:
          continue
        curs.execute(sqlpaginabestaat2, pbparam)
        row = curs.fetchone()
        if row['Aantal']!=0:
          continue
      id = uc["pageid"]
      orgsize = uc["size"] 
      print(knight, title, orgsize, id)
      tbp = pywikibot.Page(site,title)
      if not tbp.exists():
        status = u'verwijderd'
        verwijderd += 1 
      else:
        if tbp.isRedirectPage():
          status = u'doorverwijzing'
          redirect += 1 
        else:
          if tbp.isDisambig():
            status = u'doorverwijspagina'
            dvp += 1 
          else:
            status = ''
      ts_edit_time = tbp.latest_revision.timestamp
      edit_time = u'{}-{:02}-{:02}'.format( ts_edit_time.year, ts_edit_time.month, ts_edit_time.day)
      total_edits = tbp.revision_count()
      contributors = tbp.contributors()
      n_contributors = len(contributors)
      current_size = tbp.latest_revision.size
      print (n_contributors, current_size,)
      if n_contributors <30:
        for cb in contributors:
          aantal = tbp.revision_count(contributors=cb) 
          param_pagbew = [title, cb, aantal, isnieuw,]
          curs.execute(sqlpagbew, param_pagbew)

      param_pagina = [title, id, orgsize, current_size, edit_time, n_contributors, total_edits, status,]
      curs.execute(sqlpagina, param_pagina)
      conn.commit()
      knight = knight+1
    if 'continue' not in DATA:
      break
    lastContinue = DATA['continue']      

  print ("verwijderd:", verwijderd, "redirects:", redirect, "doorverwijspagina's:", dvp)
  conn.commit()
  
def verwerkbewerkers(conn):
  curspb = conn.cursor()
  cursbw = conn.cursor()
  sqlbewerker = 'INSERT INTO `bewerkers` VALUES (?,?,?,?,?, ?,?)'
  sqlbot = 'UPDATE `bewerkers` SET `isbot`=1 WHERE `naam` = ?'
  sqlpagbew = 'SELECT DISTINCT(`bewerker`) FROM `paginabewerkers` ORDER BY `bewerker`'
  cbew = curspb.execute(sqlpagbew)
  while True:
    row = cbew.fetchone()
    if row == None:
      break
    cb = row['bewerker']
    user = User(site, cb)
    contribs = user.contributions(total=1, reverse=False)
    for page, oldid, ts, comment in contribs:
      ts_edit_time = ts
      last_edit = u'{}-{:02}-{:02}'.format( ts_edit_time.year, ts_edit_time.month, ts_edit_time.day)
    userpage = user.getUserPage().title()
    botbewerkbaar = user.getUserPage().botMayEdit() 
    param_bewerker = [cb, last_edit, user.isAnonymous(), user.isBlocked(), userpage, 0, botbewerkbaar] 
    print(param_bewerker)
    cursbw.execute(sqlbewerker, param_bewerker)
  conn.commit()                                                    \
  
  bots = site.botusers()
  for bot in bots:
    param = [bot['name'],]
    cursbw.execute(sqlbot, param)
  conn.commit()                                                    \
  
def getborderdate():
  now = datetime.now()
  six_months_ago = now - timedelta(days = 180)
  borderdate = u'{}-{:02}-{:02}'.format( six_months_ago.year, six_months_ago.month, six_months_ago.day)
  return (borderdate)   
  
def getAantalGeinformeerdeBewerkers(conn, pagetitle):
  curspb = conn.cursor()
  sql = 'SELECT COUNT(`bewerker`) AS `aantal` FROM paginabewerkers WHERE `pagina`= ? AND `bewerker` NOT IN (SELECT `naam` FROM `bewerkers` WHERE `isanoniem`>0 OR `isgeblokkeerd`>0 OR `isbot`=1 OR `isbotbewerkbaar`=0 OR `laatstebewerking`< ?)'
  param = [pagetitle, getborderdate(), ]
  cpb = curspb.execute(sql, param)
  row = cpb.fetchone()
  return row['aantal']
  
def maakartikellijst(conn):
  curspa = conn.cursor()
  text  = '== Toelichting ==\n'
  text += '\n'
  text += '* Kolom Behouden – Kladruimte:\n'
  text += "** {{aut|<big><u>Artikel grondig nagekeken</u></big>}}? Zet je handtekening erachter voor behoud. '''<nowiki>~~~~</nowiki>'''\n"
  text += '** Opknappers verplaats je naar je eigen kladruimte. Dan geen handtekening, maar een link naar het kladblok.\n'
  text += '* Kolom Toelichting – Commentaar:\n'
  text += '** Ruimte voor toelichting en commentaar, met beperkte discussie.\n'
  text += '** Bij behoud dienen daadwerkelijk alle tekst en alle toegevoegde bronvermeldingen op inhoudelijke juistheid te zijn gecontroleerd\n'
  text += f'Daadwerkelijke verwijdering is te verwachten tussen 20 november 2023 en eind januari 2024, zie [[Overleg Wikipedia:Stemlokaal/Methodiek voor het verwijderen van artikelen van Torval/PeterKeijsers/Paolingstein (TPP)#Mogelijke tijdlijn|Overleg bij de stem#Mogelijke tijdlijn]].\n'
  text += '\n'
  text += '== Tabel aangemaakte artikelen ==\n'
  text += '{| class="wikitable sortable"\n'
  text += '!id!!paginatitel\n'
  text += '!# bewer-<br>kers!!# geïnfor-<br>meerde bewer-<br>kers!!# bewer-<br>kingen!!laatste bewerking\n'
  text += '!# originele grootte!!# huidige grootte\n'
  text += '!Behouden – Kladruimte\n'
  text += 'Handtekening (erbij) voor evt. overleg\n'
  text += '!Toelichting – Commentaar\n'
  text += 'Handtekening erbij voor evt. overleg\n'
  sqlpag = "SELECT * FROM `nieuwepaginas` WHERE `status`='' ORDER BY `titel`"
  cpag = curspa.execute(sqlpag)
  while True:
    row = cpag.fetchone()
    if row == None:
      break
    text += '|-\n'
    text +=f"|{row['id']}||[[{row['titel']}]]"
    geinformeerdebewerkers = getAantalGeinformeerdeBewerkers(conn, row['titel'])
    text +=f"||{row['aantalbewerkers']}||{geinformeerdebewerkers}||{row['aantalbewerkingen']}||{row['laatstebewerking']}"
    text +=f"||{row['orggrootte']}||{row['huidigegrootte']}\n"
    text += '|\n'
    text += '|\n'
  text += '|}\n\n'

  sqlpag = "SELECT * FROM `nieuwepaginas` WHERE `status`<>'' ORDER BY `status`, `titel`"
  cpag = curspa.execute(sqlpag)
  text += '== Tabel aangemaakte niet-artikelen in de hoofdnaamruimte ==\n'
  text += '{| class="wikitable sortable"\n'
  text += '!id!!paginatitel\n'
  text += '!# bewer-<br>kers!!# geïnfor-<br>meerde bewer-<br>kers!!# bewer-<br>kingen!!laatste bewerking\n'
  text += '!soort!!# originele grootte!!# huidige grootte\n'
  text += '!Behouden – Kladruimte\n'
  text += 'Handtekening (erbij) voor evt. overleg\n'
  text += '!Toelichting – Commentaar\n'
  text += 'Handtekening erbij voor evt. overleg\n'
  while True:
    row = cpag.fetchone()
    if row == None:
      break
    text += '|-\n'
    text +=f"|{row['id']}||[[{row['titel']}]]"
    geinformeerdebewerkers = getAantalGeinformeerdeBewerkers(conn, row['titel'])
    text +=f"||{row['aantalbewerkers']}||{geinformeerdebewerkers}||{row['aantalbewerkingen']}||{row['laatstebewerking']}"
    text +=f"||{row['status']}||{row['orggrootte']}||{row['huidigegrootte']}\n"
    text += '|\n'
    text += '|\n'
  text += '|}\n\n'
  
  text += '== Tabel overige bewerkte artikelen in de hoofdnaamruimte ==\n'
  text += '{| class="wikitable sortable"\n'
  text += '!id!!paginatitel\n'
  text += '!# bewer-<br>kers!!# geïnfor-<br>meerde bewer-<br>kers!!# bewer-<br>kingen!!laatste bewerking\n'
  text += '!# originele grootte!!# huidige grootte\n'
  text += '!Behouden – Kladruimte\n'
  text += 'Handtekening (erbij) voor evt. overleg\n'
  text += '!Toelichting – Commentaar\n'
  text += 'Handtekening erbij voor evt. overleg\n'
  sqlpag = "SELECT * FROM `editedpaginas` WHERE `status`='' ORDER BY `titel`"
  cpag = curspa.execute(sqlpag)
  while True:
    row = cpag.fetchone()
    if row == None:
      break
    text += '|-\n'
    text +=f"|{row['id']}||[[{row['titel']}]]"
    geinformeerdebewerkers = getAantalGeinformeerdeBewerkers(conn, row['titel'])
    text +=f"||{row['aantalbewerkers']}||{geinformeerdebewerkers}||{row['aantalbewerkingen']}||{row['laatstebewerking']}"
    text +=f"||{row['orggrootte']}||{row['huidigegrootte']}\n"
    text += '|\n'
    text += '|\n'
  text += '|}\n\n'

  sqlpag = "SELECT * FROM `editedpaginas` WHERE `status`<>'' ORDER BY `status`, `titel`"
  cpag = curspa.execute(sqlpag)
  text += '== Tabel overige bewerkte niet-artikelen in de hoofdnaamruimte ==\n'
  text += '{| class="wikitable sortable"\n'
  text += '!id!!paginatitel\n'
  text += '!# bewer-<br>kers!!# geïnfor-<br>meerde bewer-<br>kers!!# bewer-<br>kingen!!laatste bewerking\n'
  text += '!soort!!# originele grootte!!# huidige grootte\n'
  text += '!Behouden – Kladruimte\n'
  text += 'Handtekening (erbij) voor evt. overleg\n'
  text += '!Toelichting – Commentaar\n'
  text += 'Handtekening erbij voor evt. overleg\n'
  while True:
    row = cpag.fetchone()
    if row == None:
      break
    text += '|-\n'
    text +=f"|{row['id']}||[[{row['titel']}]]"
    geinformeerdebewerkers = getAantalGeinformeerdeBewerkers(conn, row['titel'])
    text +=f"||{row['aantalbewerkers']}||{geinformeerdebewerkers}||{row['aantalbewerkingen']}||{row['laatstebewerking']}"
    text +=f"||{row['status']}||{row['orggrootte']}||{row['huidigegrootte']}\n"
    text += '|\n'
    text += '|\n'
  text += '|}'
  
  PageTitle = f'Gebruiker:RonnieV/Nalooplijst/{groep}'
  page = pywikibot.Page(site, PageTitle )
  page.text = text
  Toelichting = 'Lijst met informatie bijgewerkt'
  page.save(Toelichting)
  
def addsection(title, summary, text):
  page = pywikibot.Page(site, title)
  result = pywikibot.site.APISite.editpage(
    site,
    page=page,
    summary=summary,
    minor=False,
    text=text,
    section="new"
  )
  return result
  
def getPaginasBewerkt(conn, bewerker, isnieuw):
  curspb = conn.cursor()
  aantal = 0
  param = [bewerker, isnieuw,]
  text = ''

  sql = 'SELECT `pagina`, `aantal` FROM `paginabewerkers` WHERE `bewerker` = ? AND `isnieuw` = ? ORDER BY `pagina`'   
  cpb = curspb.execute(sql, param)
  while True:
    row = cpb.fetchone()
    if row == None:
      break
    if text == '':
      text = f"* [[{row['pagina']}]] - ({row['aantal']} bewerking"
      if row['aantal']!=1:
        text+= "en"
      text+= ")\n"
    else:
      text+= f"* [[{row['pagina']}]] - ({row['aantal']})\n"
    aantal += 1
  return (aantal, text)
    
def maakoverzichtbewerkers(conn):
  cursbw = conn.cursor()
  paramrecent = [getborderdate(),]
  sqlbw = 'SELECT COUNT(*) AS `Aantal` FROM `bewerkers`'
  
  text = "De volgende aantallen bewerkers hebben bijgedragen aan pagina's op deze nalooplijst:\n"
  text += '{| class="wikitable"\n'
  text += '!omschrijving!!aantal\n'
  text += '|-\n'
  condition = ''
  sqltoperform = f"{sqlbw} {condition}"
  cursbw.execute(sqltoperform)
  row = cursbw.fetchone()
  text +=f"|alle bewerkers||{row['Aantal']}\n"
  
  text += '|-\n'
  condition = ' WHERE `isanoniem`<>0'
  sqltoperform = f"{sqlbw} {condition}"
  cursbw.execute(sqltoperform)
  row = cursbw.fetchone()
  text +=f"|anoniemen||{row['Aantal']}\n"

  text += '|-\n'
  condition = ' WHERE `isgeblokkeerd`<>0'
  sqltoperform = f"{sqlbw} {condition}"
  cursbw.execute(sqltoperform)
  row = cursbw.fetchone()
  text +=f"|geblokkeerd||{row['Aantal']}\n"

  text += '|-\n'
  condition = ' WHERE `isbot`<>0'
  sqltoperform = f"{sqlbw} {condition}"
  cursbw.execute(sqltoperform)
  row = cursbw.fetchone()
  text +=f"|bots||{row['Aantal']}\n"

  text += '|-\n'
  condition = ' WHERE `isbotbewerkbaar`=0'
  sqltoperform = f"{sqlbw} {condition}"
  cursbw.execute(sqltoperform)
  row = cursbw.fetchone()
  text +=f"|niet bot-bewerkbare GOP||{row['Aantal']}\n"
  
  text += '|-\n'
  condition = ' WHERE `laatstebewerking`< ?'
  sqltoperform = f"{sqlbw} {condition}"
  cursbw.execute(sqltoperform, paramrecent)
  row = cursbw.fetchone()
  text +=f"|al lang niet bewerker (voor {paramrecent[0]})||{row['Aantal']}\n"
  
  text += '|-\n'
  condition = ' WHERE `isbotbewerkbaar`=1 AND `isanoniem`=0 AND `isgeblokkeerd`=0 AND `isbot`=0 AND  `laatstebewerking`>= ?'
  sqltoperform = f"{sqlbw} {condition}"
  cursbw.execute(sqltoperform, paramrecent)
  row = cursbw.fetchone()
  text +=f"|bereikbaar||{row['Aantal']}\n"
  text += '|}'
  
  PageTitle = f'Gebruiker:RonnieV/Nalooplijst/{groep}-bewerkers'
  page = pywikibot.Page(site, PageTitle )
  page.text = text
  Toelichting = 'De aantallen bewerkers voor deze nalooplijst'
  page.save(Toelichting)
  
def plaatssjabloon (conn):
  aantal = 0
  curspag = conn.cursor()
  sqlpag = "SELECT `titel` FROM `nieuwepaginas` WHERE `status`='' ORDER BY `titel`"
  cp = curspag.execute(sqlpag)
  toelichting = f'Toevoeging aanpaksjabloon {accountnaam}'
  while True:
    try:
      row = cp.fetchone()
      if row == None:
        break
      PageTitle= row['titel']
      page = pywikibot.Page(site, PageTitle )
      if page.exists():
        text = page.text;
        eind = text.find(sjabloonnaam)
        if eind == -1:
#              oldestrevision = page.oldest_revision
#              text = nieuwevermelding.format(oldestrevision.timestamp.year) + text[eind+len(eindevermelding):]
          text = f'{{{{{sjabloonnaam}}}}}\n{text}'
          page.text = text
          page.save(toelichting)
    except:
      print ('Er is een fout opgetreden bij pagina', page)
    aantal += 1
    if aantal > maxaantal:
      break

def maakbewerkersteksten(conn):    
  cursbw = conn.cursor()
  sqlbw = 'SELECT * FROM `bewerkers` WHERE `isanoniem`=0 AND `isgeblokkeerd`=0 AND `isbot`=0 AND `isbotbewerkbaar`=1 AND `laatstebewerking`>= ? ORDER BY `naam`'
  param = [getborderdate(),]
  cbew = cursbw.execute(sqlbw, param)
  aantal = 0
  while True:
    row = cbew.fetchone()
    if row == None:
      break
    bewerker = row['naam']
    aantalnw, linksnw = getPaginasBewerkt(conn, bewerker, 1)
#    aantalbew, linksbew = getPaginasBewerkt(conn, bewerker, 0)
    if aantalnw == 0:
      print (bewerker, 'heeft alleen bewerkte artikelen aangepast')
      break
    text = f"Beste {bewerker},\n\n"
    text += f"Uit onderzoek is gebleken dat vele pagina's die door een gebruiker onder de naam {accountnaam} zijn aangemaakt, niet voldoen aan de normen die op de Nederlandse Wikipedia gelden met betrekking tot verifieerbaarheid. Tijdens een [[Wikipedia:Stemlokaal/Methodiek voor het verwijderen van artikelen van Torval-PeterKeijsers-Paolingstein (TPP)|recente stemming]] is besloten dat deze artikelen uit de hoofdnaamruimte zullen verdwijnen, tenzij iemand duidelijk aangeeft, voor 20 november 2023, dat het betreffende artikel gecontroleerd is, dat wil zeggen dat de feiten gecontroleerd zijn in onafhankelijke bronnen en dat alle opgegeven bronnen zorgvuldig aangeven wat deze worden toegedicht.\n"
    if aantalnw == 1:
      text += "Omdat jij een van deze artikelen in het verleden bewerkt hebt, willen we jou met dit bericht specifiek wijzen op dat artikel:\n"
    else:
      text += "Omdat jij meerdere van deze artikelen in het verleden bewerkt hebt, willen we jou met dit bericht wijzen op de volgende artikelen op deze lijst:\n"
    text += linksnw
    text += f"Als je vindt dat een artikel daadwerkelijk voldoet aan alle eisen, dan kan je dit aangeven op [[Gebruiker:RonnieV/Nalooplijst/{groep}|de nalooplijst]]. Gelieve dan ook het sjabloon bovenaan de pagina te verwijderen.\n\n"
    text += "Alvast bedankt, mede namens [[Gebruiker:Bertux|]],\n\n[[Gebruiker:RonnieV|RonnieV]] [[Overleg gebruiker:RonnieV|(overleg)]] ~~~~~\n"
    
    text += f"\n<small>Te plaatsen op {row['GOP']}</small>\n"
    PageTitle = f'Gebruiker:RonnieV/Nalooplijst/{groep}-meldingen'
    summary = f'Melding voor {bewerker} over artikelen van {accountnaam}'
    addsection(PageTitle, summary, text)
    if aantal > maxaantal:
      break;
    aantal += 1
  
def createdatabase(namedatabase):
  databasename = f'Nalooplijst {namedatabase}.db' 
  conn = sqlite3.connect(databasename)
  conn.row_factory = sqlite3.Row
  tabledefs.recreate_tabel_bewerkers(conn)
  tabledefs.recreate_tabel_bewerkte_paginas(conn)
  tabledefs.recreate_tabel_nieuwe_paginas(conn)
  tabledefs.recreate_tabel_paginabewerkers(conn)
  return (conn)
  
def main():
  conn = createdatabase(groep)
  for account in accounts:
    verzamelnieuw(conn, account)
  for account in accounts:
    verzamelbewerkt(conn, account)
  verwerkbewerkers(conn)
  maakartikellijst(conn)
  maakoverzichtbewerkers(conn)
  plaatssjabloon(conn)
  maakbewerkersteksten(conn)    
  
if __name__ == '__main__':
  main()
   