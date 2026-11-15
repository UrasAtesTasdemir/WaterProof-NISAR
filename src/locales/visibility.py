"""'Is this scene analyzable?' page (src/visibility_panel.py) and case notes (src/visibility.py)."""

EN = {
    'vis.case.louisiana': 'Louisiana (USA)',
    'vis.case.kerrville': 'Kerrville, Texas (USA)',
    'vis.note.louisiana': "No documented flood event in the cached records for this AOI; {station} returned '{status}' for {start}…{end}.",
    'vis.note.kerrville': 'Provisional gauge peak {value} ft at {station} ({time}). {warning}',
    'vis.fig.nisar': 'NISAR acquisition · footprint coverage of AOI',
    'vis.fig.usable': 'usable',
    'vis.fig.not_usable': 'not usable (cloud/shadow or no data)',
    'vis.fig.reference': 'Reference (DSWx) valid share · {text} ({count})',
    'vis.fig.peak': 'Documented gauge peak',
    'vis.fig.ylabel': '% of area of interest',
    'vis.fig.title': '{name} · shaded band = usable (≥{usable})',
    'vis.fig.suptitle': 'Radar availability vs usable optical coverage (cached catalog and AOI window results)',
    'vis.m.acquisitions': 'NISAR acquisitions (cached search)',
    'vis.m.pairs': 'Compatible pairs (same track/frame/mode)',
    'vis.m.full': 'Pairs covering the full AOI',
    'vis.m.optical': 'Optical refs ≥{usable} valid',
    'vis.m.optical_value': '{usable} of {inspected}',
    'vis.first_after': 'First NISAR acquisition after the documented peak: {hours} h later. The event maximum is not observed.',
    'vis.pairs_title': 'Compatible acquisition pairs',
    'vis.no_event': 'no event documented',
    'vis.col.track': 'Track', 'vis.col.frame': 'Frame', 'vis.col.direction': 'Direction', 'vis.col.before': 'Before (UTC)',
    'vis.col.after': 'After (UTC)', 'vis.col.interval': 'Interval (days)', 'vis.col.coverage': 'Shared AOI coverage',
    'vis.col.method': 'Coverage method', 'vis.col.spans': 'Spans documented event',
    'vis.method.intersection': 'geometric intersection',
    'vis.method.upper': 'upper bound (min of single-date coverage; footprints unavailable)',
    'vis.refs_title': 'Independent optical / radar references inspected over the AOI',
    'vis.col.collection': 'Collection', 'vis.col.acquired': 'Acquired (UTC)', 'vis.col.valid': 'Valid share of AOI',
    'vis.col.cloud': 'Tile cloud cover (metadata)', 'vis.col.cells': 'Cloud/shadow cells', 'vis.col.status': 'Status',
    'vis.col.hours': 'Hours from event',
    'vis.cells': '{cloud} of {cells}',
    'vis.reason.usable': 'usable',
    'vis.reason.cloud': 'mostly cloud / cloud shadow',
    'vis.reason.nodata': 'mostly no data (outside swath / not observed)',
    'vis.reason.few': 'too few valid cells',
    'vis.refs_caption': 'Tile cloud cover is catalog metadata for the whole tile; the valid share is measured inside the AOI window. '
                        'Saved decision for this case: **{decision}**. Sources: {sources}',
    'vis.title': 'Is this scene analyzable?',
    'vis.cached_only': 'Cached cases only: Louisiana and Kerrville. This page does not search other places.',
    'vis.intro': '**Is a place analyzable at all?** Before reading any [[change_map]], check whether compatible radar pairs exist '
                 '(same [[track_frame]]), how much of the area their [[footprint|footprints]] cover, how they are timed relative to an '
                 'event, and whether independent [[reference]] could ever check the result.',
    'vis.info': 'Cached results from earlier catalog searches and small AOI window reads. Nothing on this page queries NASA live.',
    'vis.error': 'Cached catalog results could not be read ({error}). No download was attempted.',
    'vis.fig_caption': 'Radar sees through cloud: every NISAR acquisition here covers the area it images. In these two cases, optical '
                       'references were rarely usable: clouds, cloud shadow and missing data took out most windows.',
    'vis.kerrville_checklist': 'Evidence checklist for Kerrville (availability study, no change map)',
    'vis.meaning': 'What "compatible" and "usable" mean here',
    'vis.meaning_text': '- **Compatible pair:** same orbit [[track_frame]], direction and radar mode, so viewing geometry matches.\n'
                        '- **Usable reference:** at least {usable} of the AOI is valid (water or not-water) in the DSWx product, the same '
                        'conservative guardrail used in the saved pair-selection study. Not a universal standard.\n'
                        '- A usable reference is still not ground truth: 30 m optical pixels, different water definitions and hours of '
                        'timing difference matter.',
}

TR = {
    'vis.case.louisiana': 'Louisiana (ABD)',
    'vis.case.kerrville': 'Kerrville, Teksas (ABD)',
    'vis.note.louisiana': "Bu ilgi alanı için önbellekteki kayıtlarda belgelenmiş bir taşkın olayı yok; {station}, {start}…{end} için "
                          "'{status}' döndürdü.",
    'vis.note.kerrville': '{station} istasyonunda geçici zirve {value} ft ({time}). {warning}',
    'vis.fig.nisar': 'NISAR çekimi · ilgi alanının ayak izi kapsaması',
    'vis.fig.usable': 'kullanılabilir',
    'vis.fig.not_usable': 'kullanılamaz (bulut/gölge ya da veri yok)',
    'vis.fig.reference': 'Referans (DSWx) geçerli payı · {text} ({count})',
    'vis.fig.peak': 'Belgelenmiş istasyon zirvesi',
    'vis.fig.ylabel': 'İlgi alanının %\'si',
    'vis.fig.title': '{name} · gölgeli bant = kullanılabilir (≥{usable})',
    'vis.fig.suptitle': 'Radar erişilebilirliği ve kullanılabilir optik kapsama (önbellekteki katalog ve ilgi alanı penceresi sonuçları)',
    'vis.m.acquisitions': 'NISAR çekimleri (önbellekteki arama)',
    'vis.m.pairs': 'Uyumlu çiftler (aynı iz/çerçeve/mod)',
    'vis.m.full': 'Tüm ilgi alanını kapsayan çiftler',
    'vis.m.optical': '≥{usable} geçerli optik referanslar',
    'vis.m.optical_value': '{inspected} içinden {usable}',
    'vis.first_after': 'Belgelenmiş zirveden sonraki ilk NISAR çekimi: {hours} saat sonra. Olayın en yüksek noktası gözlenmedi.',
    'vis.pairs_title': 'Uyumlu çekim çiftleri',
    'vis.no_event': 'belgelenmiş olay yok',
    'vis.col.track': 'İz', 'vis.col.frame': 'Çerçeve', 'vis.col.direction': 'Yön', 'vis.col.before': 'Önce (UTC)',
    'vis.col.after': 'Sonra (UTC)', 'vis.col.interval': 'Aralık (gün)', 'vis.col.coverage': 'Ortak ilgi alanı kapsaması',
    'vis.col.method': 'Kapsama yöntemi', 'vis.col.spans': 'Belgelenmiş olayı kapsıyor',
    'vis.method.intersection': 'geometrik kesişim',
    'vis.method.upper': 'üst sınır (tek tarih kapsamalarının en küçüğü; ayak izleri yok)',
    'vis.refs_title': 'İlgi alanı üzerinde incelenen bağımsız optik / radar referansları',
    'vis.col.collection': 'Koleksiyon', 'vis.col.acquired': 'Çekim (UTC)', 'vis.col.valid': 'İlgi alanının geçerli payı',
    'vis.col.cloud': 'Pafta bulut örtüsü (üst veri)', 'vis.col.cells': 'Bulut/gölge hücreleri', 'vis.col.status': 'Durum',
    'vis.col.hours': 'Olaydan saat farkı',
    'vis.cells': '{cells} içinden {cloud}',
    'vis.reason.usable': 'kullanılabilir',
    'vis.reason.cloud': 'çoğunlukla bulut / bulut gölgesi',
    'vis.reason.nodata': 'çoğunlukla veri yok (şerit dışında / gözlenmemiş)',
    'vis.reason.few': 'çok az geçerli hücre',
    'vis.refs_caption': 'Pafta bulut örtüsü tüm pafta için katalog üst verisidir; geçerli pay ilgi alanı penceresinin içinde ölçülür. '
                        'Bu vaka için kayıtlı karar: **{decision}**. Kaynaklar: {sources}',
    'vis.title': 'Bu sahne analiz edilebilir mi?',
    'vis.cached_only': 'Yalnızca önbellekteki vakalar: Louisiana ve Kerrville. Bu sayfa başka yerleri aramaz.',
    'vis.intro': '**Bir yer hiç analiz edilebilir mi?** Herhangi bir [[change_map|değişim haritasını]] okumadan önce uyumlu radar '
                 'çiftlerinin (aynı [[track_frame]]) olup olmadığını, [[footprint|ayak izlerinin]] alanın ne kadarını kapsadığını, bir olaya '
                 'göre nasıl zamanlandıklarını ve bağımsız [[reference|referans verinin]] sonucu hiç kontrol edip edemeyeceğini inceleyin.',
    'vis.info': 'Önceki katalog aramalarından ve küçük ilgi alanı penceresi okumalarından önbelleğe alınmış sonuçlar. Bu sayfadaki hiçbir şey '
                'NASA\'yı canlı sorgulamaz.',
    'vis.error': 'Önbellekteki katalog sonuçları okunamadı ({error}). Hiçbir indirme denenmedi.',
    'vis.fig_caption': 'Radar bulutun arasından görür: buradaki her NISAR çekimi görüntülediği alanı kapsar. Bu iki vakada optik referanslar '
                       'nadiren kullanılabildi: bulutlar, bulut gölgesi ve eksik veriler çoğu pencereyi kullanılamaz hâle getirdi.',
    'vis.kerrville_checklist': 'Kerrville için kanıt listesi (erişilebilirlik çalışması, değişim haritası yok)',
    'vis.meaning': 'Burada "uyumlu" ve "kullanılabilir" ne demek',
    'vis.meaning_text': '- **Uyumlu çift:** aynı yörünge [[track_frame|izi/çerçevesi]], yön ve radar modu; böylece bakış geometrisi eşleşir.\n'
                        '- **Kullanılabilir referans:** DSWx ürününde ilgi alanının en az {usable} kısmı geçerlidir (su ya da su değil); '
                        'kayıtlı çift seçimi çalışmasında kullanılan temkinli sınırla aynı. Evrensel bir standart değildir.\n'
                        '- Kullanılabilir bir referans yine de yer gerçeği değildir: 30 m optik pikseller, farklı su tanımları ve saatlerce '
                        'zamanlama farkı önemlidir.',
}
