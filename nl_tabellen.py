def recreate_tabel_bewerkers(cur):
    tablenaam = 'bewerkers'
    tableprefix = tablenaam[0:5]
    cur.execute(f'DROP TABLE IF EXISTS `{tablenaam}`')
    cur.execute(f'CREATE TABLE `{tablenaam}` ( `naam` TEXT, `laatstebewerking` TEXT, `isanoniem` INTEGER, `isgeblokkeerd` INTEGER, `GOP` TEXT, `isbot` INTEGER, `isbotbewerkbaar` INTEGER )')
    cur.execute(f'CREATE UNIQUE INDEX `{tableprefix}_naam` ON `{tablenaam}` ( `naam` )')

def recreate_tabel_bewerkte_paginas(cur):
    tablenaam = 'editedpaginas'
    tableprefix = tablenaam[0:5]
    cur.execute(f'DROP TABLE IF EXISTS `{tablenaam}`')
    cur.execute(f'CREATE TABLE `{tablenaam}` ("titel" TEXT, "id" INTEGER, "orggrootte" INTEGER, "huidigegrootte" INTEGER, "laatstebewerking" TEXT, "aantalbewerkers" INTEGER, "aantalbewerkingen" INTEGER, "status" TEXT)')
    cur.execute(f'CREATE UNIQUE INDEX `{tableprefix}_naam` ON `{tablenaam}` ( `titel`)')
    
def recreate_tabel_nieuwe_paginas(cur):
    tablenaam = 'nieuwepaginas'
    tableprefix = tablenaam[0:5]
    cur.execute(f'DROP TABLE IF EXISTS `{tablenaam}`')
    cur.execute(f'CREATE TABLE `{tablenaam}` ("titel" TEXT, "id" INTEGER, "orggrootte" INTEGER, "huidigegrootte" INTEGER, "laatstebewerking" TEXT, "aantalbewerkers" INTEGER, "aantalbewerkingen" INTEGER, "status" TEXT)')
    cur.execute(f'CREATE UNIQUE INDEX `{tableprefix}_naam` ON `{tablenaam}` ( `titel`)')
    
def recreate_tabel_paginabewerkers(cur):
    tablenaam = 'paginabewerkers'
    tableprefix = tablenaam[0:5]
    cur.execute(f'DROP TABLE IF EXISTS `{tablenaam}`')
    cur.execute(f'CREATE TABLE `{tablenaam}` ("pagina" TEXT, "bewerker" TEXT, `aantal` INTEGER, `isnieuw` INTEGER)')
    cur.execute(f'CREATE INDEX `{tableprefix}_bewerkers` ON `{tablenaam}` ( `bewerker`, `pagina`, `isnieuw` )')
    
    
