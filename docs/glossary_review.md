# Glossary wording for review

Every tooltip definition used in the app, in English and Turkish. Source: `src/glossary.py` (this file is generated from it).
Rules followed: at most two short sentences, everyday words, an analogy where it helps, never more certain than the science allows.
Terms are shown in the app with a dotted underline; the definition appears on hover, keyboard focus or tap.

| Key | English | Definition (EN) | Turkish | Definition (TR) |
|---|---|---|---|---|
| `sar` | SAR | Synthetic Aperture Radar: a satellite sends microwave pulses and records the echoes, so it can image the ground through clouds, day or night. | SAR | Yapay Açıklıklı Radar: uydu mikrodalga darbeleri gönderip yankılarını kaydeder, böylece bulutların arasından, gece ya da gündüz görüntü alabilir. |
| `nisar` | NISAR | A NASA–ISRO radar satellite launched in 2025. It revisits the same places about every 12 days. | NISAR | NASA ile ISRO'nun 2025'te fırlatılan radar uydusu. Aynı yerlerin üzerinden yaklaşık 12 günde bir yeniden geçer. |
| `lband` | L-band | Radar waves about 24 cm long. They pass through leaves more easily than short waves, so they also respond to stems, branches and the ground below. | L-bant | Yaklaşık 24 cm boyunda radar dalgaları. Kısa dalgalardan daha kolay yaprakların arasından geçer, bu yüzden gövde, dal ve alttaki zemine de tepki verir. |
| `backscatter` | backscatter | The share of the radar signal that bounces back to the satellite. Like how bright a surface looks under a flashlight held next to your eye. | geri saçılım | Radar sinyalinin uyduya geri dönen kısmı. Gözünüzün yanında tuttuğunuz bir el fenerinin altında bir yüzeyin ne kadar parlak göründüğüne benzer. |
| `db` | dB | Decibels: a log scale for radar brightness. A drop of 3 dB means roughly half as much returned signal. | dB | Desibel: radar parlaklığı için logaritmik ölçek. 3 dB düşüş, dönen sinyalin kabaca yarıya inmesi demektir. |
| `hh` | HH | Radar sent and received with horizontal waves. Darker HH returns often mean a smooth surface such as calm water, but not always. | HH | Yatay dalgayla gönderilip yatay dalgayla alınan radar. Daha karanlık HH dönüşleri çoğu zaman sakin su gibi düz bir yüzeye işaret eder, ama her zaman değil. |
| `hv` | HV | Radar sent horizontally and received vertically. It is often stronger where leaves and branches scatter the wave in many directions. | HV | Yatay gönderilip dikey alınan radar. Yaprak ve dalların dalgayı birçok yöne saçtığı yerlerde çoğu zaman daha güçlüdür. |
| `polarization` | polarization | The direction in which the radar wave vibrates (horizontal or vertical). Comparing polarizations can hint at surface structure. | polarizasyon | Radar dalgasının titreşim yönü (yatay ya da dikey). Polarizasyonları karşılaştırmak yüzey yapısı hakkında ipucu verebilir. |
| `gcov` | GCOV | NISAR's map-ready radar brightness product (Level 2), already placed on a map grid and corrected for terrain. | GCOV | NISAR'ın haritaya hazır radar parlaklığı ürünü (Seviye 2); bir harita ızgarasına yerleştirilmiş ve araziye göre düzeltilmiştir. |
| `speckle` | speckle | Grainy noise that every radar image has, like the sparkle of a laser on a wall. Averaging neighbouring pixels reduces it. | benek gürültüsü | Her radar görüntüsünde bulunan taneli gürültü; duvardaki bir lazerin parıltısı gibi. Komşu pikselleri ortalamak onu azaltır. |
| `threshold` | threshold | A cut-off value chosen to sort pixels, for example "darker than −16 dB". It is a choice we made, not a law of nature. | eşik | Pikselleri ayırmak için seçilen sınır değer, örneğin "−16 dB'den karanlık". Doğa yasası değil, bizim yaptığımız bir seçimdir. |
| `change_map` | change map | A map of how radar brightness differs between two dates. It shows where something changed, not what changed. | değişim haritası | Radar parlaklığının iki tarih arasında nasıl farklılaştığını gösteren harita. Neyin değiştiğini değil, nerede bir şeyin değiştiğini gösterir. |
| `candidate` | candidate | A place flagged for a closer look because its radar signal changed a lot. It may or may not be a real surface change. | aday | Radar sinyali çok değiştiği için daha yakından bakılmak üzere işaretlenen yer. Gerçek bir yüzey değişimi olabilir ya da olmayabilir. |
| `compass` | Change Compass | Our way of describing a change by the direction HH and HV moved. It names patterns the change is consistent with, not causes. | Değişim Pusulası | Bir değişimi HH ve HV'nin hangi yöne gittiğine göre tarif etme yöntemimiz. Nedenleri değil, değişimin tutarlı olduğu desenleri adlandırır. |
| `ring` | ring comparison | Comparing a candidate with the land 50–150 m around it. If both changed alike, the change may not be local. | halka karşılaştırması | Bir adayı çevresindeki 50–150 m'lik alanla karşılaştırmak. İkisi de benzer değiştiyse değişim yerel olmayabilir. |
| `lodo` | leave-one-date-out | Repeating the check with one date removed each time. If the change disappears, it may rest on a single date. | bir tarihi dışarıda bırakma | Kontrolü her seferinde bir tarihi çıkararak tekrarlamak. Değişim kaybolursa tek bir tarihe dayanıyor olabilir. |
| `scene_change` | scene-wide change | The typical (median) change over the whole area. A large one may come from weather or processing rather than local events. | sahne geneli değişim | Tüm alandaki tipik (medyan) değişim. Büyükse yerel olaylardan çok hava koşulları ya da işlemeden kaynaklanabilir. |
| `noise_floor` | noise floor | The faintest signal the radar can tell apart from its own noise. Below it, changes may be meaningless; here it is not quantified. | gürültü tabanı | Radarın kendi gürültüsünden ayırt edebildiği en zayıf sinyal. Bunun altında değişimler anlamsız olabilir; burada sayısal olarak belirlenmedi. |
| `acquisition` | acquisition | One satellite pass that images the area: one date, one picture. | çekim | Alanı görüntüleyen tek bir uydu geçişi: bir tarih, bir görüntü. |
| `track_frame` | track/frame | Track is the orbit path; frame is the slice along it. Same track and frame means the same viewing geometry. | iz/çerçeve | İz yörünge yoludur; çerçeve bu yol boyunca bir dilimdir. Aynı iz ve çerçeve, aynı bakış geometrisi demektir. |
| `footprint` | footprint | The patch of ground an image or a region actually covers. | ayak izi | Bir görüntünün ya da bölgenin gerçekte kapladığı zemin parçası. |
| `valid_pixel` | valid pixel | A pixel with a usable measurement on the dates being compared. Missing or edge pixels are left out, never filled in. | geçerli piksel | Karşılaştırılan tarihlerde kullanılabilir ölçümü olan piksel. Eksik ya da kenar pikseller dışarıda bırakılır, asla doldurulmaz. |
| `reference` | reference data | Independent information (optical images, field visits, gauges) used to check a result. None matched these dates and places. | referans veri | Bir sonucu kontrol etmek için kullanılan bağımsız bilgi (optik görüntü, saha ziyareti, ölçüm istasyonu). Bu tarih ve yerlerle eşleşen yoktu. |
| `hypothesis` | hypothesis | A possible explanation that still needs checking. Everything this app suggests is a hypothesis. | hipotez | Hâlâ kontrol edilmesi gereken olası bir açıklama. Bu uygulamanın öne sürdüğü her şey bir hipotezdir. |
| `placebo` | placebo check | Repeating the same measurement on random places that were not picked out. It shows how unusual the picked place looks, not why it changed. | plasebo kontrolü | Aynı ölçümü seçilmemiş rastgele yerlerde tekrarlamak. Seçilen yerin ne kadar sıra dışı göründüğünü gösterir, neden değiştiğini değil. |
| `null_distribution` | null distribution | The spread of values that random places give. It is the yardstick the candidate is compared with. | sıfır dağılımı | Rastgele yerlerin verdiği değerlerin yayılımı. Adayın karşılaştırıldığı ölçüttür. |
| `exceedance` | exceedance fraction | The share of random places whose value was at least as extreme as the candidate's. Small means unusual here; it is not the chance that the change is real. | aşım oranı | Değeri en az aday kadar uç olan rastgele yerlerin payı. Küçükse burada sıra dışı demektir; değişimin gerçek olma olasılığı değildir. |

## Definitions I am less sure about

- **L-band** (`lband`): The ~24 cm wavelength is the nominal L-band value for NISAR; penetration depends strongly on vegetation density and moisture.
- **dB** (`db`): "3 dB ≈ half" is a rounded rule (10·log10(0.5) = −3.01 dB).
- **HV** (`hv`): HV is also sensitive to roughness and can be near the noise floor over water; "often" is deliberate.
- **GCOV** (`gcov`): GCOV is terrain-corrected (RTC gamma-0); "map-ready" simplifies the geocoding and calibration steps.
- **NISAR** (`nisar`): Launch year 2025 is from public mission information; the 12-day repeat is the nominal cycle.
- **Turkish technical terms**: "geri saçılım" (backscatter), "benek gürültüsü" (speckle), "çekim" (acquisition), "iz/çerçeve" (track/frame) and "ayak izi" (footprint) are the forms I chose; please check them against the terms your Turkish remote-sensing sources use.
- **Change Compass / Değişim Pusulası** is our own name, not a standard term.

## New terms for review (2026-11-15, placebo check)

`placebo`, `null_distribution`, `exceedance` were added for the placebo (null) check in the researcher workflow
(docs/PLACEBO_METHOD.md). Please check in particular: the Turkish statistical term "sıfır dağılımı" (null distribution) and
whether "aşım oranı" reads naturally for "exceedance fraction"; the English "it is not the chance that the change is real"
is meant to stop readers treating the fraction as a p-value or a probability.
