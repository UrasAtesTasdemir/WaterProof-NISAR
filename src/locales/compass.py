"""Change Compass: pattern labels (built from src.change_compass.LABELS for English), reasons and page text."""
from src.change_compass import LABELS, COMMON_ALTERNATIVES

EN = {}
for _key, _info in LABELS.items():
    for _field in ('title', 'rule', 'physics', 'caution'):
        EN[f'compass.{_key}.{_field}'] = _info[_field]
    for _i, _alt in enumerate(_info['alternatives']):
        EN[f'compass.{_key}.alt{_i}'] = _alt
for _i, _alt in enumerate(COMMON_ALTERNATIVES):
    EN[f'compass.common.alt{_i}'] = _alt

EN.update({
    'compass.reason.pixels': 'only {pixels} valid pixels (< {minimum})',
    'compass.reason.dead_zone': 'median change vector ({h}, {v}) dB is inside the ±{tau} dB dead zone',
    'compass.reason.disagree': 'the middle 50% of pixels disagree in direction on both HH and HV',
    'compass.reason.mixed': 'mixed directions ({h} dB HH, {v} dB HV) without a single reading',
    'compass.reason.rule': 'median ΔHH {h} dB, median ΔHV {v} dB; rule: {rule}',
    'compass.sector.dead': 'inside dead zone',
    'compass.sector.mixed': 'mixed directions',
    'compass.card.raw': 'Raw medians',
    'compass.card.relative': 'Relative to scene-wide median',
    'compass.col.reference': 'Reference',
    'compass.col.pattern': 'Pattern',
    'compass.col.why': 'Why',
    'compass.card.disagree': '⚠️ **The two references give different readings.** The unexplained [[scene_change]] '
                             '(ΔHH {dhh} dB, ΔHV {dhv} dB) is large enough to change the pattern, so neither reading should be used on its own.',
    'compass.card.alternatives': '**Other explanations this radar pair cannot rule out:**',
    'compass.card.caution': 'Caution: {caution} Patterns are descriptive and not validated for this site.',
    'compass.title': 'Change Compass',
    'compass.intro': '**Which change pattern is this region consistent with?** Compare how [[hh]] (co-pol) and [[hv]] (cross-pol) '
                     'changed inside a region. The direction maps to a descriptive *pattern* ([[compass]]), shown with its numbers and the '
                     'other explanations it cannot rule out.',
    'compass.warning': 'Descriptive patterns only. The mapping follows typical L-band behaviour from the literature; it is NOT '
                       'validated for this site and does not show water, flooding or land-cover change.',
    'compass.spinner': 'Verifying cached HH/HV change…',
    'compass.error': 'Cached HH/HV change could not be verified ({error}). Run `python scripts/process_hv_compass.py` locally '
                     '(offline; uses cached real data). No download was attempted.',
    'compass.context': 'Louisiana case · NISAR L2 GCOV frequency A · {first} → {second} · {pixels} common valid 10 m pixels · '
                       'same 3×3 linear-power filter as the case study',
    'compass.region': 'Region',
    'compass.mode.saved': 'Saved region',
    'compass.mode.rectangle': 'Rectangle',
    'compass.saved_region': 'Saved region (real masks on the same grid)',
    'compass.whole_aoi': 'Whole common AOI',
    'compass.baseline_note': 'Baseline classes are the saved −16 dB / 3 dB case-study output for this same pair.',
    'compass.investigation_note': 'Investigation regions come from the six-date HH Investigation Explorer; here they are read for this pair only.',
    'compass.cols': 'West → east extent (% of AOI width)',
    'compass.rows': 'North → south extent (% of AOI height)',
    'compass.bad_rectangle': 'That rectangle cannot be used ({error}). Choose a start and end between 0 and 100%.',
    'compass.widened': 'The rectangle was widened to at least 1% so it contains pixels.',
    'compass.dead_zone': 'Dead zone τ (dB)',
    'compass.dead_zone_help': 'Median change vectors with both |ΔHH| and |ΔHV| below τ are inconclusive. Default 1.5 dB '
                              'exceeds the unexplained scene-wide median HH change (−1.39 dB); it is not a calibrated noise level.',
    'compass.metric.pixels': 'Valid pixels in region',
    'compass.metric.area': 'Area',
    'compass.metric.dhh': 'Median ΔHH',
    'compass.metric.dhv': 'Median ΔHV',
    'compass.iqr': 'IQR ΔHH {hh_lo}…{hh_hi} dB · IQR ΔHV {hv_lo}…{hv_hi} dB · scene-wide medians ΔHH {shh} dB, ΔHV {shv} dB. '
                   'Pixels are spatially dependent; counts are not independent samples.',
    'compass.hv_dark': 'HV is very dark here (region median {d0} / {d1} dB vs scene {pct}th percentile {s0} / {s1} dB). HV may be '
                       'near the [[noise_floor]], which was not quantified, so the HV change is weak evidence in this region.',
    'compass.hv_neutral': 'HV is above the scene {pct}th percentile on both dates. The HV [[noise_floor]] is not quantified '
                          '(product noise layers are in DN² without a verified conversion), so this is neutral, not support.',
    'compass.no_pixels': 'The selected region has no valid pixels. Choose a larger rectangle or another region.',
    'compass.spread_title': "**Where the region's pixels fall** (same direction rules, per pixel)",
    'compass.col.share': 'Share of pixels',
    'compass.col.sector': 'Direction sector',
    'compass.spread_note': 'A view of spread, not a per-pixel classification. A wide spread across sectors weakens any single reading.',
    'compass.fig.pixels_log': 'Pixels per cell (log)',
    'compass.fig.region_pixels': 'Region pixels',
    'compass.fig.dead_zone': 'Dead zone ±{tau} dB → inconclusive',
    'compass.fig.corner_smooth': 'both darker:\nconsistent with a\nsmoother surface',
    'compass.fig.corner_hh': 'HH up, HV not up:\nHH-dominated\nbrightening',
    'compass.fig.corner_volume': 'HV up: more volume\nscattering or roughness',
    'compass.fig.bottom': 'HV down, HH steady:\nreduced volume scattering',
    'compass.fig.scene': 'Scene-wide median ({h}, {v}) dB',
    'compass.fig.median': 'Region median ({h}, {v}) dB, IQR bars',
    'compass.fig.minus_scene': ' − scene median',
    'compass.fig.xlabel': 'ΔHH (dB){suffix}  ·  after − before',
    'compass.fig.ylabel': 'ΔHV (dB){suffix}',
    'compass.loc.title': 'Region (orange) on ΔHH · {pair}',
    'compass.loc.xlabel': 'UTM 15N easting (m)',
    'compass.how': 'How the Compass reads a region',
    'compass.how_text': 'Rules on the region\'s median change vector (raw and relative to the scene-wide median), with dead zone τ: '
                        '{rules}. If the two references give different patterns, the result is "Reading depends on the reference". '
                        'Basis: general L-band scattering behaviour (smooth surfaces darken HH and HV, double bounce brightens HH, '
                        'HV tracks volume scattering). See docs/CHANGE_COMPASS_METHOD.md.',
    'compass.alt_heading': 'Other explanations',
})

TR = {
    'compass.smoother_surface.title': 'Daha düz bir yüzeyle tutarlı desen (HH ve HV ikisi de daha karanlık)',
    'compass.smoother_surface.rule': 'medyan ΔHH ≤ −τ ve medyan ΔHV ≤ −τ/2',
    'compass.smoother_surface.physics': 'Sakin açık su gibi daha düz bir yüzey enerjiyi algılayıcıdan uzağa yansıtır ve hem eş-polarizasyon (HH) '
                                        'hem çapraz-polarizasyon (HV) dönüşlerini düşürebilir.',
    'compass.smoother_surface.caution': 'Tek başına su ya da taşkın kanıtı değildir.',
    'compass.smoother_surface.alt0': 'Toprağın ya da bitki örtüsünün kuruması',
    'compass.smoother_surface.alt1': 'Mevcut su üzerinde rüzgârın sakinleşmesi',
    'compass.smoother_surface.alt2': 'Bitki hacminin azalması',
    'compass.hh_darkening.title': 'HH daha karanlık, HV kabaca değişmemiş',
    'compass.hh_darkening.rule': 'medyan ΔHH ≤ −τ ve |medyan ΔHV| < τ/2',
    'compass.hh_darkening.physics': 'HH enerji kaybetti ama HV pek değişmedi. HV\'de zaten karanlık olan bir yüzeyin düzleşmesi ya da '
                                    'esas olarak eş-polarizasyon kanalını etkileyen bir değişim bunu üretebilir.',
    'compass.hh_darkening.caution': 'HV çok karanlık olduğunda HV değişimi az bilgi taşır; HV karanlık seviye uyarısına bakın.',
    'compass.hh_darkening.alt0': 'HV gürültü tabanına yakın, bu yüzden daha fazla düşemiyor',
    'compass.hh_darkening.alt1': 'Toprağın kuruması (HH üzerinde daha güçlü etki)',
    'compass.hh_darkening.alt2': 'HV\'nin zaten çok düşük olduğu daha sakin bir su yüzeyi',
    'compass.hh_brightening.title': 'HH ağırlıklı parlaklaşmayla tutarlı desen',
    'compass.hh_brightening.rule': 'medyan ΔHH ≥ +τ ve medyan ΔHV < +τ',
    'compass.hh_brightening.physics': 'L-bantta, su yüzeyinden çıkan bitkilerin altındaki ya da yapıların yanındaki su, HH\'yi HV\'den çok daha '
                                      'fazla parlatan çift sekmeli bir dönüş ekleyebilir.',
    'compass.hh_brightening.caution': 'Tek başına su basmış bitki örtüsünün kanıtı değildir.',
    'compass.hh_brightening.alt0': 'Daha ıslak toprak',
    'compass.hh_brightening.alt1': 'Sıra ya da yapı yöneliminin radara göre konumu',
    'compass.hh_brightening.alt2': 'Daha pürüzlü yüzey',
    'compass.volume_loss.title': 'Azalmış hacim saçılımıyla tutarlı desen (HV daha karanlık, HH sabit)',
    'compass.volume_loss.rule': 'medyan ΔHV ≤ −τ ve medyan ΔHH > −τ',
    'compass.volume_loss.physics': 'HV\'ye bitki örtüsündeki hacim saçılımı hâkimdir; HH az değişirken HV\'nin belirgin düşmesi, azalan bitki '
                                   'hacminin (ör. hasat, yaprak dökümü, açma) tipik bir işaretidir.',
    'compass.volume_loss.caution': 'Hiçbir arazi örtüsü değişimi kanıtlanmış değildir.',
    'compass.volume_loss.alt0': 'Bitki örtüsünün kuruması',
    'compass.volume_loss.alt1': 'Rüzgârın bitki örtüsünü hareket ettirmesi',
    'compass.volume_loss.alt2': 'Karanlık alanlarda HV gürültüsü',
    'compass.volume_gain.title': 'Daha fazla hacim saçılımı ya da pürüzlülükle tutarlı desen (HV daha parlak)',
    'compass.volume_gain.rule': 'medyan ΔHV ≥ +τ',
    'compass.volume_gain.physics': 'HV\'nin (çoğu zaman HH ile birlikte) yükselmesi, daha fazla hacim saçılımının ya da daha pürüzlü / ıslak '
                                   'yüzeylerin tipik bir işaretidir.',
    'compass.volume_gain.caution': 'Bu deseni birçok farklı süreç üretir; tek bir nedeni belirlemez.',
    'compass.volume_gain.alt0': 'Bitki büyümesi',
    'compass.volume_gain.alt1': 'Islanma',
    'compass.volume_gain.alt2': 'Toprak işleme ya da rüzgârla pürüzlenme',
    'compass.inconclusive.title': 'Belirgin desen yok (sonuçsuz)',
    'compass.inconclusive.rule': 'piksel sayısı çok az, ±τ ölü bölgenin içinde, pikseller anlaşmıyor ya da yönler karışık',
    'compass.inconclusive.physics': 'Değişim vektörü çok küçük, çok dağınık ya da tek bir ortak fiziksel okuması olmayan bir yönü gösteriyor.',
    'compass.inconclusive.caution': 'Sonuçsuz geçerli bir cevaptır: bu radar çifti tek başına burada bir deseni desteklemiyor.',
    'compass.reference_dependent.title': 'Okuma referansa bağlı',
    'compass.reference_dependent.rule': 'ham medyan ve sahne medyanına göreli okumalar farklı',
    'compass.reference_dependent.physics': 'Açıklanamayan sahne geneli medyan değişim çıkarıldığında desen değişiyor; bu yüzden bölgeye özgü bir '
                                           'şeyden çok o sahne geneli kaymadan kaynaklanıyor olabilir.',
    'compass.reference_dependent.caution': 'Hiçbir okuma tek başına kullanılmamalı; ikisi de sayılarıyla birlikte gösterilir.',
    'compass.reference_dependent.alt0': 'Kalibrasyon, nem ya da rüzgârdan kaynaklanan sahne geneli kayma',
    'compass.reference_dependent.alt1': 'Kaymayla benzer büyüklükte yerel bir değişim',
    'compass.common.alt0': 'Toprak ya da bitki örtüsü neminde değişim (ıslanma geri saçılımı artırır, kuruma azaltır)',
    'compass.common.alt1': 'Açık su üzerindeki rüzgâr dahil yüzey pürüzlülüğünde değişim',
    'compass.common.alt2': 'Bitki büyümesi, hasat, yaşlanma ya da yatma',
    'compass.common.alt3': 'İşleme ya da sahne geneli kayma: geçici kalibrasyon ya da açıklanamayan sahne geneli medyan değişim',
    'compass.common.alt4': 'Bakış geometrisi, piksel altı hizalama hatası ve karışık 10 m pikseller',
    'compass.reason.pixels': 'yalnızca {pixels} geçerli piksel (< {minimum})',
    'compass.reason.dead_zone': 'medyan değişim vektörü ({h}, {v}) dB, ±{tau} dB ölü bölgenin içinde',
    'compass.reason.disagree': 'piksellerin ortadaki %50\'si hem HH hem HV\'de yön konusunda anlaşmıyor',
    'compass.reason.mixed': 'karışık yönler ({h} dB HH, {v} dB HV), tek bir okuma yok',
    'compass.reason.rule': 'medyan ΔHH {h} dB, medyan ΔHV {v} dB; kural: {rule}',
    'compass.sector.dead': 'ölü bölgenin içinde',
    'compass.sector.mixed': 'karışık yönler',
    'compass.card.raw': 'Ham medyanlar',
    'compass.card.relative': 'Sahne geneli medyana göre',
    'compass.col.reference': 'Referans',
    'compass.col.pattern': 'Desen',
    'compass.col.why': 'Neden',
    'compass.card.disagree': '⚠️ **İki referans farklı okumalar veriyor.** Açıklanamayan [[scene_change]] '
                             '(ΔHH {dhh} dB, ΔHV {dhv} dB) deseni değiştirecek kadar büyük; bu yüzden hiçbir okuma tek başına kullanılmamalı.',
    'compass.card.alternatives': '**Bu radar çiftinin dışlayamadığı diğer açıklamalar:**',
    'compass.card.caution': 'Dikkat: {caution} Desenler betimleyicidir ve bu alan için doğrulanmamıştır.',
    'compass.title': 'Değişim Pusulası',
    'compass.intro': '**Bu bölge hangi değişim deseniyle tutarlı?** Bir bölgenin içinde [[hh]] (eş-polarizasyon) ve [[hv]] (çapraz-polarizasyon) '
                     'değerlerinin nasıl değiştiğini karşılaştırın. Yön, betimleyici bir *desene* ([[compass]]) karşılık gelir; desen sayılarıyla '
                     've dışlayamadığı diğer açıklamalarla birlikte gösterilir.',
    'compass.warning': 'Yalnızca betimleyici desenler. Eşleme, literatürdeki tipik L-bant davranışını izler; bu alan için DOĞRULANMAMIŞTIR ve '
                       'su, taşkın ya da arazi örtüsü değişimi göstermez.',
    'compass.spinner': 'Önbellekteki HH/HV değişimi doğrulanıyor…',
    'compass.error': 'Önbellekteki HH/HV değişimi doğrulanamadı ({error}). `python scripts/process_hv_compass.py` komutunu yerelde çalıştırın '
                     '(çevrimdışı; önbellekteki gerçek verileri kullanır). Hiçbir indirme denenmedi.',
    'compass.context': 'Louisiana vakası · NISAR L2 GCOV frekans A · {first} → {second} · {pixels} ortak geçerli 10 m piksel · '
                       'vaka çalışmasıyla aynı 3×3 doğrusal güç filtresi',
    'compass.region': 'Bölge',
    'compass.mode.saved': 'Kayıtlı bölge',
    'compass.mode.rectangle': 'Dikdörtgen',
    'compass.saved_region': 'Kayıtlı bölge (aynı ızgarada gerçek maskeler)',
    'compass.whole_aoi': 'Tüm ortak ilgi alanı',
    'compass.baseline_note': 'Temel sınıflar, aynı çift için kaydedilmiş −16 dB / 3 dB vaka çalışması çıktısıdır.',
    'compass.investigation_note': 'İnceleme bölgeleri altı tarihli HH İnceleme gezgininden gelir; burada yalnızca bu çift için okunurlar.',
    'compass.cols': 'Batı → doğu kapsamı (ilgi alanı genişliğinin %\'si)',
    'compass.rows': 'Kuzey → güney kapsamı (ilgi alanı yüksekliğinin %\'si)',
    'compass.bad_rectangle': 'Bu dikdörtgen kullanılamaz ({error}). %0 ile %100 arasında bir başlangıç ve bitiş seçin.',
    'compass.widened': 'Dikdörtgen, piksel içermesi için en az %1\'e genişletildi.',
    'compass.dead_zone': 'Ölü bölge τ (dB)',
    'compass.dead_zone_help': 'Hem |ΔHH| hem |ΔHV| değeri τ\'nun altında kalan medyan değişim vektörleri sonuçsuz sayılır. Varsayılan 1,5 dB, '
                              'açıklanamayan sahne geneli medyan HH değişimini (−1,39 dB) aşar; kalibre edilmiş bir gürültü düzeyi değildir.',
    'compass.metric.pixels': 'Bölgedeki geçerli pikseller',
    'compass.metric.area': 'Alan',
    'compass.metric.dhh': 'Medyan ΔHH',
    'compass.metric.dhv': 'Medyan ΔHV',
    'compass.iqr': 'ÇAA ΔHH {hh_lo}…{hh_hi} dB · ÇAA ΔHV {hv_lo}…{hv_hi} dB · sahne geneli medyanlar ΔHH {shh} dB, ΔHV {shv} dB. '
                   'Pikseller uzamsal olarak bağımlıdır; sayılar bağımsız örnekler değildir.',
    'compass.hv_dark': 'HV burada çok karanlık (bölge medyanı {d0} / {d1} dB, sahne %{pct}\'lik yüzdeliği {s0} / {s1} dB). HV, sayısal olarak '
                       'belirlenmemiş [[noise_floor]] yakınında olabilir; bu yüzden bu bölgede HV değişimi zayıf bir kanıttır.',
    'compass.hv_neutral': 'HV her iki tarihte de sahnenin %{pct}\'lik yüzdeliğinin üzerinde. HV [[noise_floor]] sayısal olarak belirlenmedi '
                          '(ürün gürültü katmanları doğrulanmış bir dönüşüm olmadan DN² biriminde); bu yüzden bu destek değil, nötrdür.',
    'compass.no_pixels': 'Seçilen bölgede geçerli piksel yok. Daha büyük bir dikdörtgen ya da başka bir bölge seçin.',
    'compass.spread_title': '**Bölgenin pikselleri nereye düşüyor** (aynı yön kuralları, piksel başına)',
    'compass.col.share': 'Piksel payı',
    'compass.col.sector': 'Yön dilimi',
    'compass.spread_note': 'Bu bir dağılım görünümüdür, piksel bazında sınıflandırma değildir. Dilimlere geniş dağılım, tek bir okumayı zayıflatır.',
    'compass.fig.pixels_log': 'Hücre başına piksel (log)',
    'compass.fig.region_pixels': 'Bölge pikselleri',
    'compass.fig.dead_zone': 'Ölü bölge ±{tau} dB → sonuçsuz',
    'compass.fig.corner_smooth': 'ikisi de karanlık:\ndaha düz bir yüzeyle\ntutarlı',
    'compass.fig.corner_hh': 'HH yukarı, HV değil:\nHH ağırlıklı\nparlaklaşma',
    'compass.fig.corner_volume': 'HV yukarı: daha fazla hacim\nsaçılımı ya da pürüzlülük',
    'compass.fig.bottom': 'HV aşağı, HH sabit:\nazalmış hacim saçılımı',
    'compass.fig.scene': 'Sahne geneli medyan ({h}, {v}) dB',
    'compass.fig.median': 'Bölge medyanı ({h}, {v}) dB, ÇAA çubukları',
    'compass.fig.minus_scene': ' − sahne medyanı',
    'compass.fig.xlabel': 'ΔHH (dB){suffix}  ·  sonra − önce',
    'compass.fig.ylabel': 'ΔHV (dB){suffix}',
    'compass.loc.title': 'ΔHH üzerinde bölge (turuncu) · {pair}',
    'compass.loc.xlabel': 'UTM 15K doğu koordinatı (m)',
    'compass.how': 'Pusula bir bölgeyi nasıl okur',
    'compass.how_text': 'Bölgenin medyan değişim vektörü üzerindeki kurallar (ham ve sahne geneli medyana göre), ölü bölge τ ile: {rules}. '
                        'İki referans farklı desenler verirse sonuç "Okuma referansa bağlı" olur. Dayanak: genel L-bant saçılım davranışı '
                        '(düz yüzeyler HH ve HV\'yi karartır, çift sekme HH\'yi parlatır, HV hacim saçılımını izler). '
                        'Bkz. docs/CHANGE_COMPASS_METHOD.md.',
    'compass.alt_heading': 'Diğer açıklamalar',
}

EN.update({
    'compass.hv_gate': 'Does HV carry usable signal here? (Phase 2 gate, computed before this page was built)',
    'compass.hv_assessment': '**Assessment: HV {verdict} at scene scale.**',
    'compass.noise_floor_prefix': 'Noise floor: ',
    'compass.hist_caption': 'Real ΔHH and ΔHV distributions, whole common AOI (data/hv/change_histograms.png).',
    'compass.method': 'Method: how directions map to patterns',
    'compass.col.label': 'Label',
    'compass.col.rule': 'Rule (medians, after − before)',
    'compass.col.physics': 'Typical physical reading',
    'compass.method_text': 'Rules are applied in the order listed, after three inconclusive checks: fewer than {minimum} valid pixels, '
                           'both medians inside ±τ, or the middle 50% of pixels straddling zero on both channels. Each region is '
                           'evaluated twice (raw medians, and relative to the scene-wide median); if the two differ the result is '
                           '"Reading depends on the reference". Basis: general L-band scattering literature (specular reflection from '
                           'smooth water; double bounce under flooded vegetation; HV as a volume-scattering indicator). See '
                           'docs/CHANGE_COMPASS_METHOD.md. **Not validated here.**',
    'compass.rect_name': 'Rectangle {c0}–{c1}% E-W, {r0}–{r1}% N-S',
})
TR.update({
    'compass.hv_gate': 'HV burada kullanılabilir sinyal taşıyor mu? (2. aşama kontrolü, bu sayfa yapılmadan önce hesaplandı)',
    'compass.hv_assessment': '**Değerlendirme (kayıtlı, İngilizce): sahne ölçeğinde HV {verdict}.**',
    'compass.noise_floor_prefix': 'Gürültü tabanı: ',
    'compass.hist_caption': 'Gerçek ΔHH ve ΔHV dağılımları, tüm ortak ilgi alanı (data/hv/change_histograms.png).',
    'compass.method': 'Yöntem: yönler desenlere nasıl eşlenir',
    'compass.col.label': 'Etiket',
    'compass.col.rule': 'Kural (medyanlar, sonra − önce)',
    'compass.col.physics': 'Tipik fiziksel okuma',
    'compass.method_text': 'Kurallar, üç sonuçsuzluk kontrolünden sonra listelenen sırayla uygulanır: {minimum} geçerli pikselden az, '
                           'iki medyan da ±τ içinde ya da piksellerin ortadaki %50\'si iki kanalda da sıfırın iki yanında. Her bölge iki kez '
                           'değerlendirilir (ham medyanlar ve sahne geneli medyana göre); ikisi farklıysa sonuç "Okuma referansa bağlı" olur. '
                           'Dayanak: genel L-bant saçılım literatürü (düz sudan aynasal yansıma; su basmış bitki örtüsü altında çift sekme; '
                           'hacim saçılımı göstergesi olarak HV). Bkz. docs/CHANGE_COMPASS_METHOD.md. **Burada doğrulanmamıştır.**',
    'compass.rect_name': 'Dikdörtgen D-B %{c0}–{c1}, K-G %{r0}–{r1}',
})
