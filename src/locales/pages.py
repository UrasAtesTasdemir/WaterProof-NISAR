"""About page and Sentinel-1 benchmark appendix."""

EN = {
    'about.title': 'About {app}',
    'about.headline': 'Radar change maps are hard to interpret and hard to trust.',
    'about.framing': '[[nisar]] sees through cloud, day and night. Its [[lband]] radar responds to water, vegetation structure, soil moisture '
                     'and roughness, which is why "the radar got darker here" is ambiguous: a darker pixel can come from new open water, '
                     'a calmer or drier surface, harvested vegetation, or a processing effect. Most change maps also hide how fragile '
                     'they are. This tool keeps the raw numbers, the alternative explanations and the robustness checks side by side. '
                     'Everything it suggests is a [[hypothesis]].',
    'about.pages': 'Pages',
    'about.page.Researcher workflow': 'One candidate, one date pair, one evidence list, and a downloadable review note.',
    'about.page.NISAR study': 'The original Louisiana dashboard plus its analysis views (map, time series, HH/HV, investigation, '
                              'Change Compass, evidence checklist, diagnostics).',
    'about.page.Is this scene analyzable?': 'Compatible radar pairs, shared footprint coverage, timing and optical reference usability '
                                            'for the two cached cases.',
    'about.page.Benchmark Validation (Sentinel-1)': 'A frozen Sentinel-1 benchmark. It does not describe NISAR.',
    'about.provenance': 'Data provenance',
    'about.provenance_table': 'Folders and what they contain',
    'about.col.data': 'Data', 'about.col.folder': 'Folder', 'about.col.notes': 'Notes',
    'about.prov.louisiana.name': 'Louisiana NISAR pair (HH)',
    'about.prov.louisiana.notes': 'NISAR L2 GCOV provisional, track 105 / frame 17, 21 Jun & 3 Jul 2026',
    'about.prov.six_date.name': 'Six-date HH and HV',
    'about.prov.six_date.notes': 'Bounded HTTPS range reads (≈8 MiB per product); SHA-256 sidecars',
    'about.prov.hv.name': 'HH/HV pair change',
    'about.prov.hv.notes': 'Derived offline from the cached windows above',
    'about.prov.investigation.name': 'Investigation candidates',
    'about.prov.investigation.notes': 'Five regions from a stated screening heuristic (not a score)',
    'about.prov.robustness.name': 'Robustness checks',
    'about.prov.robustness.notes': 'Settings variants, leave-one-date-out (seed-event interval), surrounding ring; offline. '
                                   'Version 1 in data/robustness/ is kept for the record',
    'about.prov.baseline.name': 'Baseline candidates and quality checks',
    'about.prov.baseline.notes': '−16 dB / 3 dB baseline, sensitivity, waterways',
    'about.prov.references.name': 'Independent references',
    'about.prov.references.notes': 'OPERA DSWx-HLS / DSWx-S1 AOI windows, USGS gauges',
    'about.prov.benchmark.name': 'Sentinel-1 benchmark (appendix)',
    'about.prov.benchmark.notes': 'Sen1Floods11 subset; frozen; does not describe NISAR',
    'about.offline': 'Cached examples and saved comparisons need no Earthdata authentication or new NASA downloads. Live searches require internet; new radar reads also need Earthdata authentication. Basemap tiles need internet; the globe texture, cached radar overlays and numbers are local.',
    'about.limits': 'Limits',
    'about.limits_text': '- **Three evidence scopes.** Louisiana (and Kerrville): exploratory; no independent [[reference]] with matching timing and coverage, so no accuracy is claimed. Thailand and Gandak: case-specific agreement with independent water products (OPERA DSWx) for the saved dates, grids and threshold map only. Live places: exploratory unless that exact product pair has been evaluated; Thailand/Gandak scores never transfer.\n- Measured agreement varies by place: new open-water F1 0.78 [0.74, 0.81] on Thailand track 011 A versus 0.24 [0.17, 0.31] at Gandak. The two Thailand tracks cover the same area and share references; they are not two independent successes.\n- A pre-event Thailand control (6 → 18 Sep 2026) still produced 3.1 / 5.2 km² of new-water candidates; a darker pixel alone is not evidence of flooding.\n- Nothing in the app confirms flooding, water or land-cover change, or establishes a cause.\n- The [[scene_change]] (−1.39 dB HH for 21 Jun → 3 Jul, Louisiana) is unexplained and not corrected.\n- The HV [[noise_floor]] is not quantified (noise layers are in DN²); very dark HV may be floor-limited.\n- Louisiana has six dates with one 24-day gap (27 Jul → 20 Aug); short-lived changes can be missed.\n- Screening settings and [[threshold|thresholds]] are exploratory; robustness checks use the same observations and are not accuracy.\n- NISAR products are provisional; DSWx references are products, not field truth.',
    'about.glossary': 'Glossary',
    'about.glossary_open': 'All terms in plain words',
    'about.col.term': 'Term', 'about.col.meaning': 'Meaning',
    'about.ai': 'AI use',
    'about.ai_text': 'AI tools were used in building this project: **Claude Code (Anthropic)** and **ChatGPT / Codex (OpenAI)**, '
                     'for writing and refactoring code and tests, inspecting cached data and reports, and drafting documentation. '
                     'All scientific numbers come from real NASA data processed by the code in this repository. See README.md.',
    'about.license': 'License',
    'about.license_text': 'MIT License (see LICENSE).',
    'bm.title': 'Appendix: Sentinel-1 benchmark',
    'bm.caption': 'Appendix to WaterProof. This page evaluates a different sensor (Sentinel-1) and does not describe NISAR performance.',
    'bm.subheader': 'Sen1Floods11 · Sentinel-1 adaptation only',
    'bm.warning': 'These scores evaluate Sentinel-1 VV/VH adaptation against manual benchmark water labels. They do NOT establish '
                  'NISAR HH accuracy or confirmed flood extent.',
    'bm.error': 'Benchmark evaluation is missing or incomplete. Run the separate benchmark workflow first.',
    'bm.summary': '{test} held-out test chips · {groups} geographic event groups · {pixels} evaluated pixels. Calibration used {train} '
                  'separate official training chips.',
    'bm.subset': 'Small deterministic subset, not the full benchmark. Train/test chips can share events; this is not an unseen-event '
                 'generalization test.',
    'bm.col.method': 'Method',
    'bm.method.calibrated': 'Train-calibrated threshold',
    'bm.method.otsu': 'Per-chip Otsu baseline',
    'bm.micro': 'Micro scores pool test pixels. Macro per-chip F1: {macro}; the gap shows scene imbalance. No NISAR score is inferred.',
    'bm.frozen': 'Frozen training choice: {band} ≤ {threshold} dB. 3×3 valid-linear-power mean; source values already dB. No second '
                 'logarithm is applied to dB values.',
    'bm.matrix': 'Confusion matrix and all held-out scenes',
    'bm.col.manual': 'Manual class', 'bm.col.pred_not': 'Predicted not water', 'bm.col.pred_water': 'Predicted water', 'bm.col.scene': 'Scene',
    'bm.not_water': 'Not water', 'bm.water': 'Water',
    'bm.undefined': 'Undefined denominators remain undefined. Label −1, NaN and radar nodata are ignored. No test chip was removed '
                    'because of poor performance.',
    'bm.scenes': 'Real scenes: successes and failures',
    'bm.scene': 'Held-out scene',
    'bm.figure_missing': 'Scene figure missing; numeric results remain available.',
    'bm.limits': 'A single global intensity threshold can miss water affected by vegetation/roughness and mistake dark nonwater for '
                 'water. The NISAR app uses a different sensor band and product. This benchmark measures surface-water presence, not '
                 'verified flood expansion.',
    'bm.link': '[Official Sen1Floods11 dataset](https://github.com/cloudtostreet/Sen1Floods11)',
}

TR = {
    'about.title': '{app} hakkında',
    'about.headline': 'Radar değişim haritalarını yorumlamak da onlara güvenmek de zordur.',
    'about.framing': '[[nisar]] bulutun arasından, gece ve gündüz görür. [[lband|L-bant]] radarı suya, bitki yapısına, toprak nemine ve '
                     'pürüzlülüğe tepki verir; bu yüzden "radar burada karardı" ifadesi belirsizdir: daha karanlık bir piksel yeni açık sudan, '
                     'daha sakin ya da kuru bir yüzeyden, hasat edilmiş bitkiden ya da bir işleme etkisinden gelebilir. Çoğu değişim haritası '
                     'ne kadar kırılgan olduğunu da gizler. Bu araç ham sayıları, alternatif açıklamaları ve sağlamlık kontrollerini yan yana '
                     'tutar. Öne sürdüğü her şey bir [[hypothesis|hipotezdir]].',
    'about.pages': 'Sayfalar',
    'about.page.Researcher workflow': 'Bir aday, bir tarih çifti, bir kanıt listesi ve indirilebilir bir inceleme notu.',
    'about.page.NISAR study': 'Orijinal Louisiana paneli ve analiz görünümleri (harita, zaman serisi, HH/HV, inceleme, Değişim Pusulası, '
                              'kanıt listesi, tanılamalar).',
    'about.page.Is this scene analyzable?': 'Önbellekteki iki vaka için uyumlu radar çiftleri, ortak ayak izi kapsaması, zamanlama ve optik '
                                            'referansların kullanılabilirliği.',
    'about.page.Benchmark Validation (Sentinel-1)': 'Dondurulmuş bir Sentinel-1 kıyaslaması. NISAR\'ı tanımlamaz.',
    'about.provenance': 'Verinin kaynağı',
    'about.provenance_table': 'Klasörler ve içerikleri',
    'about.col.data': 'Veri', 'about.col.folder': 'Klasör', 'about.col.notes': 'Notlar',
    'about.prov.louisiana.name': 'Louisiana NISAR çifti (HH)',
    'about.prov.louisiana.notes': 'NISAR L2 GCOV geçici ürün, iz 105 / çerçeve 17, 21 Haziran ve 3 Temmuz 2026',
    'about.prov.six_date.name': 'Altı tarihli HH ve HV',
    'about.prov.six_date.notes': 'Sınırlı HTTPS aralık okumaları (ürün başına ≈8 MiB); SHA-256 yan dosyaları',
    'about.prov.hv.name': 'HH/HV çift değişimi',
    'about.prov.hv.notes': 'Yukarıdaki önbellek pencerelerinden çevrimdışı türetildi',
    'about.prov.investigation.name': 'İnceleme adayları',
    'about.prov.investigation.notes': 'Belirtilen bir tarama sezgisinden beş bölge (puan değil)',
    'about.prov.robustness.name': 'Sağlamlık kontrolleri',
    'about.prov.robustness.notes': 'Ayar varyantları, bir tarihi dışarıda bırakma (tohum olayı aralığı), çevre halkası; çevrimdışı. '
                                   'data/robustness/ içindeki 1. sürüm kayıt için saklanıyor',
    'about.prov.baseline.name': 'Temel adaylar ve kalite kontrolleri',
    'about.prov.baseline.notes': '−16 dB / 3 dB temel, duyarlılık, su yolları',
    'about.prov.references.name': 'Bağımsız referanslar',
    'about.prov.references.notes': 'OPERA DSWx-HLS / DSWx-S1 ilgi alanı pencereleri, USGS ölçüm istasyonları',
    'about.prov.benchmark.name': 'Sentinel-1 kıyaslaması (ek)',
    'about.prov.benchmark.notes': 'Sen1Floods11 alt kümesi; dondurulmuş; NISAR\'ı tanımlamaz',
    'about.offline': 'Önbellekteki örnekler ve kayıtlı karşılaştırmalar Earthdata girişi veya yeni NASA indirmesi gerektirmez. Canlı arama internet; yeni radar okumaları ayrıca Earthdata kimlik doğrulaması gerektirir. Harita altlıkları internet kullanır; küre dokusu, önbellekteki radar katmanları ve sayılar yereldir.',
    'about.limits': 'Sınırlar',
    'about.limits_text': "- **Üç kanıt kapsamı.** Louisiana (ve Kerrville): keşif amaçlı; zamanı ve kapsamı eşleşen bağımsız [[reference]] yok, bu nedenle doğruluk iddia edilmez. Tayland ve Gandak: yalnızca kayıtlı tarihler, ızgaralar ve eşik haritası için bağımsız su ürünleriyle (OPERA DSWx) vakaya özgü uyum. Canlı yerler: tam o ürün çifti değerlendirilmedikçe keşif amaçlıdır; Tayland/Gandak puanları asla aktarılmaz.\n- Ölçülen uyum yere göre değişir: yeni açık su için Tayland 011 A izinde F1 0,78 [0,74; 0,81], Gandak'ta 0,24 [0,17; 0,31]. İki Tayland izi aynı alanı kapsar ve referansları paylaşır; iki bağımsız başarı değildir.\n- Tayland'da olay öncesi kontrol (6 → 18 Eyl 2026) yine de 3,1 / 5,2 km² yeni su adayı üretti; yalnızca kararan bir piksel taşkın kanıtı değildir.\n- Uygulamadaki hiçbir şey taşkını, suyu ya da arazi örtüsü değişimini teyit etmez veya bir neden ortaya koymaz.\n- [[scene_change]] (Louisiana, 21 Haz → 3 Tem için HH −1,39 dB) açıklanamamıştır ve düzeltilmemiştir.\n- HV [[noise_floor]] sayısal olarak belirlenmedi (gürültü katmanları DN² biriminde); çok karanlık HV tabana dayanmış olabilir.\n- Louisiana'da bir 24 günlük boşlukla (27 Tem → 20 Ağu) altı tarih var; kısa süreli değişimler kaçabilir.\n- Tarama ayarları ve [[threshold|eşikler]] keşif amaçlıdır; sağlamlık kontrolleri aynı gözlemleri kullanır ve doğruluk değildir.\n- NISAR ürünleri geçicidir; DSWx referansları üründür, saha gerçeği değildir.",
    'about.glossary': 'Sözlük',
    'about.glossary_open': 'Tüm terimler sade bir dille',
    'about.col.term': 'Terim', 'about.col.meaning': 'Anlamı',
    'about.ai': 'Yapay zekâ kullanımı',
    'about.ai_text': 'Bu projenin yapımında yapay zekâ araçları kullanıldı: **Claude Code (Anthropic)** ve **ChatGPT / Codex (OpenAI)**; '
                     'kod ve testleri yazmak ve yeniden düzenlemek, önbellekteki veri ve raporları incelemek ve belgeleri taslak olarak '
                     'hazırlamak için. Tüm bilimsel sayılar, bu depodaki kodla işlenen gerçek NASA verilerinden gelir. Bkz. README.md.',
    'about.license': 'Lisans',
    'about.license_text': 'MIT Lisansı (bkz. LICENSE).',
    'bm.title': 'Ek: Sentinel-1 kıyaslaması',
    'bm.caption': 'WaterProof eki. Bu sayfa farklı bir algılayıcıyı (Sentinel-1) değerlendirir ve NISAR performansını tanımlamaz.',
    'bm.subheader': 'Sen1Floods11 · yalnızca Sentinel-1 uyarlaması',
    'bm.warning': 'Bu puanlar Sentinel-1 VV/VH uyarlamasını el ile etiketlenmiş kıyaslama su etiketlerine göre değerlendirir. NISAR HH '
                  'doğruluğunu ya da teyit edilmiş taşkın kapsamını KANITLAMAZ.',
    'bm.error': 'Kıyaslama değerlendirmesi eksik ya da tamamlanmamış. Önce ayrı kıyaslama iş akışını çalıştırın.',
    'bm.summary': '{test} ayrılmış test parçası · {groups} coğrafi olay grubu · {pixels} değerlendirilen piksel. Kalibrasyonda {train} ayrı '
                  'resmî eğitim parçası kullanıldı.',
    'bm.subset': 'Küçük, belirlenimci bir alt küme; kıyaslamanın tamamı değil. Eğitim/test parçaları olayları paylaşabilir; bu, görülmemiş '
                 'olaylara genelleme testi değildir.',
    'bm.col.method': 'Yöntem',
    'bm.method.calibrated': 'Eğitimle kalibre edilmiş eşik',
    'bm.method.otsu': 'Parça başına Otsu temeli',
    'bm.micro': 'Mikro puanlar test piksellerini birleştirir. Parça başına makro F1: {macro}; aradaki fark sahne dengesizliğini gösterir. '
                'Hiçbir NISAR puanı çıkarılmaz.',
    'bm.frozen': 'Dondurulmuş eğitim seçimi: {band} ≤ {threshold} dB. 3×3 geçerli doğrusal güç ortalaması; kaynak değerler zaten dB. dB '
                 'değerlerine ikinci bir logaritma uygulanmaz.',
    'bm.matrix': 'Karışıklık matrisi ve tüm ayrılmış sahneler',
    'bm.col.manual': 'El ile sınıf', 'bm.col.pred_not': 'Tahmin: su değil', 'bm.col.pred_water': 'Tahmin: su', 'bm.col.scene': 'Sahne',
    'bm.not_water': 'Su değil', 'bm.water': 'Su',
    'bm.undefined': 'Tanımsız paydalar tanımsız kalır. −1 etiketi, NaN ve radar veri-yok değerleri yok sayılır. Kötü performans nedeniyle '
                    'hiçbir test parçası çıkarılmadı.',
    'bm.scenes': 'Gerçek sahneler: başarılar ve başarısızlıklar',
    'bm.scene': 'Ayrılmış sahne',
    'bm.figure_missing': 'Sahne şekli eksik; sayısal sonuçlar mevcut.',
    'bm.limits': 'Tek bir küresel yoğunluk eşiği bitki/pürüzlülükten etkilenen suyu kaçırabilir ve karanlık su olmayan yüzeyi su sanabilir. '
                 'NISAR uygulaması farklı bir algılayıcı bandı ve ürünü kullanır. Bu kıyaslama yüzey suyunun varlığını ölçer, doğrulanmış '
                 'taşkın genişlemesini değil.',
    'bm.link': '[Resmî Sen1Floods11 veri kümesi](https://github.com/cloudtostreet/Sen1Floods11)',
}
