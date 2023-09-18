# Cvičení QoS_1

## Signál:
Je to fyzikální vyjádření zprávy, nebo matematický model popisující zprávu.
## Rozdělení signálů:
**Spojitý (ANALOGOVÝ)**
 ```Spojitá, nebo po částech spojitá funkce spojité nezávislé proměnné.```
 ![Spojitý signál](https://i.imgur.com/ULydS4L.png)
 [Cite]: [https://owncloud.cesnet.cz/index.php/s/AAudTKwsECmibzN#pdfviewer]

**Diskrétní signál** 
    ```Signál diskretizovaný v nezávislé proměnné (tzn. Df = diskrétní množina bodů).```
     ![Diskrétní signál](https://imgur.com/rGmu74E.png)
      [Cite]: [https://owncloud.cesnet.cz/index.php/s/AAudTKwsECmibzN#pdfviewer]
      
**Digitální signál** 
    ```Signál diskretizovaný v nezávislé proměnné a kvantizovaný v úrovni.```
    ![Digitální signál](https://imgur.com/NVjmFY2.png)
     [Cite]: [https://owncloud.cesnet.cz/index.php/s/AAudTKwsECmibzN#pdfviewer]
     
**Schodovitý signál** 
```Diskretizovaný v Hf, ale po částech spojitý v čase.```
    ![Schodovitý signál](https://imgur.com/8sogZbR.png)
     [Cite]: [https://owncloud.cesnet.cz/index.php/s/AAudTKwsECmibzN#pdfviewer]
     
**Deterministický signál** 
```V každém okamžiku můžeme určit jeho hodnotu, máme jeho matematický popis (sin(x, ...)).```
**Stochastický signál**
```Nedokážeme v každém okamžiku jednoznačne určit jejich hodnotu pro popis se používají pravděpodobnostní nebo statistické metody.```

## PCM (Pulzně kódová modulace):    
[comment]: [http://fyzika.jreichl.com/main.article/view/1355-digitalizace-analogoveho-signalu]
**Vzorkování:** 
Ze spojitého analogového signálu, který reprezentuje zaznamenaný zvuk nebo obraz, vybereme omezený počet vzorků. 
Výsledkem je konečný počet analogových vzorků, které jsou snímány s periodou T_vz dané vzorkovací frekvencí vzorkování.
![Vzorkování](https://imgur.com/YRZZfpe.png)

**Kvantování:**
jedná se o úrovňovou diskretizaci (tj. zaokrouhlení skutečné hodnoty na předem vybrané hodnoty). 
Výsledkem této operace je konečný počet vzorků (ten byl k dispozici už po vzorkování) s konečným počtem jejich hodnot, které jsou vyjádřeny určitým binárním kódem.
![Kvantování](https://imgur.com/zTaDkFo.png)

**Kódování:**
získaný jednoduchý binární kód nahradíme kódem, který je vhodnější pro další zpracování.
![Kódování](https://imgur.com/0cPr20m.png)
> **TIP:** Vzorkovací obvod vnáší chybu ve formě (překrytí) aliasingu, kvantovací obvod ve formě kvantizačního šumu.
 ###  Podmínky pro správné vzorkování (Shannon-Kotelnikův teorém):
 
 Platí zde vzorkovací teorém, který říká, že signál je popsatelný pouze tehdy, pokud je ohraničený kmitočtem $$f_{max}$$, a je-li $$f_{vz}$$ => 2 * $$f_{max}$$, tzn. to znamená, že vzorkovací frekvence musí být, alespoň dvakrát větší než je nejvyšší kmitočet signálu.  
 
  Využití např. pro DPS (Digital Signaling Processor) - umožńuje frekvenční úpravu, úpravu hlasitosti, popř. kompresi signálu. Např. u MP3 - analogový signál se převede na digitální signál, dále do DSP a ten vykoná kódování signálu, zpátky se pomocí DSP dekóduje (MPEG-1/2 pro kompresi audia).

$$T[s]$$ (Perioda) - označuje ve fyzice fyzikální veličinu, která udává dobu trvání jednoho opakování periodického děje
    $$f[Hz = s^{-1}]$$ (Frekvence neboli kmitočet) - udává počet period za jednotku času

### Gaussovský šum:
Gaussovský šum představují náhodné změny v intenzitě odpovídající gaussovskému (normálnímu) rozdělení.

![Gauss](https://imgur.com/tN6l2ad.png)
[Cite]: [https://en.wikipedia.org/wiki/Gaussian_noise]

$$P(x) = \frac{1}{{\sigma \sqrt {2\pi } }}e^{{{-  {(z - \mu )}^2 } \mathord{/ {\vphantom {{ - ( {x - \mu }^2 } {2\sigma ^2 }}}} {(2\sigma^2)}}}$$

Směrodatná odchylka ($$\sigma$$), značená řeckým písmenem σ, je v teorii pravděpodobnosti a statistice často používanou mírou statistické variability. 
Jedná se o odmocninu z rozptylu náhodné veličiny. Výběrová směrodatná odchylka je charakteristikou proměnlivosti (variability) statistického souboru.

![Gauss](https://imgur.com/X1hUPFG.png)
[Cite]: [http://people.ciirc.cvut.cz/~hlavac/TeachPresEn/11ImageProc/13FourierFiltrationEn.pdf]

### Kapacita kanálu (Shannonův vzorec):
**C = B * log_2 (1+ S/N)**
**C:** kapacita kanál (bit/s)
**B:** šířka kanálu (Hz)
**S:** Výkon signálu
**N:** výkon šumu (W)
**S/N:** poměr signálu a šumu

### Frekvence:
**Telefonní kanál:**  ```3100 Hz```  (pásmo 300 - 3400 Hz)
**WiFi 802.11n:** ```20 MhZ``` (2.4 GHz)/```40 MhZ``` (5 GHz), (kanál)
**5G:** ```100 MhZ```  (2300 MhZ)
**5G mmWave:** ```500/1000/2000 MhZ``` (28/38/72 GhZ)
**MIMO:** ```800 MhZ``` (kanál), 2x2, 4x4, 8x8, 16x16, 32x32, and 64x64 (antény) - 28/73 GhZ
Čísla odkazují na počet streamů, se kterými router pracuje. Směrovač ve variantě 2x2 má tedy dvě antény, které se využívají pro 2 simultánní streamy. 

