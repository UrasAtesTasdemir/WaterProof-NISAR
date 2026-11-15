"""Evidence & limitations checklist (src/evidence.py) and its page (src/evidence_panel.py)."""

EN = {
    'ev.rule.offset': 'caution if fewer than half of the baseline expansion pixels remain candidates after removing the measured scene-wide median change',
    'ev.rule.threshold': 'caution if candidate expansion area changes by more than a factor of 2 for a ±2 dB threshold change',
    'ev.rule.singletons': 'caution if more than 10% of expansion pixels are isolated single pixels',
    'ev.rule.waterways': 'caution if most (> 50%) expansion pixels lie within 30 m of mapped canals/streams (ambiguous: channel-edge change vs existing water)',
    'ev.rule.reference': 'no concern only if an independent reference meets ≤24 h timing and ≥80% valid coverage on both dates',
    'ev.rule.registration': 'no concern if the best integer shift within ±2 px is (0, 0); subpixel registration stays unknown',
    'ev.rule.quality_mask': 'no concern if every common pixel carries the GCOV valid-subswath mask code on both dates',
    'ev.rule.cross_pol': 'caution if the new-water candidates have median HV at/below the scene 5th percentile (possible noise floor); '
                         'otherwise neutral (unknown), because the noise floor is not quantified. Never counted as support.',
    'ev.rule.timing': 'caution if the first post-event acquisition misses the documented peak by more than 24 h',
    'ev.rule.coverage': 'no concern if at least one compatible pair covers the full area of interest',
    'ev.title.offset': 'Scene-wide darkening',
    'ev.title.threshold': 'Threshold sensitivity',
    'ev.title.singletons': 'Isolated pixels',
    'ev.title.waterways': 'Distance to mapped waterways',
    'ev.title.reference': 'Independent reference',
    'ev.title.registration': 'Co-registration (integer shifts)',
    'ev.title.quality_mask': 'Product quality mask',
    'ev.title.cross_pol': 'Cross-polarization (HV) signal level',
    'ev.title.timing': 'Timing relative to the event',
    'ev.title.coverage': 'Footprint coverage',
    'ev.find.offset': 'The whole scene darkened by a median {median} dB, cause unknown. If that offset is removed, only {kept} of {base} '
                      'expansion pixels ({share}) remain candidates ({area} vs {area0} km²).',
    'ev.find.threshold': 'Expansion area is {a14} km² at −14 dB, {a16} km² at −16 dB, {a18} km² at −18 dB and {a20} km² at −20 dB '
                         '(3 dB change gate). A ±2 dB choice moves the area by up to ×{worst}.',
    'ev.find.singletons': '{count} of {total} expansion pixels ({share}) are isolated single pixels; {groups} groups in total, '
                          'the largest only {largest} pixels ({m2} m²).',
    'ev.find.waterways': '{near} of {total} expansion pixels ({share}) lie within 30 m of historical USGS NHD canals/streams. That fits '
                         'water-level or edge changes along existing channels, but also existing water, mixed pixels or small '
                         'misregistration. It is context, not validation.',
    'ev.same_day_item': '{date}: {share} valid',
    'ev.none_inspected': 'none inspected',
    'ev.find.reference': 'No independent reference qualifies: {reason} Same-day optical (DSWx-HLS) windows: {same} (cloud/shadow); the '
                         'best inspected reference ({collection}, {date}) reached {best} valid coverage but is {hours} h from the nearest '
                         'NISAR date. Later-date pair search: {decision}.',
    'ev.find.registration': 'Best integer shift is ({row}, {col}) px, gradient correlation {corr}. {limitation}',
    'ev.code_item': 'code {code} × {count}',
    'ev.find.quality_mask': 'GCOV valid-sample mask on the common pixels: {listing} (code 1 = valid, fully focused subswath). '
                            'Both products report noiseCorrectionApplied=False.',
    'ev.find.cross_pol': "New-water candidates: median ΔHH {dhh} dB but ΔHV only {dhv} dB, with HV near the scene's darkest levels "
                         '({d0} / {d1} dB). HV may be floor-limited; its noise floor is not quantified.',
    'ev.find.cross_pol_missing': 'Not available: data/hv outputs are missing. Run scripts/process_hv_compass.py (offline).',
    'ev.find.not_available': 'Not available: no NISAR change map was produced for this case, so this check cannot be computed.',
    'ev.before': 'before',
    'ev.after': 'after',
    'ev.after_item': '{share} valid ({date})',
    'ev.none_valid': 'none with valid pixels',
    'ev.find.k_reference': '{inspected} DSWx-HLS windows inspected; {valid} had any valid pixels (best {best} on {date}, {relation} the '
                           'gauge peak). Best window after the peak: {after}. DSWx-S1 hits: {hits}. Decision: {decision}.',
    'ev.find.timing': 'Earliest post-event NISAR is {hours} h after the provisional gauge peak ({station}); stage had already fallen to '
                      '{stage} ft. The event maximum is not observed.',
    'ev.find.coverage': '{pairs} compatible 12-day pairs; {full} cover the full AOI, one track covers about {share}.',
    'ev.head.exploratory': 'Louisiana exploration: no independent reference with matching timing and coverage exists for these pairs, so these findings are not validated.',
    'ev.head.concerns': 'Some checks raise concerns; read the warnings before using any result.',
    'ev.head.none': 'No check raised a concern, which is still not validation.',
    'ev.head.several': 'Several independent checks warn: treat the candidates as weak evidence.',
    'evp.badge.pass': '🟢 No concern from this check',
    'evp.badge.warn': '🟠 Caution',
    'evp.badge.unknown': '❔ Unknown / not quantified',
    'evp.counts': '{ok} no concern · {warn} caution · {unknown} unknown',
    'evp.rule_source': 'Rule: {rule} · Source: `{source}`',
    'evp.legend': '"No concern from this check" means one specific check raised nothing; it does not make a result correct. '
                  '"Unknown" means the evidence needed for that check does not exist or is not quantified in the cached data.',
    'evp.title': 'Evidence review',
    'evp.intro': '**What supports or weakens these change [[candidate|candidates]]?** One checklist that gathers evidence already computed and '
                 'saved for each case. Each line states its rule, the numbers it used and the file they came from.',
    'evp.warning': 'This is an evidence checklist, not validation and not a confidence or accuracy score: no independent reference '
                   'with matching timing and coverage exists for these NISAR pairs.',
    'evp.case': 'Case',
    'evp.case.louisiana': 'Louisiana · 21 June → 3 July 2026 (baseline −16 dB / 3 dB)',
    'evp.case.kerrville': 'Kerrville, Texas · July 2026 (availability study only)',
    'evp.error': 'Saved evidence could not be read ({error}). Restore the reports in data/. No download was attempted.',
    'evp.baseline_note': 'Checks describe the saved baseline settings (−16 dB water threshold, 3 dB change gate, singleton filter off). '
                         'The case-study sliders explore other settings but do not update this checklist.',
    'evp.figures': 'Saved sensitivity figures behind this checklist',
    'evp.fig_threshold': 'Threshold sensitivity (saved)',
    'evp.fig_offset': 'Scene-offset sensitivity (saved, counterfactual)',
    'evp.fig_missing': '{caption}: figure not available ({path} missing).',
    'evp.details': 'Details of each check',
}

TR = {
    'ev.rule.offset': 'ölçülen sahne geneli medyan değişim çıkarıldıktan sonra temel genişleme piksellerinin yarısından azı aday olarak '
                      'kalırsa dikkat',
    'ev.rule.threshold': 'eşikte ±2 dB değişim, aday genişleme alanını 2 katından fazla değiştirirse dikkat',
    'ev.rule.singletons': 'genişleme piksellerinin %10\'undan fazlası tek başına duran piksellerse dikkat',
    'ev.rule.waterways': 'genişleme piksellerinin çoğu (> %50) haritalanmış kanal/derelere 30 m\'den yakınsa dikkat (belirsiz: kanal kenarı '
                         'değişimi mi, mevcut su mu)',
    'ev.rule.reference': 'yalnızca bağımsız bir referans her iki tarihte de ≤24 saat zamanlama ve ≥%80 geçerli kapsama sağlarsa sorun yok',
    'ev.rule.registration': '±2 piksel içindeki en iyi tam sayı kayma (0, 0) ise sorun yok; piksel altı hizalama bilinmiyor',
    'ev.rule.quality_mask': 'her ortak piksel iki tarihte de GCOV geçerli alt şerit maske kodunu taşıyorsa sorun yok',
    'ev.rule.cross_pol': 'yeni su adaylarının medyan HV değeri sahnenin %5\'lik yüzdeliğinde ya da altındaysa dikkat (olası gürültü tabanı); '
                         'aksi hâlde nötr (bilinmiyor), çünkü gürültü tabanı sayısal olarak belirlenmedi. Asla destek sayılmaz.',
    'ev.rule.timing': 'olaydan sonraki ilk çekim belgelenmiş zirveyi 24 saatten fazla kaçırırsa dikkat',
    'ev.rule.coverage': 'en az bir uyumlu çift tüm ilgi alanını kapsıyorsa sorun yok',
    'ev.title.offset': 'Sahne geneli kararma',
    'ev.title.threshold': 'Eşik duyarlılığı',
    'ev.title.singletons': 'Tek başına duran pikseller',
    'ev.title.waterways': 'Haritalanmış su yollarına uzaklık',
    'ev.title.reference': 'Bağımsız referans',
    'ev.title.registration': 'Eş hizalama (tam sayı kaymalar)',
    'ev.title.quality_mask': 'Ürün kalite maskesi',
    'ev.title.cross_pol': 'Çapraz polarizasyon (HV) sinyal düzeyi',
    'ev.title.timing': 'Olaya göre zamanlama',
    'ev.title.coverage': 'Ayak izi kapsaması',
    'ev.find.offset': 'Tüm sahne medyan {median} dB karardı, nedeni bilinmiyor. Bu kayma çıkarılırsa {base} genişleme pikselinden yalnızca '
                      '{kept} tanesi ({share}) aday olarak kalıyor ({area} / {area0} km²).',
    'ev.find.threshold': 'Genişleme alanı −14 dB\'de {a14} km², −16 dB\'de {a16} km², −18 dB\'de {a18} km² ve −20 dB\'de {a20} km² '
                         '(3 dB değişim kapısı). ±2 dB\'lik bir seçim alanı ×{worst} kata kadar değiştiriyor.',
    'ev.find.singletons': '{total} genişleme pikselinden {count} tanesi ({share}) tek başına duran piksel; toplam {groups} grup var, '
                          'en büyüğü yalnızca {largest} piksel ({m2} m²).',
    'ev.find.waterways': '{total} genişleme pikselinden {near} tanesi ({share}) tarihî USGS NHD kanal/derelerine 30 m\'den yakın. Bu, mevcut '
                         'kanallar boyunca su düzeyi ya da kenar değişimlerine uyar, ama mevcut su, karışık pikseller ya da küçük hizalama '
                         'hatasına da uyar. Bu doğrulama değil, bağlamdır.',
    'ev.same_day_item': '{date}: {share} geçerli',
    'ev.none_inspected': 'incelenen yok',
    'ev.find.reference': 'Hiçbir bağımsız referans uygun değil: {reason} Aynı günkü optik (DSWx-HLS) pencereler: {same} (bulut/gölge); '
                         'incelenen en iyi referans ({collection}, {date}) {best} geçerli kapsamaya ulaştı ama en yakın NISAR tarihinden '
                         '{hours} saat uzakta. Sonraki tarih çifti araması: {decision}.',
    'ev.find.registration': 'En iyi tam sayı kayma ({row}, {col}) piksel, gradyan korelasyonu {corr}. {limitation}',
    'ev.code_item': 'kod {code} × {count}',
    'ev.find.quality_mask': 'Ortak piksellerde GCOV geçerli örnek maskesi: {listing} (kod 1 = geçerli, tam odaklanmış alt şerit). '
                            'İki ürün de noiseCorrectionApplied=False bildiriyor.',
    'ev.find.cross_pol': 'Yeni su adayları: medyan ΔHH {dhh} dB ama ΔHV yalnızca {dhv} dB; HV sahnenin en karanlık düzeylerine yakın '
                         '({d0} / {d1} dB). HV tabanla sınırlı olabilir; gürültü tabanı sayısal olarak belirlenmedi.',
    'ev.find.cross_pol_missing': 'Mevcut değil: data/hv çıktıları eksik. scripts/process_hv_compass.py betiğini (çevrimdışı) çalıştırın.',
    'ev.find.not_available': 'Mevcut değil: bu vaka için NISAR değişim haritası üretilmedi, bu yüzden bu kontrol hesaplanamaz.',
    'ev.before': 'önce',
    'ev.after': 'sonra',
    'ev.after_item': '{share} geçerli ({date})',
    'ev.none_valid': 'geçerli pikseli olan yok',
    'ev.find.k_reference': '{inspected} DSWx-HLS penceresi incelendi; {valid} tanesinde geçerli piksel vardı (en iyisi {date} tarihinde {best}, '
                           'ölçüm istasyonu zirvesinden {relation}). Zirveden sonraki en iyi pencere: {after}. DSWx-S1 eşleşmeleri: {hits}. '
                           'Karar: {decision}.',
    'ev.find.timing': 'Olaydan sonraki en erken NISAR çekimi, geçici ölçüm istasyonu zirvesinden {hours} saat sonra ({station}); su düzeyi '
                      'zaten {stage} ft\'e düşmüştü. Olayın en yüksek noktası gözlenmedi.',
    'ev.find.coverage': '{pairs} uyumlu 12 günlük çift; {full} tanesi tüm ilgi alanını kapsıyor, bir iz yaklaşık {share} kapsıyor.',
    'ev.head.exploratory': 'Louisiana incelemesi: bu çiftler için zamanı ve kapsamı eşleşen bağımsız referans yok; bu nedenle bu bulgular doğrulanmış değildir.',
    'ev.head.concerns': 'Bazı kontroller endişe doğuruyor; herhangi bir sonucu kullanmadan önce uyarıları okuyun.',
    'ev.head.none': 'Hiçbir kontrol endişe doğurmadı; bu yine de doğrulama değildir.',
    'ev.head.several': 'Birkaç bağımsız kontrol uyarı veriyor: adayları zayıf kanıt olarak değerlendirin.',
    'evp.badge.pass': '🟢 Bu kontrolden endişe yok',
    'evp.badge.warn': '🟠 Dikkat',
    'evp.badge.unknown': '❔ Bilinmiyor / sayısal değil',
    'evp.counts': '{ok} endişe yok · {warn} dikkat · {unknown} bilinmiyor',
    'evp.rule_source': 'Kural: {rule} · Kaynak: `{source}`',
    'evp.legend': '"Bu kontrolden endişe yok", belirli bir kontrolün hiçbir sorun bulmadığı anlamına gelir; bir sonucu doğru yapmaz. '
                  '"Bilinmiyor", o kontrol için gereken kanıtın önbellekteki verilerde bulunmadığı ya da sayısal olarak belirlenmediği anlamına gelir.',
    'evp.title': 'Kanıt incelemesi',
    'evp.intro': '**Bu değişim [[candidate|adaylarını]] ne destekliyor ya da zayıflatıyor?** Her vaka için önceden hesaplanıp kaydedilmiş '
                 'kanıtları toplayan tek bir kontrol listesi. Her satır kuralını, kullandığı sayıları ve geldikleri dosyayı belirtir.',
    'evp.warning': 'Bu bir kanıt kontrol listesidir; doğrulama, güven ya da doğruluk puanı değildir: bu NISAR çiftleri için zamanlaması ve '
                   'kapsaması eşleşen bağımsız bir referans yok.',
    'evp.case': 'Vaka',
    'evp.case.louisiana': 'Louisiana · 21 Haziran → 3 Temmuz 2026 (temel −16 dB / 3 dB)',
    'evp.case.kerrville': 'Kerrville, Teksas · Temmuz 2026 (yalnızca erişilebilirlik çalışması)',
    'evp.error': 'Kayıtlı kanıtlar okunamadı ({error}). data/ içindeki raporları geri yükleyin. Hiçbir indirme denenmedi.',
    'evp.baseline_note': 'Kontroller kayıtlı temel ayarları açıklar (−16 dB su eşiği, 3 dB değişim kapısı, tekil piksel filtresi kapalı). '
                         'Vaka çalışmasındaki kaydırıcılar başka ayarları keşfeder ama bu listeyi güncellemez.',
    'evp.figures': 'Bu listenin arkasındaki kayıtlı duyarlılık şekilleri',
    'evp.fig_threshold': 'Eşik duyarlılığı (kayıtlı)',
    'evp.fig_offset': 'Sahne kayması duyarlılığı (kayıtlı, karşı-olgusal)',
    'evp.fig_missing': '{caption}: şekil mevcut değil ({path} eksik).',
    'evp.details': 'Her kontrolün ayrıntıları',
}
