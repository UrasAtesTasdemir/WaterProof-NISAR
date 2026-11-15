"""Placebo (null) check in the researcher workflow and its review note (src/placebo.py, data/placebo/)."""

EN = {
    'pl.title': 'Placebo check',
    'pl.caption': 'How unusual is this region’s contrast compared with random regions of the same size? It does not tell us why.',
    'pl.intro': 'The candidate’s exact shape was placed at many random valid spots in the same window; each copy was compared '
                'with its own 50–150 m ring in the same interval. The spread of those values is the [[null_distribution]]; the '
                '[[exceedance]] is the share of copies at least as extreme as the candidate.',
    'pl.not_available': 'Placebo check not available: the saved outputs in data/placebo are missing or changed '
                        '(run scripts/process_placebo.py).',
    'pl.not_enough': 'Not enough valid placements: {n} kept, {minimum} required. No number is shown.',
    'pl.interval': 'Computed for the candidate’s seed interval {d1} → {d2} (the selected pair may differ): {n} placements kept '
                   'of {draws} random draws, seed {seed}.',
    'pl.line': '**{band}:** candidate minus ring {value} dB. Random placements: median {median} dB, 5th–95th percentile '
               '{p05} to {p95} dB. {count} of {n} placements were at least as large in absolute value (exceedance fraction {fraction}).',
    'pl.limits': 'Candidates were selected because they changed a lot in this interval and random regions were not, so this '
                 'comparison is incomplete. Nearby placements are not independent (the 100 m minimum spacing is a simplification), '
                 'and no correction is applied for comparing five candidates and two channels. Not a significance test; not '
                 'evidence of a cause.',
    'pl.fig.xlabel': '{band}: region minus ring change (dB)',
    'pl.fig.ylabel': 'Placements',
    'pl.fig.candidate': 'Candidate {id}',
    'pl.fig.band_null': '{band} random placements',
    'pl.note': '- Placebo check (seed interval {d1} → {d2}; {n} random same-shape placements; seed {seed}): exceedance '
               'fraction HH {hh}, HV {hv}. Descriptive only: candidates were selected for large change, no multiple-comparison '
               'correction, not a significance test.',
    'pl.note_missing': '- Placebo check: not available (saved outputs missing or changed).',
    'pl.note_not_enough': '- Placebo check: not enough valid placements ({n} of {minimum}); no number given.',
}

TR = {
    'pl.title': 'Plasebo kontrolü',
    'pl.caption': 'Bu bölgenin çevresiyle karşıtlığı, aynı büyüklükteki rastgele bölgelere göre ne kadar sıra dışı? Nedenini söylemez.',
    'pl.intro': 'Adayın tam şekli aynı pencerede birçok rastgele geçerli noktaya yerleştirildi; her kopya aynı aralıkta kendi '
                '50–150 m halkasıyla karşılaştırıldı. Bu değerlerin yayılımı [[null_distribution]]; [[exceedance]] ise en az aday '
                'kadar uç olan kopyaların payıdır.',
    'pl.not_available': 'Plasebo kontrolü kullanılamıyor: data/placebo içindeki kayıtlı çıktılar eksik ya da değişmiş '
                        '(scripts/process_placebo.py çalıştırın).',
    'pl.not_enough': 'Yeterli geçerli yerleşim yok: {n} tutuldu, {minimum} gerekli. Sayı gösterilmiyor.',
    'pl.interval': 'Adayın tohum aralığı {d1} → {d2} için hesaplandı (seçili çift farklı olabilir): {draws} rastgele denemeden '
                   '{n} yerleşim tutuldu, tohum {seed}.',
    'pl.line': '**{band}:** aday eksi halka {value} dB. Rastgele yerleşimler: medyan {median} dB, %5–%95 aralığı {p05} ile '
               '{p95} dB. {n} yerleşimden {count} tanesi mutlak değerce en az bu kadar büyüktü (aşım oranı {fraction}).',
    'pl.limits': 'Adaylar bu aralıkta çok değiştikleri için seçildi, rastgele bölgeler değil; bu yüzden karşılaştırma eksiktir. '
                 'Yakın yerleşimler birbirinden bağımsız değildir (100 m asgari aralık bir basitleştirmedir) ve beş aday ile iki '
                 'kanalın karşılaştırılması için düzeltme uygulanmaz. Anlamlılık testi değildir; bir nedene kanıt değildir.',
    'pl.fig.xlabel': '{band}: bölge eksi halka değişimi (dB)',
    'pl.fig.ylabel': 'Yerleşim',
    'pl.fig.candidate': '{id}. aday',
    'pl.fig.band_null': '{band} rastgele yerleşimler',
    'pl.note': '- Plasebo kontrolü (tohum aralığı {d1} → {d2}; aynı şekilde {n} rastgele yerleşim; tohum {seed}): aşım oranı '
               'HH {hh}, HV {hv}. Yalnızca betimleyici: adaylar büyük değişim için seçildi, çoklu karşılaştırma düzeltmesi yok, '
               'anlamlılık testi değil.',
    'pl.note_missing': '- Plasebo kontrolü: kullanılamıyor (kayıtlı çıktılar eksik ya da değişmiş).',
    'pl.note_not_enough': '- Plasebo kontrolü: yeterli geçerli yerleşim yok ({n} / {minimum}); sayı verilmedi.',
}
