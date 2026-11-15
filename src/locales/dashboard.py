"""Louisiana change dashboard (app.py)."""

EN = {
    'dash.title': 'Case study: Louisiana',
    'dash.intro': 'Part of **{app}** · explore radar observations and **[[candidate]] surface-water change** in a Louisiana wetland area.',
    'dash.open_workflow': 'Open the researcher workflow',
    'dash.warning': 'Exploratory surface-water change candidates. NOT confirmed flooding. Independent validation unavailable.',
    'dash.spinner': 'Verifying local radar data…',
    'dash.error': 'Local data could not be verified ({error}). Restore the Milestone 2 subsets and Milestone 3 metadata in data/. '
                  'No download was attempted.',
    'dash.explore': 'Explore the signal',
    'dash.two_obs': 'Two real observations · Local cached data',
    'dash.threshold': 'Water threshold (dB)',
    'dash.threshold_help': 'Filtered HH ≤ threshold is a water candidate. This is an exploratory setting.',
    'dash.minimum': 'Minimum backscatter change (dB)',
    'dash.minimum_help': 'Transitions require |after − before| ≥ this value. Zero removes the magnitude gate.',
    'dash.singletons': 'Suppress single-pixel change candidates (optional)',
    'dash.singletons_help': 'Separately suppress 8-connected one-pixel expansion and recession groups. Can remove real narrow features. '
                            'Persistent and unknown pixels stay unchanged.',
    'dash.fixed': 'Fixed: 3 × 3 mask-aware mean in linear power, then dB conversion.',
    'dash.sensitivity_info': 'Thresholds explore sensitivity. They do not validate flooding.',
    'dash.grid_note': 'HH · 10 m grid · EPSG:32615\n\nNo credentials or NASA downloads needed.',
    'dash.dates': 'BEFORE 21 June 2026, 11:19 UTC → AFTER 3 July 2026, 11:19 UTC · Louisiana, USA',
    'dash.metric.expansion': 'Candidate expansion',
    'dash.metric.recession': 'Candidate recession',
    'dash.metric.net': 'Net candidate change',
    'dash.metric.valid_area': 'Valid comparison area',
    'dash.settings': 'Water threshold {threshold} dB · Minimum change {minimum} dB · {pixels} common valid pixels',
    'dash.filter_on': 'Optional size filter ON: {count} isolated change-candidate pixels suppressed. They are shown as other valid surface, '
                      'not verified dry land. Real small water features can be lost. Radar values are unchanged.',
    'dash.interpretation': 'Scientific interpretation',
    'dash.interpretation_text': '**Darker radar is not proof of flooding.** Existing channels, smooth ground, vegetation, wind and soil '
                                'moisture can change the return.\n\n**[[threshold|Threshold]] sensitivity:** candidate areas vary with the '
                                'exploratory water threshold and change gate. Use the sensitivity tab; no threshold is optimized for a larger '
                                'area.\n\n**Scene-wide darkening:** the common AOI median change is **{median} dB**. This may influence '
                                'candidates but is not established sensor bias. No scene-offset correction is applied. A spatially uniform '
                                'shift of this size alone is below the default 3 dB gate.\n\n**Independent validation is unavailable.** '
                                'Same-day inspected optical references were cloud/shadow covered. Historical waterways provide context, not '
                                'proof of flooding. Singleton suppression is optional and does not increase scientific confidence.',
    'dash.tab.geo': 'Geographic map',
    'dash.tab.radar': 'Radar & water candidates',
    'dash.tab.sensitivity': 'Threshold sensitivity',
    'dash.tab.source': 'Data & scientific context',
    'dash.easting': 'Easting (m)',
    'dash.northing': 'Northing (m)',
    'dash.gamma0': 'Gamma-0 (dB)',
    'dash.geo_caption': 'Same classes as the metrics above, for the current slider settings, on an OpenStreetMap basemap. Display is '
                        'nearest-resampled to Web Mercator; areas are always computed on the native 10 m grid. The basemap needs internet; '
                        'the overlay is local.',
    'dash.geo_missing': 'Geographic overlay not available ({error}); the radar panels in the next tab are unaffected.',
    'dash.panel.before': 'Before SAR backscatter',
    'dash.panel.before_caption': '21 June 2026 · filtered HH',
    'dash.panel.after': 'After SAR backscatter',
    'dash.panel.after_caption': '3 July 2026 · filtered HH',
    'dash.panel.difference': 'Backscatter difference',
    'dash.panel.difference_caption': 'After − before · negative = darkening',
    'dash.panel.classes': 'Candidate surface-water change',
    'dash.panel.classes_caption': 'Exploratory classes · unknown remains unknown',
    'dash.legend': 'CLASS LEGEND: Gray-blue = unknown / no data · Blue = persistent water candidate · Teal = new water candidate · '
                   'Orange = receded water candidate · Light gray = other valid surface (including transitions rejected by the change gate).',
    'dash.scale': 'Before/after share one display scale. Percentile display limits never clip scientific data.',
    'dash.sens_title': 'How much depends on the threshold?',
    'dash.sens_text': 'Every point is calculated from the real radar arrays using the selected minimum change.',
    'dash.sens.expansion': 'Expansion (km²)',
    'dash.sens.recession': 'Recession (km²)',
    'dash.sens.selected': 'Selected threshold',
    'dash.sens.xlabel': 'Exploratory water threshold (dB)',
    'dash.sens.ylabel': 'Candidate area (km²)',
    'dash.sens_table': 'Values behind the chart',
    'dash.sens_caption': 'Sensitivity is not accuracy. No threshold is selected to maximize candidate area.',
    'dash.source_title': 'Two observations. A transparent processing record.',
    'dash.source_table': 'Products, files and area of interest',
    'dash.source.pol': 'HH / HHHH intensity',
    'dash.aoi': 'Louisiana, USA · Longitude −90.310020 to −90.250797° · Latitude 29.902604 to 29.924476° · EPSG:32615 · 10 m pixels.',
    'dash.checked': 'Source identifiers, file fingerprints, tags and dB values are checked against previous processing records. Areas use '
                    'projected metres, never degrees.',
    'dash.quality': 'Baseline quality check (−16 dB / 3 dB, not the current slider result): {near}/{count} expansion candidates lie within '
                    '30 m of historical mapped canals/streams. Same-day optical reference windows were cloud/shadow masked. This is not '
                    'flood validation.',
    'dash.quality_missing': 'Optional quality report missing. Independent validation remains unavailable.',
    'dash.links': '[NASA ASF NISAR Cookbook](https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/) · '
                  '[Independent optical reference: DSWx-HLS](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-HLS_V1) · '
                  '[Historical USGS hydrography](https://www.usgs.gov/national-hydrography/access-national-hydrography-products)',
    'dash.product_link': '[{date} NASA catalog product URL]({url})',
    'dash.method': 'Methodology & scientific limitations',
    'dash.method_text': '[[nisar]] measures radar scattering from the Earth’s surface. **[[hh]]** means horizontally transmitted and '
                        'horizontally received radar. The [[gcov]] **HHHH** layer is radiometrically terrain-corrected gamma-0 '
                        '[[backscatter]] power.\n\nWe intersect valid positive-power masks, apply a **3 × 3 normalized mean in linear '
                        'power** (reduces [[speckle]]), preserve invalid centers, then compute **[[db]] = 10 × log10(power)**. Change is '
                        '**after dB − before dB**.\n\nAt or below the selected threshold is a **water candidate**. Both dates below: '
                        'persistent candidate. Crossing downward: new candidate. Crossing upward: receded candidate. Transitions must '
                        'also meet the absolute-change control. Other valid pixels remain other surface; missing pixels are always '
                        'unknown. Areas count projected 100 m² cells.\n\n**The threshold is exploratory, not universal.** Existing '
                        'channels, smooth ground and radar shadow can produce dark returns. Wind, vegetation, soil moisture and '
                        'acquisition conditions affect interpretation. Filtering blurs narrow features and has reduced support near AOI '
                        'boundaries. Isolated detections, scene-wide darkening and subpixel registration need further study. Historical '
                        'water maps cannot establish flooding on these dates. Inspected date-matched optical references were '
                        'cloud/shadow masked. Independent validation is unavailable; no accuracy or confidence score is claimed.',
    'dash.footer': '{app} · Case study: Louisiana · Real cached NASA data · Exploratory science, openly stated limits',
}

TR = {
    'dash.title': 'Vaka çalışması: Louisiana',
    'dash.intro': '**{app}** uygulamasının bir parçası · bir Louisiana sulak alanında radar gözlemlerini ve **[[candidate|aday]] yüzey suyu '
                  'değişimini** keşfedin.',
    'dash.open_workflow': 'Araştırmacı iş akışını aç',
    'dash.warning': 'Keşif amaçlı yüzey suyu değişimi adayları. Taşkın TEYİT EDİLMEMİŞTİR. Bağımsız doğrulama mevcut değil.',
    'dash.spinner': 'Yerel radar verileri doğrulanıyor…',
    'dash.error': 'Yerel veriler doğrulanamadı ({error}). data/ içindeki 2. kilometre taşı alt kümelerini ve 3. kilometre taşı üst verilerini '
                  'geri yükleyin. Hiçbir indirme denenmedi.',
    'dash.explore': 'Sinyali keşfet',
    'dash.two_obs': 'İki gerçek gözlem · Yerel önbellek verileri',
    'dash.threshold': 'Su eşiği (dB)',
    'dash.threshold_help': 'Filtrelenmiş HH ≤ eşik ise su adayıdır. Bu keşif amaçlı bir ayardır.',
    'dash.minimum': 'En küçük geri saçılım değişimi (dB)',
    'dash.minimum_help': 'Geçişler için |sonra − önce| ≥ bu değer gerekir. Sıfır, büyüklük kapısını kaldırır.',
    'dash.singletons': 'Tek pikselli değişim adaylarını bastır (isteğe bağlı)',
    'dash.singletons_help': '8-bağlantılı tek pikselli genişleme ve çekilme gruplarını ayrı ayrı bastırır. Gerçek dar özellikleri '
                            'silebilir. Kalıcı ve bilinmeyen pikseller değişmez.',
    'dash.fixed': 'Sabit: doğrusal güçte 3 × 3 maskeye duyarlı ortalama, ardından dB dönüşümü.',
    'dash.sensitivity_info': 'Eşikler duyarlılığı keşfeder. Taşkını doğrulamazlar.',
    'dash.grid_note': 'HH · 10 m ızgara · EPSG:32615\n\nKimlik bilgisi ya da NASA indirmesi gerekmez.',
    'dash.dates': 'ÖNCE 21 Haziran 2026, 11:19 UTC → SONRA 3 Temmuz 2026, 11:19 UTC · Louisiana, ABD',
    'dash.metric.expansion': 'Aday genişleme',
    'dash.metric.recession': 'Aday çekilme',
    'dash.metric.net': 'Net aday değişim',
    'dash.metric.valid_area': 'Geçerli karşılaştırma alanı',
    'dash.settings': 'Su eşiği {threshold} dB · En küçük değişim {minimum} dB · {pixels} ortak geçerli piksel',
    'dash.filter_on': 'İsteğe bağlı boyut filtresi AÇIK: {count} tek başına duran değişim adayı piksel bastırıldı. Doğrulanmış kuru arazi '
                      'olarak değil, diğer geçerli yüzey olarak gösterilirler. Gerçek küçük su özellikleri kaybolabilir. Radar değerleri değişmedi.',
    'dash.interpretation': 'Bilimsel yorum',
    'dash.interpretation_text': '**Daha karanlık radar taşkının kanıtı değildir.** Mevcut kanallar, düz zemin, bitki örtüsü, rüzgâr ve toprak '
                                'nemi dönüşü değiştirebilir.\n\n**[[threshold|Eşik]] duyarlılığı:** aday alanlar keşif amaçlı su eşiğine ve '
                                'değişim kapısına göre değişir. Duyarlılık sekmesini kullanın; hiçbir eşik daha büyük bir alan için '
                                'optimize edilmedi.\n\n**Sahne geneli kararma:** ortak ilgi alanının medyan değişimi **{median} dB**. Bu adayları '
                                'etkileyebilir ama kanıtlanmış bir algılayıcı yanlılığı değildir. Sahne kayması düzeltmesi uygulanmadı. Bu '
                                'büyüklükte uzamsal olarak tekdüze bir kayma tek başına varsayılan 3 dB kapısının altındadır.\n\n**Bağımsız '
                                'doğrulama mevcut değil.** İncelenen aynı günkü optik referanslar bulut/gölge altındaydı. Tarihî su yolları '
                                'bağlam sağlar, taşkın kanıtı değil. Tekil piksel bastırma isteğe bağlıdır ve bilimsel güveni artırmaz.',
    'dash.tab.geo': 'Coğrafi harita',
    'dash.tab.radar': 'Radar ve su adayları',
    'dash.tab.sensitivity': 'Eşik duyarlılığı',
    'dash.tab.source': 'Veri ve bilimsel bağlam',
    'dash.easting': 'Doğu koordinatı (m)',
    'dash.northing': 'Kuzey koordinatı (m)',
    'dash.gamma0': 'Gamma-0 (dB)',
    'dash.geo_caption': 'Yukarıdaki ölçümlerle aynı sınıflar, geçerli kaydırıcı ayarları için, OpenStreetMap altlığı üzerinde. Gösterim Web '
                        'Mercator\'a en yakın komşu yöntemiyle yeniden örneklenir; alanlar her zaman özgün 10 m ızgarada hesaplanır. Altlık '
                        'internet gerektirir; katman yereldir.',
    'dash.geo_missing': 'Coğrafi katman mevcut değil ({error}); sonraki sekmedeki radar panelleri etkilenmez.',
    'dash.panel.before': 'Önce: SAR geri saçılımı',
    'dash.panel.before_caption': '21 Haziran 2026 · filtrelenmiş HH',
    'dash.panel.after': 'Sonra: SAR geri saçılımı',
    'dash.panel.after_caption': '3 Temmuz 2026 · filtrelenmiş HH',
    'dash.panel.difference': 'Geri saçılım farkı',
    'dash.panel.difference_caption': 'Sonra − önce · negatif = kararma',
    'dash.panel.classes': 'Aday yüzey suyu değişimi',
    'dash.panel.classes_caption': 'Keşif amaçlı sınıflar · bilinmeyen bilinmeyen olarak kalır',
    'dash.legend': 'SINIF AÇIKLAMASI: Gri-mavi = bilinmiyor / veri yok · Mavi = kalıcı su adayı · Turkuaz = yeni su adayı · Turuncu = '
                   'çekilmiş su adayı · Açık gri = diğer geçerli yüzey (değişim kapısının reddettiği geçişler dahil).',
    'dash.scale': 'Önce/sonra aynı gösterim ölçeğini paylaşır. Yüzdelik gösterim sınırları bilimsel verileri asla kırpmaz.',
    'dash.sens_title': 'Ne kadarı eşiğe bağlı?',
    'dash.sens_text': 'Her nokta, seçilen en küçük değişim kullanılarak gerçek radar dizilerinden hesaplanır.',
    'dash.sens.expansion': 'Genişleme (km²)',
    'dash.sens.recession': 'Çekilme (km²)',
    'dash.sens.selected': 'Seçilen eşik',
    'dash.sens.xlabel': 'Keşif amaçlı su eşiği (dB)',
    'dash.sens.ylabel': 'Aday alan (km²)',
    'dash.sens_table': 'Grafiğin arkasındaki değerler',
    'dash.sens_caption': 'Duyarlılık doğruluk değildir. Hiçbir eşik aday alanı en büyük yapmak için seçilmedi.',
    'dash.source_title': 'İki gözlem. Şeffaf bir işleme kaydı.',
    'dash.source_table': 'Ürünler, dosyalar ve ilgi alanı',
    'dash.source.pol': 'HH / HHHH yoğunluğu',
    'dash.aoi': 'Louisiana, ABD · Boylam −90,310020 ile −90,250797° · Enlem 29,902604 ile 29,924476° · EPSG:32615 · 10 m pikseller.',
    'dash.checked': 'Kaynak kimlikleri, dosya parmak izleri, etiketler ve dB değerleri önceki işleme kayıtlarına göre kontrol edilir. Alanlar '
                    'derece değil, projeksiyonlu metre kullanır.',
    'dash.quality': 'Temel kalite kontrolü (−16 dB / 3 dB, geçerli kaydırıcı sonucu değil): {count} genişleme adayından {near} tanesi tarihî '
                    'haritalanmış kanal/derelere 30 m\'den yakın. Aynı günkü optik referans pencereleri bulut/gölge ile maskelenmişti. '
                    'Bu taşkın doğrulaması değildir.',
    'dash.quality_missing': 'İsteğe bağlı kalite raporu eksik. Bağımsız doğrulama hâlâ mevcut değil.',
    'dash.links': '[NASA ASF NISAR Cookbook](https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/) · '
                  '[Bağımsız optik referans: DSWx-HLS](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-HLS_V1) · '
                  '[Tarihî USGS hidrografisi](https://www.usgs.gov/national-hydrography/access-national-hydrography-products)',
    'dash.product_link': '[{date} NASA katalog ürün bağlantısı]({url})',
    'dash.method': 'Yöntem ve bilimsel sınırlar',
    'dash.method_text': '[[nisar]] Dünya yüzeyinden gelen radar saçılımını ölçer. **[[hh]]**, yatay gönderilip yatay alınan radar demektir. '
                        '[[gcov]] **HHHH** katmanı radyometrik olarak araziye göre düzeltilmiş gamma-0 [[backscatter|geri saçılım]] gücüdür.\n\n'
                        'Geçerli pozitif güç maskelerinin kesişimini alır, **doğrusal güçte 3 × 3 normalize ortalama** uygular '
                        '([[speckle|benek gürültüsünü]] azaltır), geçersiz merkezleri korur, ardından **[[db]] = 10 × log10(güç)** hesaplarız. '
                        'Değişim **sonra dB − önce dB** olarak tanımlanır.\n\nSeçilen eşikte ya da altında olan bir **su adayıdır**. İki tarih '
                        'de altında: kalıcı aday. Aşağı geçiş: yeni aday. Yukarı geçiş: çekilmiş aday. Geçişler mutlak değişim kontrolünü de '
                        'karşılamalıdır. Diğer geçerli pikseller diğer yüzey olarak kalır; eksik pikseller her zaman bilinmeyendir. Alanlar '
                        'projeksiyonlu 100 m² hücreleri sayar.\n\n**Eşik keşif amaçlıdır, evrensel değildir.** Mevcut kanallar, düz zemin ve '
                        'radar gölgesi karanlık dönüşler üretebilir. Rüzgâr, bitki örtüsü, toprak nemi ve çekim koşulları yorumu etkiler. '
                        'Filtreleme dar özellikleri bulanıklaştırır ve ilgi alanı sınırlarına yakın daha az destek alır. Tek başına '
                        'tespitler, sahne geneli kararma ve piksel altı hizalama daha fazla çalışma gerektirir. Tarihî su haritaları bu '
                        'tarihlerde taşkını kanıtlayamaz. İncelenen tarihi eşleşen optik referanslar bulut/gölge ile maskelenmişti. Bağımsız '
                        'doğrulama mevcut değil; doğruluk ya da güven puanı iddia edilmez.',
    'dash.footer': '{app} · Vaka çalışması: Louisiana · Önbellekteki gerçek NASA verileri · Keşif amaçlı bilim, açıkça belirtilen sınırlar',
}

# Leaflet legend / tooltip text produced by the map builders (src/case_map.py, src/geographic_map.py,
# src/time_series_map.py); replaced in the HTML when Turkish is selected.
MAP_PAIRS_TR = [
    ('Unvalidated candidate<br>surface-water changes', 'Doğrulanmamış aday<br>yüzey suyu değişimleri'),
    ('Actual valid processed footprint', 'Gerçek geçerli işlenmiş ayak izi'),
    ('Actual common valid footprint', 'Gerçek ortak geçerli ayak izi'),
    ('Six-date common valid footprint', 'Altı tarihli ortak geçerli ayak izi'),
    ('Six-date common area', 'Altı tarihli ortak alan'),
    ('Sampled pixel center', 'Örneklenen piksel merkezi'),
    ('Persistent water candidate', 'Kalıcı su adayı'),
    ('New water candidate (possible expansion)', 'Yeni su adayı (olası genişleme)'),
    ('New water candidate', 'Yeni su adayı'),
    ('Receded water candidate', 'Çekilmiş su adayı'),
    ('Other valid surface', 'Diğer geçerli yüzey'),
    ('native grid', 'özgün ızgara'),
    ('Transparent = NoData', 'Saydam = Veri yok'),
    ('NOT confirmed flooding', 'Taşkın TEYİT EDİLMEDİ'),
    ('not confirmed flooding', 'taşkın teyit edilmedi'),
    ('Not a NISAR accuracy score.', 'NISAR doğruluk puanı değildir.'),
]
