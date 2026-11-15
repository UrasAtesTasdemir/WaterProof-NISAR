"""Shipped offline demo places on the Explore page (src/demo_places.py, data/demo_cache/)."""

EN = {
    'ex.preset.marmara_lake': 'Marmara Lake, Türkiye (cached, works offline)',
    'ex.preset.central_valley': 'Central Valley, California (cached, works offline)',
    'ex.preset.mekong_delta': 'Mekong Delta, Vietnam (cached, works offline)',
    'ex.demo.why.marmara_lake': 'Shallow lake basin and wetland in western Türkiye; chosen by the team as a lake/wetland surface type.',
    'ex.demo.why.central_valley': 'Irrigated agricultural fields; chosen as an agriculture surface type.',
    'ex.demo.why.mekong_delta': 'River delta with rice paddies; chosen as a delta surface type.',
    'ex.demo.title': 'Cached demo place: works offline',
    'ex.demo.info': '**{name}** · {lat}, {lon} · {window} km × {window} km window · {count} dates: {dates}  \n'
                    'Why chosen: {why}  \nSelection rule (fixed before any radar data were read): largest compatible '
                    '[[hh]]+[[hv]] group, its first {count} dates. Results are shown as computed, whatever they are.',
    'ex.demo.products': 'Product IDs',
    'ex.demo.snapshot': 'Catalog snapshot from {date}',
    'ex.demo.snapshot_caption': 'Catalog snapshot from {date} (saved public search, {count} products). It works offline; '
                                'the live catalog may list more acquisitions today.',
    'ex.demo.pending': 'This demo place is listed, but its radar windows are not in the shipped cache yet (pending a pre-warm '
                       'run with a token). Its catalog snapshot is still shown.',
    'ex.fixed_mode_demo': 'Mode: shipped offline demo place. Its dates and window are fixed; the date/window controls are '
                          'disabled. Select Custom for live exploration.',
    'ex.source.demo': 'shipped offline demo cache',
}

TR = {
    'ex.preset.marmara_lake': 'Marmara Gölü, Türkiye (önbellekte, çevrimdışı çalışır)',
    'ex.preset.central_valley': 'Central Valley, Kaliforniya (önbellekte, çevrimdışı çalışır)',
    'ex.preset.mekong_delta': 'Mekong Deltası, Vietnam (önbellekte, çevrimdışı çalışır)',
    'ex.demo.why.marmara_lake': 'Batı Türkiye\'de sığ bir göl havzası ve sulak alan; ekip tarafından göl/sulak alan yüzey türü olarak seçildi.',
    'ex.demo.why.central_valley': 'Sulanan tarım alanları; tarım yüzey türü olarak seçildi.',
    'ex.demo.why.mekong_delta': 'Çeltik tarlalarının bulunduğu bir nehir deltası; delta yüzey türü olarak seçildi.',
    'ex.demo.title': 'Önbellekteki gösterim yeri: çevrimdışı çalışır',
    'ex.demo.info': '**{name}** · {lat}, {lon} · {window} km × {window} km pencere · {count} tarih: {dates}  \n'
                    'Neden seçildi: {why}  \nSeçim kuralı (hiçbir radar verisi okunmadan önce sabitlendi): en büyük uyumlu '
                    '[[hh]]+[[hv]] grubu, ilk {count} tarihi. Sonuçlar ne çıkarsa hesaplandığı gibi gösterilir.',
    'ex.demo.products': 'Ürün kimlikleri',
    'ex.demo.snapshot': '{date} tarihli katalog anlık görüntüsü',
    'ex.demo.snapshot_caption': '{date} tarihli katalog anlık görüntüsü (kaydedilmiş herkese açık arama, {count} ürün). '
                                'Çevrimdışı çalışır; canlı katalog bugün daha fazla çekim listeleyebilir.',
    'ex.demo.pending': 'Bu gösterim yeri listeleniyor ama radar pencereleri henüz paketlenen önbellekte yok (anahtarla bir ön '
                       'ısıtma çalıştırması bekleniyor). Katalog anlık görüntüsü yine de gösterilir.',
    'ex.fixed_mode_demo': 'Mod: paketlenmiş çevrimdışı gösterim yeri. Tarihleri ve penceresi sabittir; tarih/pencere kontrolleri '
                          'kapalıdır. Canlı keşif için Özel seçin.',
    'ex.source.demo': 'paketlenmiş çevrimdışı gösterim önbelleği',
}
