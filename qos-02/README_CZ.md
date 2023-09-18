# Cvičení QoS_2

## Náhodná veličina:
 ``` Jedná se o libovolnou veličinu, kterou je možné opakovaně měřit u různých objektů, v různých místech, v různých časech atd. Tyto hodnoty lze dále zpeacovat metodami teorie pravděpodobnosti nebo matematické statistiky.```
 
Např. hod kostou, čekání ve frontě... 

## Historie:
Abraham de Moivre byl v 18. století často nabádán, zda by nebyl schopen zkrátit dlouhé výpočty daných matematických úkolů své doby. Uvedeme si zde příklad výpočtu pravděpodobnosti - pokud 100 krát hodíme mincí, jaká je pravděpodobnost, že padne 40 krát nebo vícekrát hlava. Daný úkol by se dal vypočítat pomocí následujícího vzorce:

$$P(x) = \frac{N!}{x!(N-x)}\pi^{x}(1 - \pi)^{N-x}$$, 

kde x je počet hozených hlav (40), N je počet hodů (100), a $$\pi$$ je pravděpodobnost, že padne hlava (0,5). Takto bychom museli vždy spočítat pravděpodobnost, že padne hlava 40 krát, poté 41 krát, atd. a sečíst všechny tyto pravděpodobnosti dohromady. Dříve možnost počítačů a kalkulaček nebyla, a proto se obraceli právě na Moivra. Ten poznamenal, že jestli zvýší číslo hodu, tvar binomického rozdělení se přiblíží k hladké křivce. 
 ![Normální rozdělení](https://imgur.com/oROrqFm.png) 
 Aproximace binomického rozdělení normálním rozdělením
 [Cite]: [https://dspace5.zcu.cz/bitstream/11025/8166/1/BP%20Pavel%20Stanek.pdf]
 
 Rozdělení mohou být diskrétní i spojitá podle NV - tzn. spojitá NV = spojité rozdělení a naopak. Spojité rozdělní jsou definována vzorci, hustotou pravděpodobnosti, popř. distribuční funkcí.


## Rovnoměrné rozdělení:
```Rovnoměrné rozdělení je jedno z nejjednodušších rozdělení. Toto rozdělení má pro všechny hodnoty náhodné veličiny stejnou pravděpodobnost. Toto rozdělení má spojitá náhodná veličina X, jejíž realizace vyplňují interval konečné délky a mají stejnou možnost výskytu.```

 ![Rovnoměrné rozdělení](https://imgur.com/kIQp7u4.png) 
  [Cite]: [https://dspace5.zcu.cz/bitstream/11025/8166/1/BP%20Pavel%20Stanek.pdf]
  
 Např. jedná se o všechny jevy, které mají stejnou možnost výskytu (např. doba čekání na autobus, na výrobek u automatické linky apod.). 

## Exponeciální rozdělení:
```Toto rozdělení má spojitá náhodná veličina X, která představuje dobu čekání do nastoupení (poissonovského) náhodného jevu, nebo délku intervalu (časového nebo délkového) mezi takovými dvěma jevy (např. doba čekání na obsluhu, vzdálenost mezi dvěma poškozenými místy na silnici).``` 

``` Exponenciální rozdělení vyjadřuje rozdělení délky intervalu mezi náhodně se vyskytujícími událostmi, jejichž pravděpodobnost výskytu má Poissonovo rozdělení.``` 

Závisí na parametru $$\lambda$$, což je převrácená hodnota střední hodnoty doby čekání do nastoupení sledovaného jevu.

 ![Exponenciální rozdělení](https://imgur.com/BDnq5lg.png) 
   [Cite]: [https://www.geogebra.org/m/v3Sn277h]

### Poissonův proces:
```Nejužívanější model vstupního toku. Model Poissonova toku používáme prakticky vždy, když zákazníci (příchozí volání, datové pakety, …) pocházejí z velké množiny vzájemně nezávislých uživatelů.```

**Příklad:**
K telefonnímu automatu přijde za 1 hodinu v průměru 15 zákazníků. Každý hovor trvá v průměru 3 minuty. Je nutno pořídit další automat, jestliže nechceme, aby zákazníci čekali déle než 3 minuty? Příchod zákazníků se řídí Poissonovým procesem, doba telefonování je náhodná a řídí se exponenciálním rozdělením.


## Normální rozdělení:
```Normální rozdělení hraje ze spojitých rozdělení největší roli v teorii pravděpodobnosti a statistice a řídí se jím (alespoň “přibližně“) více náhodných veličin (proměnné, jejichž hodnoty jsou jednoznačně určeny výsledkem náhodného pokusu). ```

Jako příklad můžeme uvést velikost náhodných chyb vznikajících při jakékoliv činnosti (např. při výrobě součástek odchylky v rozměrech od předem stanovené normy), dále u většiny měřitelných charakteristik biologických statistických jednotek (u hospodářských zvířat, při pokusných buněčných kulturách, ale také u lidí, aj.). 

Vezmeme-li to úplně konkrétně, normální rozdělení nalezneme např. u hmotnosti, IQ, výšky, aj.

 ![Normální rozdělení](https://imgur.com/dERk4DR.png) 
   [Cite]: [http://www.statsoft.cz/file1/PDF/newsletter/2012_11_12_StatSoft_Rozdeleni_nahodne_veliciny.pdf]

## Základy SHO:
```Systém hromadné obsluhy (SHO) je možno definovat jako systém tvořený jednou nebo více paralelními linkami (kanály) pro obsluhu přicházejících požadavků (zákazníků).```

Základními prvky systémů hromadné obsluhy (dále ve zkratce SHO) jsou tedy:
    **1. Požadavky** (zákazníci)
    **2. Obsluhovací linky** (kanály obsluhy)
    
 SHO pracuje tak, že k nějakému zařízení (jedna nebo více paralelních linek tobsluhy) přicházejí požadavky (zákazníci) vyžadující obsluhu.
  Každý SHO má konečný počet obsluhovacích linek - toto číslo určuje maximální počet paralelně (současně) obsluhovaných požadavků – tzv. kapacitu obsluhy.
Je-li volné místo pro obsluhu (volná obsluhovací linka), požadavek se přijme a ihned se zahájí jeho obsluha.

#### Klasifikace SHO:
- je nutno popsat zákonitostí vzniku a příchodu požadavku do systému, tzv.
vstupní tok
- je nutno popsat počet obslužných linek a popsat průběh vlastní obsluhy
- je nutno popsat průběh obsloužení zákazníků v případě, že nemohou být
hned obslouženi (frontový režim)
- Nejpoužívanější je tzv. Kendallova klasifikace SHO
vyjadřuje přehledně typ SHO podle jeho základních charakteristik

**Zakódování ve tvaru A/B/n (zkrácená verze)**
• typ procesu popisujícího příchod požadavku k obsluze (**A**)
• typ rozdělení doby obsluhy (**B**)
• počet linek obsluhy (**n**)

#### Základní OS - typ M/M/1:
• Nejjednodušší případ exponenciálního modelu,
• jeden obslužný kanál (obslužné zařízení),
• intervaly mezi příchody požadavků i dob obsluhy mají exponenciální rozdělení, velikost fronty není omezena, počet příchozích požadavků je neomezený, všechny požadavky trpělivě čekají ve frontě na obsluhu, i když nedostačuje kapacita obslužného zařízení (FIFO fronta).


