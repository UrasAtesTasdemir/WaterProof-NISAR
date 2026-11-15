"""Plain-language glossary with inline tooltips.

`term('HH')` returns an inline, dotted-underlined term whose definition shows on
hover, keyboard focus or tap. In translated strings, `[[key]]` or
`[[key|shown words]]` marks a term; `md()` turns the markers into tooltips.
Definitions: at most two short sentences, everyday words, never more certain
than the science allows. All wording is listed in docs/glossary_review.md.
"""
import html
import re

from src.i18n import current_lang

# key: {lang: (label, definition)}
TERMS = {
    'sar': {
        'en': ('SAR', 'Synthetic Aperture Radar: a satellite sends microwave pulses and records the echoes, so it can image the ground through clouds, day or night.'),
        'tr': ('SAR', 'Yapay Açıklıklı Radar: uydu mikrodalga darbeleri gönderip yankılarını kaydeder, böylece bulutların arasından, gece ya da gündüz görüntü alabilir.')},
    'nisar': {
        'en': ('NISAR', 'A NASA–ISRO radar satellite launched in 2025. It revisits the same places about every 12 days.'),
        'tr': ('NISAR', "NASA ile ISRO'nun 2025'te fırlatılan radar uydusu. Aynı yerlerin üzerinden yaklaşık 12 günde bir yeniden geçer.")},
    'lband': {
        'en': ('L-band', 'Radar waves about 24 cm long. They pass through leaves more easily than short waves, so they also respond to stems, branches and the ground below.'),
        'tr': ('L-bant', 'Yaklaşık 24 cm boyunda radar dalgaları. Kısa dalgalardan daha kolay yaprakların arasından geçer, bu yüzden gövde, dal ve alttaki zemine de tepki verir.')},
    'backscatter': {
        'en': ('backscatter', 'The share of the radar signal that bounces back to the satellite. Like how bright a surface looks under a flashlight held next to your eye.'),
        'tr': ('geri saçılım', 'Radar sinyalinin uyduya geri dönen kısmı. Gözünüzün yanında tuttuğunuz bir el fenerinin altında bir yüzeyin ne kadar parlak göründüğüne benzer.')},
    'db': {
        'en': ('dB', 'Decibels: a log scale for radar brightness. A drop of 3 dB means roughly half as much returned signal.'),
        'tr': ('dB', 'Desibel: radar parlaklığı için logaritmik ölçek. 3 dB düşüş, dönen sinyalin kabaca yarıya inmesi demektir.')},
    'hh': {
        'en': ('HH', 'Radar sent and received with horizontal waves. Darker HH returns often mean a smooth surface such as calm water, but not always.'),
        'tr': ('HH', 'Yatay dalgayla gönderilip yatay dalgayla alınan radar. Daha karanlık HH dönüşleri çoğu zaman sakin su gibi düz bir yüzeye işaret eder, ama her zaman değil.')},
    'hv': {
        'en': ('HV', 'Radar sent horizontally and received vertically. It is often stronger where leaves and branches scatter the wave in many directions.'),
        'tr': ('HV', 'Yatay gönderilip dikey alınan radar. Yaprak ve dalların dalgayı birçok yöne saçtığı yerlerde çoğu zaman daha güçlüdür.')},
    'polarization': {
        'en': ('polarization', 'The direction in which the radar wave vibrates (horizontal or vertical). Comparing polarizations can hint at surface structure.'),
        'tr': ('polarizasyon', 'Radar dalgasının titreşim yönü (yatay ya da dikey). Polarizasyonları karşılaştırmak yüzey yapısı hakkında ipucu verebilir.')},
    'gcov': {
        'en': ('GCOV', "NISAR's map-ready radar brightness product (Level 2), already placed on a map grid and corrected for terrain."),
        'tr': ('GCOV', "NISAR'ın haritaya hazır radar parlaklığı ürünü (Seviye 2); bir harita ızgarasına yerleştirilmiş ve araziye göre düzeltilmiştir.")},
    'speckle': {
        'en': ('speckle', 'Grainy noise that every radar image has, like the sparkle of a laser on a wall. Averaging neighbouring pixels reduces it.'),
        'tr': ('benek gürültüsü', 'Her radar görüntüsünde bulunan taneli gürültü; duvardaki bir lazerin parıltısı gibi. Komşu pikselleri ortalamak onu azaltır.')},
    'threshold': {
        'en': ('threshold', 'A cut-off value chosen to sort pixels, for example "darker than −16 dB". It is a choice we made, not a law of nature.'),
        'tr': ('eşik', 'Pikselleri ayırmak için seçilen sınır değer, örneğin "−16 dB\'den karanlık". Doğa yasası değil, bizim yaptığımız bir seçimdir.')},
    'change_map': {
        'en': ('change map', 'A map of how radar brightness differs between two dates. It shows where something changed, not what changed.'),
        'tr': ('değişim haritası', 'Radar parlaklığının iki tarih arasında nasıl farklılaştığını gösteren harita. Neyin değiştiğini değil, nerede bir şeyin değiştiğini gösterir.')},
    'candidate': {
        'en': ('candidate', 'A place flagged for a closer look because its radar signal changed a lot. It may or may not be a real surface change.'),
        'tr': ('aday', 'Radar sinyali çok değiştiği için daha yakından bakılmak üzere işaretlenen yer. Gerçek bir yüzey değişimi olabilir ya da olmayabilir.')},
    'compass': {
        'en': ('Change Compass', 'Our way of describing a change by the direction HH and HV moved. It names patterns the change is consistent with, not causes.'),
        'tr': ('Değişim Pusulası', 'Bir değişimi HH ve HV\'nin hangi yöne gittiğine göre tarif etme yöntemimiz. Nedenleri değil, değişimin tutarlı olduğu desenleri adlandırır.')},
    'ring': {
        'en': ('ring comparison', 'Comparing a candidate with the land 50–150 m around it. If both changed alike, the change may not be local.'),
        'tr': ('halka karşılaştırması', 'Bir adayı çevresindeki 50–150 m\'lik alanla karşılaştırmak. İkisi de benzer değiştiyse değişim yerel olmayabilir.')},
    'lodo': {
        'en': ('leave-one-date-out', 'Repeating the check with one date removed each time. If the change disappears, it may rest on a single date.'),
        'tr': ('bir tarihi dışarıda bırakma', 'Kontrolü her seferinde bir tarihi çıkararak tekrarlamak. Değişim kaybolursa tek bir tarihe dayanıyor olabilir.')},
    'scene_change': {
        'en': ('scene-wide change', 'The typical (median) change over the whole area. A large one may come from weather or processing rather than local events.'),
        'tr': ('sahne geneli değişim', 'Tüm alandaki tipik (medyan) değişim. Büyükse yerel olaylardan çok hava koşulları ya da işlemeden kaynaklanabilir.')},
    'noise_floor': {
        'en': ('noise floor', 'The faintest signal the radar can tell apart from its own noise. Below it, changes may be meaningless; here it is not quantified.'),
        'tr': ('gürültü tabanı', 'Radarın kendi gürültüsünden ayırt edebildiği en zayıf sinyal. Bunun altında değişimler anlamsız olabilir; burada sayısal olarak belirlenmedi.')},
    'acquisition': {
        'en': ('acquisition', 'One satellite pass that images the area: one date, one picture.'),
        'tr': ('çekim', 'Alanı görüntüleyen tek bir uydu geçişi: bir tarih, bir görüntü.')},
    'track_frame': {
        'en': ('track/frame', 'Track is the orbit path; frame is the slice along it. Same track and frame means the same viewing geometry.'),
        'tr': ('iz/çerçeve', 'İz yörünge yoludur; çerçeve bu yol boyunca bir dilimdir. Aynı iz ve çerçeve, aynı bakış geometrisi demektir.')},
    'footprint': {
        'en': ('footprint', 'The patch of ground an image or a region actually covers.'),
        'tr': ('ayak izi', 'Bir görüntünün ya da bölgenin gerçekte kapladığı zemin parçası.')},
    'valid_pixel': {
        'en': ('valid pixel', 'A pixel with a usable measurement on the dates being compared. Missing or edge pixels are left out, never filled in.'),
        'tr': ('geçerli piksel', 'Karşılaştırılan tarihlerde kullanılabilir ölçümü olan piksel. Eksik ya da kenar pikseller dışarıda bırakılır, asla doldurulmaz.')},
    'reference': {
        'en': ('reference data', 'Independent information (optical images, field visits, gauges) used to check a result. None matched these dates and places.'),
        'tr': ('referans veri', 'Bir sonucu kontrol etmek için kullanılan bağımsız bilgi (optik görüntü, saha ziyareti, ölçüm istasyonu). Bu tarih ve yerlerle eşleşen yoktu.')},
    'placebo': {
        'en': ('placebo check', 'Repeating the same measurement on random places that were not picked out. It shows how unusual the picked place looks, not why it changed.'),
        'tr': ('plasebo kontrolü', 'Aynı ölçümü seçilmemiş rastgele yerlerde tekrarlamak. Seçilen yerin ne kadar sıra dışı göründüğünü gösterir, neden değiştiğini değil.')},
    'null_distribution': {
        'en': ('null distribution', 'The spread of values that random places give. It is the yardstick the candidate is compared with.'),
        'tr': ('sıfır dağılımı', 'Rastgele yerlerin verdiği değerlerin yayılımı. Adayın karşılaştırıldığı ölçüttür.')},
    'exceedance': {
        'en': ('exceedance fraction', "The share of random places whose value was at least as extreme as the candidate's. Small means unusual here; it is not the chance that the change is real."),
        'tr': ('aşım oranı', 'Değeri en az aday kadar uç olan rastgele yerlerin payı. Küçükse burada sıra dışı demektir; değişimin gerçek olma olasılığı değildir.')},
    'hypothesis': {
        'en': ('hypothesis', 'A possible explanation that still needs checking. Everything this app suggests is a hypothesis.'),
        'tr': ('hipotez', 'Hâlâ kontrol edilmesi gereken olası bir açıklama. Bu uygulamanın öne sürdüğü her şey bir hipotezdir.')},
}

# Definitions I am least sure about, flagged for the team's review.
UNSURE = {
    'lband': 'The ~24 cm wavelength is the nominal L-band value for NISAR; penetration depends strongly on vegetation density and moisture.',
    'db': '"3 dB ≈ half" is a rounded rule (10·log10(0.5) = −3.01 dB).',
    'hv': 'HV is also sensitive to roughness and can be near the noise floor over water; "often" is deliberate.',
    'gcov': 'GCOV is terrain-corrected (RTC gamma-0); "map-ready" simplifies the geocoding and calibration steps.',
    'nisar': 'Launch year 2025 is from public mission information; the 12-day repeat is the nominal cycle.',
}


def label(key, lang=None):
    return TERMS[key][lang or current_lang()][0]


def definition(key, lang=None):
    return TERMS[key][lang or current_lang()][1]


def term(key, text=None, lang=None):
    """Inline HTML: dotted term with a tooltip (hover, focus or tap)."""
    lang = lang or current_lang()
    shown = html.escape(text or label(key, lang))
    tip = html.escape(definition(key, lang))
    return (f'<span class="cc-term" tabindex="0" aria-label="{shown}: {tip}">{shown}'
            f'<span class="cc-tip" role="tooltip">{tip}</span></span>')


MARKER = re.compile(r'\[\[(\w+)(?:\|([^\]]+))?\]\]')


def md(text, lang=None):
    """Replace [[key]] / [[key|words]] markers with tooltip terms."""
    return MARKER.sub(lambda m: term(m.group(1), m.group(2), lang), text)


def strip(text):
    """Plain text without markers (for places that cannot hold HTML)."""
    return MARKER.sub(lambda m: m.group(2) or label(m.group(1)), text)
