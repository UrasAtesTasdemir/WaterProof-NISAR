"""'Start here' opening panel and the guided example on the Explore page (src/start_here.py, src/explore_panel.py)."""

EN = {
    'start.title': 'Start here',
    'start.problem_title': 'The problem',
    'start.problem': 'Radar [[change_map|change maps]] look convincing, but they are hard to trust. A darker pixel can mean calmer '
                     'water, wetter soil, flattened plants, a different viewing geometry or plain [[speckle]].',
    'start.do_title': 'What you can do',
    'start.do': 'Pick a place on the globe, choose dates and see what [[nisar]] radar recorded, what the change might be, what else '
                'could explain it and how fragile it is. Then download a short note with what to check next.',
    'start.not_title': 'What this tool does NOT claim',
    'start.not': 'Louisiana findings are exploratory. Thailand and Gandak have case-specific comparisons with independent water products, and new locations do not inherit those scores. The app does not confirm flooding.',
    'start.steps_title': 'How to read the results',
    'start.step1': '**1. Select an example**  \nStart with the cached Thailand case or a Louisiana research candidate.',
    'start.step2': '**2. Observe the change**  \nCompare real radar observations and their dates.',
    'start.step3': '**3. Check uncertainty**  \nRead the case-specific evidence and alternative explanations.',
    'start.step4': '**4. Investigate next**  \nExport a note with what to verify next.',
    'start.guided': 'Take the guided example',
    'start.guided_help': 'Opens the cached Thailand case (Prachin Buri, 6 → 30 Sep 2026) and candidate open-water map. Its reference comparison is case-specific. No token needed.',
    'start.hide': 'Hide this introduction',
    'start.show': 'Show “Start here”',
    'ex.preset.louisiana_c1': 'Louisiana candidate 1 (cached, works offline)',
    'ex.example_caption': 'Example pair: the saved screening flagged this interval for candidate 1; other pairs, including '
                          'first-to-last, are one click away.',
    'ex.c1.title': 'Candidate 1 on its own footprint (saved researcher workflow)',
    'ex.c1.scale': 'The square above covers {square} pixels around candidate 1; the candidate’s own [[footprint]] is only {pixels} '
                   'pixels, so its change is diluted in the square’s reading. Both readings are shown as computed.',
    'ex.c1.reading': '**Footprint reading, {d1} → {d2}:** {observation}',
    'ex.c1.limits': '**Candidate 1’s own limits**',
    'ex.c1.size': 'Small region: {pixels} pixels ({area} km²).',
    'ex.c1.open': 'Open candidate 1 in the researcher workflow',
    'ex.c1.unavailable': 'The saved candidate 1 checks are not available ({error}).',
}

TR = {
    'start.title': 'Buradan başlayın',
    'start.problem_title': 'Sorun',
    'start.problem': 'Radar [[change_map|değişim haritaları]] ikna edici görünür ama güvenmek zordur. Daha karanlık bir piksel daha '
                     'sakin su, daha ıslak toprak, yatmış bitkiler, farklı bir bakış geometrisi ya da yalnızca [[speckle]] olabilir.',
    'start.do_title': 'Neler yapabilirsiniz',
    'start.do': 'Küre üzerinde bir yer seçin, tarihleri belirleyin ve [[nisar]] radarının ne kaydettiğini, değişimin ne olabileceğini, '
                'başka neyin açıklayabileceğini ve sonucun ne kadar kırılgan olduğunu görün. Ardından bir sonraki adımda neyin '
                'kontrol edileceğini anlatan kısa bir not indirin.',
    'start.not_title': 'Bu aracın iddia ETMEDİKLERİ',
    'start.not': 'Louisiana bulguları keşif amaçlıdır; Tayland ve Gandak bağımsız su ürünleriyle vakaya özgü karşılaştırılmıştır. Yeni alanlar bu puanları devralmaz. Teyit edilmiş taşkın iddia edilmez.',
    'start.steps_title': 'Sonuçlar nasıl okunur',
    'start.step1': '**1. Örnek seçin**  \nÖnbellekteki Tayland vakasıyla veya Louisiana araştırma adayıyla başlayın.',
    'start.step2': '**2. Değişimi görün**  \nGerçek radar gözlemlerini ve tarihlerini karşılaştırın.',
    'start.step3': '**3. Belirsizliği inceleyin**  \nVakaya özgü kanıtları ve alternatif açıklamaları okuyun.',
    'start.step4': '**4. Sonraki adımı belirleyin**  \nNeyin doğrulanması gerektiğini anlatan notu indirin.',
    'start.guided': 'Rehberli örneği açın',
    'start.guided_help': 'Önbellekteki Tayland vakasını (Prachin Buri, 6 → 30 Eyl 2026) ve açık su adayı haritasını açar. Referans karşılaştırması bu vakaya özgüdür. Anahtar gerekmez.',
    'start.hide': 'Bu tanıtımı gizle',
    'start.show': '“Buradan başlayın” bölümünü göster',
    'ex.preset.louisiana_c1': 'Louisiana 1. aday (önbellekte, çevrimdışı çalışır)',
    'ex.example_caption': 'Örnek çift: kayıtlı tarama bu aralığı 1. aday için işaretledi; ilk-son dahil diğer çiftler bir tık uzakta.',
    'ex.c1.title': '1. aday kendi ayak izinde (kayıtlı araştırmacı iş akışı)',
    'ex.c1.scale': 'Yukarıdaki kare 1. adayın çevresinde {square} pikseli kapsıyor; adayın kendi [[footprint]] alanı yalnızca {pixels} '
                   'piksel, bu yüzden değişimi karenin okumasında seyreliyor. İki okuma da hesaplandığı gibi gösterilir.',
    'ex.c1.reading': '**Ayak izi okuması, {d1} → {d2}:** {observation}',
    'ex.c1.limits': '**1. adayın kendi sınırları**',
    'ex.c1.size': 'Küçük bölge: {pixels} piksel ({area} km²).',
    'ex.c1.open': '1. adayı araştırmacı iş akışında aç',
    'ex.c1.unavailable': 'Kayıtlı 1. aday kontrolleri kullanılamıyor ({error}).',
}
