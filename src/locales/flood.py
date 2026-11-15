"""Flood map layer on Explore (src/flood_layer.py), the 'Flood validation' page (src/flood_panel.py) and the
time-gap wording fix. Numbers in the validation note are exactly the measured values (data/flood_validation/)."""

EN = {
    'page.flood': 'Reference comparisons (Thailand, Gandak)',
    # Explore: flood map layer
    'fl.layer.title': 'Candidate open-water change — evaluated threshold method',
    'fl.layer.intro': 'Candidate water where HH ≤ −16 dB; candidate new water requires crossing from above this threshold with |ΔHH| ≥ 3 dB. A 3×3 valid-linear-power filter precedes dB conversion. This is an exploratory threshold map, not confirmed flooding.',
    'fl.layer.share': 'Candidate new open water in this window: {share} of valid pixels ({area} km²), {d1} → {d2}.',
    'fl.class.0': 'invalid / no data', 'fl.class.1': 'water candidate on both dates', 'fl.class.2': 'new open-water candidate',
    'fl.class.3': 'water candidate only on the first date', 'fl.class.4': 'other valid surface',
    
    'fl.layer.error': 'The candidate-water map could not be computed for this window ({error}).',
    # time-gap wording fix
    'fl.time.unloaded': 'This {days}-day pair has no loaded acquisition in between, but the catalog lists {count} '
                        'acquisition(s) in between ({dates}) that were not loaded.',
    'fl.time.unchecked': 'This {days}-day pair has no loaded acquisition in between; the catalog was not checked here, so '
                         'this may be a real acquisition gap or a date that was not loaded.',
    'fl.time.caption_unloaded': 'Acquisitions between the loaded dates exist in the catalog but were not loaded: {dates}. '
                                'Shaded intervals are therefore not missing acquisitions.',
    'fl.q.unloaded': 'Do the acquisitions that were not loaded ({dates}) change the picture?',
    # Flood validation page
    'fl.title': 'Reference comparisons (Thailand, Gandak)',
    'fl.intro': 'A preregistered comparison of the app\'s water-change rule with **independent water products** (OPERA DSWx '
                'from Sentinel-1 and from Landsat/Sentinel-2) on two real 2026 floods. These are **agreement numbers, not '
                'accuracy against ground truth, and not proof**.',
    'fl.protocol.title': 'Protocol summary',
    'fl.protocol.items': '- Protocol written and committed **before** any NISAR flood window was read (local commit {freeze}).\n'
                         '- Areas: 10 km × 10 km windows fixed before any water result: Prachin Buri River (Thailand) and '
                         'the Gandak at the centre of the NASA Earth Observatory image (India).\n'
                         '- NISAR [[gcov]] DHDH 40+5 MHz, release P05023: Thailand tracks 004 D (calibration) and 011 A (test); '
                         'Gandak 026 A (test).\n'
                         '- References: DSWx-S1 is primary (pre and flood-date scenes); DSWx-HLS is a sensitivity check '
                         '(flood date only; cloud-limited). Scenes below 70 % valid pixels are unusable, never dropped silently.\n'
                         '- **Primary rule:** the untuned default, fixed before any data was seen: HH ≤ −16 dB, new water '
                         'needs |ΔHH| ≥ 3 dB. **Primary outcome:** new open water against DSWx-S1.\n'
                         '- 95 % intervals: spatial block bootstrap (1 km blocks, 1000 resamples, fixed seed).',
    'fl.maps.title': 'Primary-rule maps',
    'fl.maps.caption': 'Left: the primary rule\'s classes. Right: agreement with DSWx-S1 for new open water (TP agreement, '
                       'FP NISAR only, FN DSWx-S1 only, TN both no new water). Pixels that are partial/inundated or invalid in '
                       'the reference are excluded.',
    'fl.agree.0': 'excluded / invalid', 'fl.agree.1': 'TP: both new water', 'fl.agree.2': 'FP: NISAR only',
    'fl.agree.3': 'FN: DSWx-S1 only', 'fl.agree.4': 'TN: both no new water',
    'fl.stage.a': 'Thailand 004 D, 6 → 30 Sep 2026 (calibration scene; primary rule untuned)',
    'fl.stage.b': 'Thailand 011 A, 6 → 30 Sep 2026 (test scene)',
    'fl.stage.c': 'Gandak 026 A, 19 Sep → 1 Oct 2026 (test scene; S1 only)',
    'fl.table.title': 'Primary results with 95 % intervals',
    'fl.col.scene': 'Scene', 'fl.col.outcome': 'Outcome', 'fl.col.reference': 'Reference (time offset)',
    'fl.col.precision': 'Precision', 'fl.col.recall': 'Recall', 'fl.col.f1': 'F1', 'fl.col.iou': 'IoU',
    'fl.outcome.new': 'new open water', 'fl.outcome.presence': 'open water on the flood date',
    'fl.neg.title': 'Negative control (two pre-flood dates, 6 → 18 Sep 2026)',
    'fl.neg.text': 'Co-registration of the 18 Sep forecast-orbit products passed ({o1} px and {o2} px; rule ≤ 1 px). The '
                   'primary rule flags {bb1} and {bb2} of the window as new water between two pre-flood dates, against {bd1} and '
                   '{bd2} for the flood pair (004 D, 011 A). Against DSWx-S1 (8 → 19 Sep, {ref} new water): {fp1} km² and '
                   '{fp2} km² of new water that the reference does not show.',
    'fl.secondary.title': 'Secondary and exploratory results',
    'fl.secondary.text': '- Calibrated thresholds (HH −10.0 dB, HV −15.5 dB) are kept frozen and are secondary: the HH '
                         'value landed on the edge of the search grid, and calibrating against DSWx-HLS "water on the flood '
                         'date" did not match the primary goal (new water against S1). New-water F1: 0.41 (Thailand test), '
                         '0.20 (Gandak).\n'
                         '- Calibrated HH+HV gives the same numbers as HH: under the "both below threshold" rule, HV adds '
                         'nothing.\n'
                         '- An exploratory rule for flooded vegetation (HH up ≥ 3 dB, HV not down) failed: F1 0.02 / 0.01 '
                         '(Thailand), 0.17 (Gandak). Not a claim.',
    'fl.deviations.title': 'Deviations from the protocol (recorded before the affected results)',
    'fl.deviations.text': '1. Block caching in the reference reader (speed only).\n'
                          '2. PO.DAAC redirects to one CloudFront host, approved by the owner (no token sent there).\n'
                          '3. After calibration and before any test: the primary rule became the untuned default; the '
                          'calibrated thresholds became secondary (commit {dev3}).\n'
                          '4. After the Thailand test: spatial block-bootstrap intervals added (point estimates unchanged).\n'
                          '- Bagaha (secondary Gandak window): not run (time). No other Gandak date or track was added.',
    'fl.limits.title': 'Limits',
    'fl.limits.text': '- Two floods, three scenes: not a general accuracy statement.\n'
                      '- References are products, not ground truth: DSWx-HLS and DSWx-S1 disagree on the Thailand flood '
                      'date (open water 57 % vs 31 %, IoU 0.55). About 90 % of the primary rule\'s false positives against '
                      'S1 are pixels that HLS calls open water.\n'
                      '- Both Thailand scenes share the same references and area. Pixel counts overstate independent '
                      'samples (30 m reference pixels repeated on the 10 m grid).\n'
                      '- Time offsets: 24–59 h in Thailand, 71.5 h at Gandak.\n'
                      '- DSWx-S1 marks flooded vegetation only inside mapped wetland; the DSWx-HLS class table comes from '
                      'its v1.0 specification while the files are v1.1.\n'
                      '- Misses cluster at flood edges and in partly submerged fields (hypothesis).',
    'fl.missing': 'Reference-comparison outputs are not available ({error}).',
    'ex.preset.thailand_prachinburi': 'Guided example: Thailand flood, Prachin Buri (cached, works offline)',
    'ex.demo.why.thailand_prachinburi': 'River floodplain with rice paddies and a town; the scene of the case-specific reference comparison.',
    'fl.demo.info': '**{name}** · {lat}, {lon} · {window} km × {window} km window · {count} dates: {dates}  \n'
                    'Why chosen: {why}  \nDates and window are those of the reference-comparison protocol, fixed before any '
                    'NISAR flood window was read: 6 and 18 Sep 2026 are before the flood (18 Sep uses a forecast orbit; '
                    'its co-registration was checked), 30 Sep is during the flood. Results are shown as computed.',
    'fl.example_caption': 'Example pair: 6 → 30 Sep 2026, the saved Thailand 004 D comparison. Reference agreement applies to the evaluated mask only. Select 6 → 18 Sep for the pre-event control; other pairs remain available.',
    'fl.gandak_rotation': 'The square looks rotated because the NISAR grid here is UTM zone 44N while the area was defined in '
                          'UTM zone 45N; the data are correct.',
    'fl.legend': 'Legend',
}

TR = {
    'page.flood': 'Referans karşılaştırmaları (Tayland, Gandak)',
    'fl.layer.title': 'Açık su değişimi adayları — değerlendirilmiş eşik yöntemi',
    'fl.layer.intro': 'HH ≤ −16 dB su adayıdır; yeni su adayı bu eşiğin üstünden altına geçiş ve |ΔHH| ≥ 3 dB gerektirir. dB dönüşümünden önce 3×3 geçerli doğrusal güç filtresi uygulanır. Bu keşif amaçlı eşik haritasıdır; teyit edilmiş taşkın değildir.',
    'fl.layer.share': 'Bu penceredeki yeni açık su adayı: geçerli piksellerin {share} kadarı ({area} km²), {d1} → {d2}.',
    'fl.class.0': 'geçersiz / veri yok', 'fl.class.1': 'iki tarihte de su adayı', 'fl.class.2': 'yeni açık su adayı',
    'fl.class.3': 'yalnızca ilk tarihte su adayı', 'fl.class.4': 'diğer geçerli yüzey',
    
    'fl.layer.error': 'Bu pencere için su adayı haritası hesaplanamadı ({error}).',
    'fl.time.unloaded': 'Bu {days} günlük çiftin arasında yüklenmiş çekim yok, ancak katalogda arada {count} çekim '
                        '({dates}) var ve bunlar yüklenmedi.',
    'fl.time.unchecked': 'Bu {days} günlük çiftin arasında yüklenmiş çekim yok; katalog burada kontrol edilmedi, bu yüzden '
                         'bu gerçek bir çekim boşluğu ya da yüklenmemiş bir tarih olabilir.',
    'fl.time.caption_unloaded': 'Yüklenen tarihler arasında katalogda çekimler var ama yüklenmedi: {dates}. Bu nedenle '
                                'gölgeli aralıklar eksik çekim değildir.',
    'fl.q.unloaded': 'Yüklenmeyen çekimler ({dates}) tabloyu değiştiriyor mu?',
    'fl.title': 'Referans karşılaştırmaları (Tayland, Gandak)',
    'fl.intro': 'Uygulamanın su değişimi kuralının, 2026\'daki iki gerçek selde **bağımsız su ürünleriyle** (Sentinel-1 ve '
                'Landsat/Sentinel-2\'den OPERA DSWx) önceden kayıt altına alınmış karşılaştırması. Bunlar **uyum sayılarıdır; '
                'yer gerçeğine göre doğruluk değildir ve kanıt değildir**.',
    'fl.protocol.title': 'Protokol özeti',
    'fl.protocol.items': '- Protokol, hiçbir NISAR sel penceresi okunmadan **önce** yazıldı ve kaydedildi (yerel commit {freeze}).\n'
                         '- Alanlar: herhangi bir su sonucundan önce sabitlenen 10 km × 10 km pencereler: Prachin Buri Nehri '
                         '(Tayland) ve NASA Earth Observatory görüntüsünün merkezindeki Gandak (Hindistan).\n'
                         '- NISAR [[gcov]] DHDH 40+5 MHz, sürüm P05023: Tayland 004 D (kalibrasyon) ve 011 A (test) izleri; '
                         'Gandak 026 A (test).\n'
                         '- Referanslar: DSWx-S1 birincil (sel öncesi ve sel tarihi sahneleri); DSWx-HLS duyarlılık kontrolü '
                         '(yalnızca sel tarihi; bulut sınırlı). Geçerli pikseli %70\'in altındaki sahneler kullanılamaz; '
                         'sessizce atılmaz.\n'
                         '- **Birincil kural:** hiçbir veri görülmeden sabitlenen ayarlanmamış varsayılan: HH ≤ −16 dB, yeni '
                         'su için |ΔHH| ≥ 3 dB. **Birincil sonuç:** DSWx-S1\'e göre yeni açık su.\n'
                         '- %95 aralıklar: uzamsal blok bootstrap (1 km bloklar, 1000 yeniden örnekleme, sabit tohum).',
    'fl.maps.title': 'Birincil kural haritaları',
    'fl.maps.caption': 'Sol: birincil kuralın sınıfları. Sağ: yeni açık su için DSWx-S1 ile uyum (TP uyum, FP yalnızca NISAR, '
                       'FN yalnızca DSWx-S1, TN ikisi de yeni su yok). Referansta kısmi/su basmış bitki ya da geçersiz olan '
                       'pikseller hariç tutulur.',
    'fl.agree.0': 'hariç / geçersiz', 'fl.agree.1': 'TP: ikisi de yeni su', 'fl.agree.2': 'FP: yalnızca NISAR',
    'fl.agree.3': 'FN: yalnızca DSWx-S1', 'fl.agree.4': 'TN: ikisi de yeni su yok',
    'fl.stage.a': 'Tayland 004 D, 6 → 30 Eyl 2026 (kalibrasyon sahnesi; birincil kural ayarlanmadı)',
    'fl.stage.b': 'Tayland 011 A, 6 → 30 Eyl 2026 (test sahnesi)',
    'fl.stage.c': 'Gandak 026 A, 19 Eyl → 1 Eki 2026 (test sahnesi; yalnızca S1)',
    'fl.table.title': '%95 aralıklarla birincil sonuçlar',
    'fl.col.scene': 'Sahne', 'fl.col.outcome': 'Sonuç', 'fl.col.reference': 'Referans (zaman farkı)',
    'fl.col.precision': 'Kesinlik', 'fl.col.recall': 'Duyarlılık', 'fl.col.f1': 'F1', 'fl.col.iou': 'IoU',
    'fl.outcome.new': 'yeni açık su', 'fl.outcome.presence': 'sel tarihinde açık su',
    'fl.neg.title': 'Negatif kontrol (sel öncesi iki tarih, 6 → 18 Eyl 2026)',
    'fl.neg.text': '18 Eylül tahmini yörünge ürünlerinin çakıştırılması geçti ({o1} px ve {o2} px; kural ≤ 1 px). Birincil '
                   'kural, sel öncesi iki tarih arasında pencerenin {bb1} ve {bb2} kadarını yeni su olarak işaretliyor; sel '
                   'çiftinde bu oran {bd1} ve {bd2} (004 D, 011 A). DSWx-S1\'e göre (8 → 19 Eyl, {ref} yeni su): referansın '
                   'göstermediği {fp1} km² ve {fp2} km² yeni su.',
    'fl.secondary.title': 'İkincil ve keşif amaçlı sonuçlar',
    'fl.secondary.text': '- Kalibre edilmiş eşikler (HH −10,0 dB, HV −15,5 dB) dondurulmuş olarak tutulur ve ikincildir: HH '
                         'değeri arama ızgarasının kenarına düştü ve DSWx-HLS "sel tarihinde su" ölçütüne göre kalibrasyon '
                         'birincil amaçla (S1\'e göre yeni su) örtüşmedi. Yeni su F1: 0,41 (Tayland testi), 0,20 (Gandak).\n'
                         '- Kalibre edilmiş HH+HV, HH ile aynı sayıları veriyor: "ikisi de eşiğin altında" kuralında HV bir '
                         'şey katmıyor.\n'
                         '- Su basmış bitki örtüsü için keşif amaçlı bir kural (HH ≥ 3 dB artış, HV düşmüyor) başarısız oldu: '
                         'F1 0,02 / 0,01 (Tayland), 0,17 (Gandak). Bir iddia değildir.',
    'fl.deviations.title': 'Protokolden sapmalar (etkilenen sonuçlardan önce kaydedildi)',
    'fl.deviations.text': '1. Referans okuyucuda blok önbellekleme (yalnızca hız).\n'
                          '2. PO.DAAC tek bir CloudFront sunucusuna yönlendiriyor; sahip onayladı (oraya anahtar gönderilmez).\n'
                          '3. Kalibrasyondan sonra ve herhangi bir testten önce: birincil kural ayarlanmamış varsayılan oldu; '
                          'kalibre edilmiş eşikler ikincil oldu (commit {dev3}).\n'
                          '4. Tayland testinden sonra: uzamsal blok bootstrap aralıkları eklendi (nokta tahminleri değişmedi).\n'
                          '- Bagaha (ikincil Gandak penceresi): çalıştırılmadı (zaman). Başka Gandak tarihi ya da izi eklenmedi.',
    'fl.limits.title': 'Sınırlar',
    'fl.limits.text': '- İki sel, üç sahne: genel bir doğruluk ifadesi değildir.\n'
                      '- Referanslar yer gerçeği değil, üründür: DSWx-HLS ve DSWx-S1 Tayland sel tarihinde uyuşmuyor (açık '
                      'su %57\'ye karşı %31, IoU 0,55). Birincil kuralın S1\'e göre yanlış pozitiflerinin yaklaşık %90\'ı '
                      'HLS\'nin açık su dediği pikseller.\n'
                      '- İki Tayland sahnesi aynı referansları ve alanı paylaşıyor. Piksel sayıları bağımsız örnekleri '
                      'olduğundan fazla gösterir (30 m referans pikselleri 10 m ızgarada tekrarlanır).\n'
                      '- Zaman farkları: Tayland\'da 24–59 saat, Gandak\'ta 71,5 saat.\n'
                      '- DSWx-S1 su basmış bitki örtüsünü yalnızca haritalanmış sulak alanlarda işaretler; DSWx-HLS sınıf '
                      'tablosu v1.0 belirtiminden alındı, dosyalar ise v1.1.\n'
                      '- Kaçırılan pikseller sel kenarlarında ve kısmen su altındaki tarlalarda yoğunlaşıyor (hipotez).',
    'fl.missing': 'Referans karşılaştırma çıktıları kullanılamıyor ({error}).',
    'ex.preset.thailand_prachinburi': 'Rehberli örnek: Tayland seli, Prachin Buri (önbellekte, çevrimdışı çalışır)',
    'ex.demo.why.thailand_prachinburi': 'Çeltik tarlaları ve bir kasaba bulunan nehir taşkın ovası; vakaya özgü referans karşılaştırmasının sahnesi.',
    'fl.demo.info': '**{name}** · {lat}, {lon} · {window} km × {window} km pencere · {count} tarih: {dates}  \n'
                    'Neden seçildi: {why}  \nTarihler ve pencere, hiçbir NISAR sel penceresi okunmadan önce sabitlenen sel '
                    'karşılaştırma protokolündekilerdir: 6 ve 18 Eylül 2026 sel öncesi (18 Eylül tahmini yörünge kullanıyor; '
                    'çakıştırması kontrol edildi), 30 Eylül sel sırası. Sonuçlar hesaplandığı gibi gösterilir.',
    'fl.example_caption': 'Örnek çift: 6 → 30 Eyl 2026, kayıtlı Tayland 004 D karşılaştırması. Referans uyumu yalnızca değerlendirme maskesi için geçerlidir. Olay öncesi kontrol için 6 → 18 Eyl seçin; diğer çiftler erişilebilir.',
    'fl.gandak_rotation': 'Kare döndürülmüş görünüyor, çünkü buradaki NISAR ızgarası UTM 44N bölgesinde, alan ise UTM 45N '
                          'bölgesinde tanımlandı; veriler doğru.',
    'fl.legend': 'Gösterge',
}
