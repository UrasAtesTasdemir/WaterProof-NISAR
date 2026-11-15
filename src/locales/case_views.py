"""Louisiana sub-views: time series, geographic map, polarization, investigation explorer, diagnostics."""

EN = {
    # Six-date HH time series
    'ts.title': 'Case study: Louisiana · HH time series',
    'ts.warning': 'Exploratory NISAR surface dynamics. NOT confirmed water or flooding. Independent change validation unavailable.',
    'ts.caption': 'Six real L-band GCOV HHHH observations · original Louisiana AOI · Sentinel-1 benchmark scores do not establish NISAR HH accuracy.',
    'ts.spinner': 'Verifying local six-date HH cube…',
    'ts.error': 'Verified six-date outputs are missing or inconsistent. Restore data/time_series/ or run scripts/process_time_series.py '
                'locally. No download was attempted.',
    'ts.sidebar': 'Explore six dates',
    'ts.first': 'Observation date',
    'ts.second': 'Comparison date',
    'ts.layer': 'Geographic layer',
    'ts.layer.0': 'Selected observation',
    'ts.layer.1': 'Comparison observation',
    'ts.layer.2': 'Comparison − selected (dB)',
    'ts.layer.3': 'Selected anomaly (dB)',
    'ts.sidebar_note': 'Cached real HH only. No NASA download on interaction.',
    'ts.m.obs': 'Real observations',
    'ts.m.common': 'Six-date valid area',
    'ts.m.pair': 'Selected-pair valid area',
    'ts.selected': 'Selected {first} → comparison {second}. Change = comparison minus selected; dates may be reversed.',
    'ts.identical': 'Identical dates selected: the valid-pixel difference is exactly zero.',
    'ts.point_title': 'Choose a point or small neighborhood',
    'ts.lon': 'Longitude (°E)',
    'ts.lat': 'Latitude (°N)',
    'ts.neighborhood': 'Neighborhood',
    'ts.pixels': '{n} × {n} native pixels',
    'ts.apply': 'Apply point',
    'ts.sampled': 'Requested lon/lat {lon}, {lat}; sampled pixel center {plon}, {plat}. Native row {row}, column {col}. Red marker = sampled center.',
    'ts.map_alt': 'Interactive Louisiana six-date HH map',
    'ts.map_caption': 'Pan/zoom and toggle the raster/footprint. Map values are nearest-resampled display pixels; native data and masks are '
                      'preserved. OSM/Leaflet need internet; radar arrays are local.',
    'ts.chart_title': 'HH backscatter at the selected location',
    'ts.fig.median': 'Median valid filtered HH (dB)',
    'ts.fig.selected': 'Selected',
    'ts.fig.comparison': 'Comparison',
    'ts.fig.ylabel': 'Gamma-0 (dB)',
    'ts.fig.xlabel': 'Actual acquisition date (UTC)',
    'ts.available': '{available}/6 valid observations; {missing} missing. Each point is the median of finite filtered dB in the selected '
                    'neighborhood. Missing dates are not filled; dates are not interpolated. The 3×3 linear-power speckle filter is already applied.',
    'ts.point_table': 'Values at this point',
    'ts.method': 'Scene distributions, provenance and scientific method',
    'ts.method_caption': 'Statistics use the fixed six-date common footprint. The difference between scene medians is not generally the '
                         'median of pixel-wise differences.',
    'ts.method_text': '**[[nisar]] measures radar scattering**, not water depth. [[lband]] and [[polarization]] help explore surface and '
                      'vegetation dynamics. This view shows HH (HHHH) only. Matching HV (HVHV) windows for all six dates are processed and '
                      'compared with HH in the HH/HV analysis and the researcher workflow.\n\n**Processing:** existing 3×3 mask-aware mean '
                      'in positive linear power, then 10 log10; 10 m EPSG:32615. Per-date validity is preserved. Pair differences exclude '
                      'either-date NoData. The saved common cube excludes any pixel missing on any of the six dates.\n\n**Exploratory '
                      'anomaly:** selected-date dB minus the per-pixel six-date temporal median, in dB. It is not a z-score or calibrated '
                      'probability. Zero variation gives zero; histories with fewer than four finite dates remain unknown. Six sparse dates '
                      'do not establish a climatology or event timing.\n\n**No scene normalization is applied.** Scene-wide darkening could '
                      'reflect environmental, geometric, noise or processing effects; sensor bias is not established. No causal attribution '
                      'or new radiometric correction is made here.\n\n**Limits:** backscatter change alone is not flooding. [[speckle|Speckle]], '
                      'vegetation, wind, moisture, mixed pixels, registration and provisional processing affect interpretation. Suitable '
                      'independent paired validation remains unavailable. The Sentinel-1 benchmark evaluates a different adapter.',
    # Geographic map
    'geo.title': 'Case study: Louisiana · Geographic map',
    'geo.warning': 'Unvalidated candidate surface-water changes. NOT confirmed flooding. Independent validation unavailable.',
    'geo.caption': 'Real NISAR GCOV frequency-A HH / HHHH · 21 June → 3 July 2026. Sentinel-1 benchmark scores do not apply here.',
    'geo.none': 'No processed geographic output found. Run scripts/process_geographic_area.py locally first. No download was attempted.',
    'geo.coverage': 'Processed coverage',
    'geo.spinner': 'Preparing cached geographic overlays…',
    'geo.error': 'Geographic output could not be verified ({error}). Original NISAR workspace remains available.',
    'geo.m.expansion': 'Candidate expansion',
    'geo.m.recession': 'Candidate recession',
    'geo.m.valid': 'Actual valid comparison area',
    'geo.requested': 'Requested {size} × {size} km; boundary shows actual common valid pixels. Measurements use full-resolution 10 m '
                     'EPSG:32615 cells. Water threshold −16 dB; |change| ≥3 dB; 3×3 linear-power filter; singleton suppression OFF.',
    'geo.alt': 'Interactive Louisiana NISAR candidate-water map',
    'geo.howto': 'Use +/− or the mouse wheel to zoom, drag to pan, and the layer checkboxes to hide/show candidates. The overlays are '
                 'nearest-resampled Web Mercator display rasters (≤768 pixels per side); no-data stays transparent. Small features may '
                 'disappear at display scale. Area calculations always use native resolution.',
    'geo.internet': 'OSM basemap and Leaflet libraries require an internet connection; radar overlays and measurements use local cached '
                    'outputs only. The map is not a validated flood map.',
    'geo.provenance': 'Coverage and data provenance',
    # Polarization
    'pol.title': 'Case study: Louisiana · Polarization Analysis',
    'pol.warning': 'Exploratory HH/HV scattering. NOT confirmed flooding or flooded vegetation. Independent validation unavailable.',
    'pol.caption': 'Real NISAR frequency-A HHHH / HVHV · original Louisiana AOI. Sentinel-1 benchmark scores do not establish NISAR accuracy.',
    'pol.spinner': 'Verifying local HH/HV observations…',
    'pol.error': 'Verified polarization outputs are missing or inconsistent. Restore data/polarization_analysis/ or run '
                 'scripts/process_polarization.py locally. No download was attempted.',
    'pol.sidebar': 'Compare polarizations',
    'pol.first': 'Selected date',
    'pol.second': 'Comparison date',
    'pol.band': 'Radar band',
    'pol.sidebar_note': '3×3 mean in joint-valid linear power; then dB. No new classifier or scene correction.',
    'pol.ratio_label': 'HH/HV power ratio (dB)',
    'pol.band_label': '{band} gamma-0 (dB)',
    'pol.footprint': 'All-date joint HH/HV valid footprint',
    'pol.legend_range': '{low} → {high} dB (display only)',
    'pol.legend_dark': 'Dark → light = lower → higher power',
    'pol.legend_ratio': 'Purple → yellow = lower → higher ratio',
    'pol.legend_nodata': 'Transparent = NoData · 10 m native pixels',
    'pol.legend_note': 'Exploratory scattering; NOT confirmed flooding.',
    'pol.m.area': 'Joint pair valid area',
    'pol.m.dhh': 'Median Δ HH',
    'pol.m.dhv': 'Median Δ HV',
    'pol.selected': '{n} real HH/HV dates · selected {first} → comparison {second}. Δ = comparison minus selected. Fixed all-date joint area {area} km².',
    'pol.identical': 'Identical dates: valid HH and HV changes are zero; correlation is undefined.',
    'pol.geo_title': 'Geographic band comparison',
    'pol.ratio_info': 'Dimensionless linear power ratio = filtered HH power / filtered HV power. In dB: 10 log10(HH/HV) = HH_dB − HV_dB. '
                      'This is not a vegetation/flood probability; weak HV can destabilize ratios.',
    'pol.role.selected': 'Selected',
    'pol.role.comparison': 'Comparison',
    'pol.maps_caption': 'HH/HV radar maps use one shared absolute dB scale; all before/after change panels share a symmetric scale. Native '
                        'values are never clipped. Map display is nearest-resampled to ≤640 pixels per side; OSM/Leaflet require internet.',
    'pol.change_title': 'HH and HV before, after and change',
    'pol.relation': 'HH versus HV change and temporal statistics',
    'pol.undefined': 'undefined (constant change)',
    'pol.pearson': 'Spatial Pearson r = {r}; descriptive association, NOT accuracy. {pixels} spatially dependent pixels. Median ΔHH − ΔHV = {diff} dB.',
    'pol.fig.median': '{band} spatial median',
    'pol.fig.ylabel': 'Filtered gamma-0 (dB)',
    'pol.fig.xlabel': 'Actual acquisition UTC',
    'pol.stats_caption': 'Spatial medians/IQRs use a fixed all-date joint mask. Difference of medians need not equal median pixel-wise '
                         'change. Irregular dates are not interpolated; these are spatial distributions, not uncertainty intervals.',
    'pol.physics': 'Physical interpretation, source layers and limitations',
    'pol.physics_text': '**[[hh]]** transmits and receives horizontal polarization. **[[hv]]** transmits horizontal and receives vertical '
                        'polarization. Their different responses can help explore scattering structure and depolarization.\n\nSmooth open '
                        'water may be weak in both channels; vegetation structure, surface roughness, wind, moisture, geometry and mixed '
                        'pixels can also change their returns. A scattering difference is an observation; its physical cause remains an '
                        'inference. Increasing HH or an HH/HV contrast does **not** identify flooded vegetation by itself.\n\nNo new '
                        'water/vegetation classifier, confidence score, normalization or noise-floor correction is applied. Weak '
                        'cross-polarized returns may be noise-sensitive (see the [[noise_floor]] notes in Scientific diagnostics). The '
                        'original HH threshold tool and its results remain unchanged. Independent date-matched reference validation remains unavailable.',
    # Investigation explorer
    'inv.title': 'Case study: Louisiana · Investigation Explorer',
    'inv.warning': 'Radar-change investigation candidates. NOT validated floods, flood risk, environmental damage or calibrated confidence. '
                   'Independent confirmation is unavailable.',
    'inv.caption': 'Help researchers decide where and when to investigate. Six real NISAR HH/HV observations · Louisiana · original '
                   'processed AOI. Sentinel-1 benchmark metrics do not apply to these candidates.',
    'inv.spinner': 'Verifying cached investigation regions…',
    'inv.error': 'Verified investigation outputs are missing or inconsistent. Restore data/investigation_engine/ or run '
                 'scripts/build_investigations.py locally. No download or original-result recomputation was attempted.',
    'inv.none': 'No meaningful localized candidate regions met the declared rules. No synthetic region or forced top-five result was substituted.',
    'inv.select': 'Investigation region',
    'inv.region': 'Region {id}',
    'inv.select_note': 'Select a region here to update the chart and report. Map popups provide location context; numbers are heuristic order.',
    'inv.m.area': 'Selected native-grid area',
    'inv.m.notable': 'Notable sampled intervals',
    'inv.m.common': 'Processed common area',
    'inv.point': 'Region {id}: representative longitude {lon}°, latitude {lat}° · {pixels} common valid 10 m cells. The representative '
                 'point is inside the actual polygon.',
    'inv.map.alt': 'Numbered Louisiana investigation regions',
    'inv.map.footprint': 'Actual six-date processed footprint',
    'inv.map.footprint_tip': 'Actual common processed area: {area} km²',
    'inv.map.group': 'Investigation candidates (heuristic order)',
    'inv.map.label': 'Region {id} · {area} km² · {count}/5 notable intervals',
    'inv.map.popup': 'Select this number in the region list to inspect its time series.',
    'inv.map.legend': '<b>Radar-change investigation candidates</b><br>Numbers = heuristic order, NOT risk/confidence.<br>Orange = selected; '
                      'teal = other candidates.<br>Boundary = actual processed footprint.<br>Unvalidated; not confirmed floods or damage.',
    'inv.map_caption': 'Use the numbered region list for selection. The initial map fits the candidates; zoom out to inspect the full {area} '
                       'km² processed boundary. Map popups/layers provide context. OSM/Leaflet require internet; scientific data and exports are local.',
    'inv.why': 'Why investigate region {id}?',
    'inv.ranges': 'Median pixel-wise six-date range: HH {hh} dB; HV {hv} dB. These ranges describe observed variation, not an '
                  'environmental severity score.',
    'inv.adjacent': 'Notable adjacent intervals are not independent recurring events: a single unusual date can cause both a rise and a '
                    'fall. Observed persistence does not establish continuous conditions between acquisitions.',
    'inv.chart_title': 'HH/HV observations on this fixed geographic region',
    'inv.fig.median': '{band} spatial median/IQR',
    'inv.fig.ylabel': 'Filtered gamma-0 (dB)',
    'inv.fig.xlabel': 'Actual acquisition UTC',
    'inv.chart_caption': 'All six observations are valid on the fixed selected cells. Bars show spatial IQR, not confidence. Points are not '
                         'interpolated across the 12/24-day sampling gaps; 10 m spacing does not imply independent samples.',
    'inv.stats_table': 'Per-date statistics for this region',
    'inv.dates': 'Dates, recurrence and observed departures',
    'inv.dates_caption': 'Median pixel-wise differences need not equal differences of region medians. Scene medians and percentile cutoffs '
                         'are context, not offsets subtracted from the data.',
    'inv.longest': 'Longest run of observed ≥3 dB departures in the seed direction: {n} sampled dates. This is not a continuous event duration.',
    'inv.sensitivity': 'Sensitivity and scientific interpretation',
    'inv.retained': 'Across nine declared filter/magnitude settings, {low}–{high} of these {pixels} cells remain in eligible connected change '
                    'regions. These are overlap counts, not confidence; regions are not reranked for a dramatic result.',
    'inv.variants': 'Variants: 1/3/5-pixel linear mean and 2.5/3/3.5 dB magnitude floors. Each recomputes the scene absolute-change '
                    'percentile and applies the same connected-size rule; retention need not vary monotonically with smoothing.',
    'inv.next': 'Suggested next scientific step: ',
    'inv.phase4': 'Original-pair Phase4 temporal-scaled diagnostic support: {support}/{pixels} cells. This is a different, fixed-pair '
                  'diagnostic and is not independent validation or a ranking input.',
    'inv.rules': 'Selection rules, provenance and limitations',
    'inv.rules_text': 'HH alone drives screening because the calibrated HV [[noise_floor]] is unresolved. Each seed must exceed the scene '
                      'absolute-change 90th percentile and the 3 dB floor, with at least 25 same-date/sign four-connected cells. The '
                      'percentile is an AOI-relative tail rule, not statistical significance. Uniform scene shifts have no localized tail '
                      'and are not converted into investigation polygons.',
    'inv.download': 'Download selected investigation report (Markdown)',
    'inv.export_caption': 'Export includes real acquisition IDs, coordinates, statistics, criteria, setting sensitivity, limitations and a '
                          'suggested investigation step (English). Original water-change and benchmark results remain separate and unchanged.',
    # Diagnostics
    'diag.title': 'Case study: Louisiana · Scientific Diagnostics',
    'diag.warning': 'Exploratory reliability diagnostics. NOT independently validated flooding, noise probabilities or calibrated '
                    'uncertainty. Original measurements and classifier are unchanged.',
    'diag.spinner': 'Loading cached scientific diagnostics…',
    'diag.error': 'Scientific diagnostic outputs are missing or inconsistent. Restore data/scientific_diagnostics/. No download or '
                  'production recomputation was attempted.',
    'diag.sidebar': 'Inspect reliability',
    'diag.band': 'Diagnostics band',
    'diag.interval': 'Change interval',
    'diag.sidebar_note': 'Six cached real dates · no NASA access · no benchmark test tuning.',
    'diag.m.median': 'Median selected change',
    'diag.m.mad': 'Robust spatial dispersion (1.4826 MAD)',
    'diag.m.area': 'Common comparison area',
    'diag.chosen': '{band}: {comparison} minus {selected} · {count} spatially dependent pixels. Dispersion is not sensor error or '
                   'confidence. Sentinel-1 benchmark scores do not establish NISAR accuracy.',
    'diag.tab.dist': 'Temporal distributions',
    'diag.tab.methods': 'Baseline vs alternative',
    'diag.tab.sens': 'Threshold sensitivity',
    'diag.tab.noise': 'Texture & quality',
    'diag.fig.median': '{band} spatial median/IQR',
    'diag.fig.ylabel': 'Filtered gamma-0 (dB)',
    'diag.fig.xlabel': 'Actual acquisition UTC',
    'diag.fig.hist_x': '{band} change (dB) · {comparison} minus {selected}',
    'diag.fig.hist_y': 'Pixel count per bin',
    'diag.tails': 'Histogram tails outside ±15 dB: below {below}, above {above}. Saved robust statistics include all valid pixels. No '
                  'median normalization is applied.',
    'diag.pairwise_table': 'All pairwise distributions',
    'diag.col.region': 'Region', 'diag.col.hh': 'HH median Δ dB', 'diag.col.hv': 'HV median Δ dB', 'diag.col.row': 'Native row',
    'diag.col.column': 'Native column',
    'diag.quiet': 'Candidate quiet-looking patches',
    'diag.quiet_caption': 'Original June21/July3 changes above. Three 210 m tiles were selected using later-four-date stability and spatial '
                          'texture, away from historical waterways. These selected patches are not verified invariant calibration targets; '
                          'they cannot distinguish environmental effects from sensor/geometry effects.',
    'diag.fixed': '**Fixed original comparison: 21 June → 3 July, HH ≤ −16 dB, 3×3 linear-power filter.** The interval/band selectors only '
                  'affect the distribution view.',
    'diag.col.gate': 'Diagnostic gate', 'diag.col.expansion': 'Expansion candidate km²', 'diag.col.recession': 'Recession candidate km²',
    'diag.gate.fixed': 'Original |Δ| ≥3 dB',
    'diag.gate.scaled': 'Reference-temporal-scaled |S| ≥3',
    'diag.fig.expansion': 'Expansion candidate',
    'diag.fig.recession': 'Recession candidate',
    'diag.fig.fixed': 'Fixed 3 dB',
    'diag.fig.scaled': 'Temporal-scaled diagnostic',
    'diag.fig.km2': 'Candidate km²',
    'diag.reference_scale': 'The reference scale uses July15, July27, August20 and September1 only; **June21 and July3 are left out**. The '
                            'denominator includes environmental temporal variation, not just noise. The 1 dB floor and dimensionless cutoff 3 '
                            'are exploratory regularizers, **not noise estimates or 3σ significance**. Zero reference spread uses the floor; '
                            'missing references stay unknown.',
    'diag.retrospective': 'Retrospective diagnostic only: genuine changes in the later reference dates can inflate MAD and suppress real '
                          'transitions. Four references cannot establish a calibrated stable baseline or real-time detection rule.',
    'diag.effective': 'Effective gate: median {median} dB; 95th spatial percentile {p95} dB. The floor guarantees a gate ≥3 dB, so fewer '
                      'candidates are expected by construction and do not establish better accuracy. The original classifier is not replaced.',
    'diag.quantity': 'Sensitivity quantity',
    'diag.q.expansion_km2': 'expansion_km2',
    'diag.q.recession_km2': 'recession_km2',
    'diag.fig.filter': '{size}×{size} linear mean',
    'diag.fig.threshold': 'Exploratory HH water threshold (dB)',
    'diag.fig.area': 'Candidate area (km²)',
    'diag.sens_table': 'All sensitivity settings',
    'diag.sens_caption': 'Fixed 3 dB change gate; no threshold is optimized against validation/test labels. Each variation is a separate '
                         'diagnostic, not a production result. All areas use native projected 10 m cells.',
    'diag.stability': 'Across all 12 scenarios: expansion in any setting {any} km²; in every setting {all} km². The strict −20 dB smoothed '
                      'settings yield zero candidates, so zero full-range intersection is not proof every candidate is false.',
    'diag.waterways': '{near}/{total} baseline expansion pixels are near historical mapped waterways. This is spatial context, not flood '
                      'confirmation; none were removed for proximity.',
    'diag.families': 'Stability families',
    'diag.families_caption': 'Within-family intersections isolate patterns stable under filter size alone or thresholds −14/−16/−18 alone. '
                             'This does not establish validation or confidence.',
    'diag.metadata': 'Actual GCOV quality metadata: original pair only',
    'diag.col.date': 'Date', 'diag.col.looks_med': 'Looks median', 'diag.col.looks_min': 'Looks min', 'diag.col.looks_max': 'Looks max',
    'diag.col.codes': 'Mask codes',
    'diag.looks_caption': 'numberOfLooks counts the adaptive averaging ensemble, not a measured ENL or an independent-sample count. Both '
                          'inspected AOI masks are code1 (valid subswath); code0 would mean partially focused/invalid ensemble, and 255 is '
                          'outside extent. Existing finite-positive masks were not altered.',
    'diag.texture_table': 'Local texture statistics',
    'diag.texture': '**Texture is not pure noise.** Raw local CV, spatial trends and adjacent-pixel correlation mix [[speckle]] and real '
                    'structure. Conditional ENL is reported only for raw patches passing declared stationarity, correlation and '
                    'looks-uniformity checks; it is a provisional spatial moment estimate, not thermal-noise calibration. Filtered pixels '
                    'are never used for ENL.',
    'diag.hv_floor': '**HV [[noise_floor]] remains unresolved.** Noise-equivalent HH/HV metadata exist on a coarse grid but are described '
                     'as **DN²**, while our science arrays are calibrated gamma-0. No direct division, noise-floor value or SNR is reported '
                     'without a verified calibration conversion. Both inspected products report `noiseCorrectionApplied=False`; this is '
                     'not proof of a known additive error in every pixel.',
    'diag.limits': '**Limits:** six dates do not establish a climatology; scene-wide and local variation may reflect moisture, vegetation, '
                   'wind, tides/drainage, registration, geometry, speckle or processing. No source is uniquely identified. Neither the '
                   'fixed gate nor the alternative is independently validated; no probabilities, accuracy or confidence percentages are produced.',
    'diag.flags': 'Processing flags',
}

TR = {
    'ts.title': 'Vaka çalışması: Louisiana · HH zaman serisi',
    'ts.warning': 'Keşif amaçlı NISAR yüzey dinamikleri. Su ya da taşkın TEYİT EDİLMEMİŞTİR. Bağımsız değişim doğrulaması mevcut değil.',
    'ts.caption': 'Altı gerçek L-bant GCOV HHHH gözlemi · orijinal Louisiana ilgi alanı · Sentinel-1 kıyaslama puanları NISAR HH doğruluğunu kanıtlamaz.',
    'ts.spinner': 'Yerel altı tarihli HH küpü doğrulanıyor…',
    'ts.error': 'Doğrulanmış altı tarihli çıktılar eksik ya da tutarsız. data/time_series/ klasörünü geri yükleyin ya da '
                'scripts/process_time_series.py betiğini yerelde çalıştırın. Hiçbir indirme denenmedi.',
    'ts.sidebar': 'Altı tarihi keşfet',
    'ts.first': 'Gözlem tarihi',
    'ts.second': 'Karşılaştırma tarihi',
    'ts.layer': 'Coğrafi katman',
    'ts.layer.0': 'Seçilen gözlem',
    'ts.layer.1': 'Karşılaştırma gözlemi',
    'ts.layer.2': 'Karşılaştırma − seçilen (dB)',
    'ts.layer.3': 'Seçilen anomali (dB)',
    'ts.sidebar_note': 'Yalnızca önbellekteki gerçek HH. Etkileşimde NASA indirmesi yok.',
    'ts.m.obs': 'Gerçek gözlemler',
    'ts.m.common': 'Altı tarihli geçerli alan',
    'ts.m.pair': 'Seçilen çiftin geçerli alanı',
    'ts.selected': 'Seçilen {first} → karşılaştırma {second}. Değişim = karşılaştırma eksi seçilen; tarihler ters olabilir.',
    'ts.identical': 'Aynı tarihler seçildi: geçerli piksel farkı tam olarak sıfır.',
    'ts.point_title': 'Bir nokta ya da küçük bir komşuluk seçin',
    'ts.lon': 'Boylam (°D)',
    'ts.lat': 'Enlem (°K)',
    'ts.neighborhood': 'Komşuluk',
    'ts.pixels': '{n} × {n} özgün piksel',
    'ts.apply': 'Noktayı uygula',
    'ts.sampled': 'İstenen boylam/enlem {lon}, {lat}; örneklenen piksel merkezi {plon}, {plat}. Özgün satır {row}, sütun {col}. Kırmızı '
                  'işaret = örneklenen merkez.',
    'ts.map_alt': 'Etkileşimli Louisiana altı tarihli HH haritası',
    'ts.map_caption': 'Kaydırın/yakınlaştırın ve raster/ayak izi katmanlarını açıp kapatın. Harita değerleri en yakın komşu ile yeniden '
                      'örneklenmiş gösterim pikselleridir; özgün veri ve maskeler korunur. OSM/Leaflet internet gerektirir; radar dizileri yereldir.',
    'ts.chart_title': 'Seçilen konumda HH geri saçılımı',
    'ts.fig.median': 'Geçerli filtrelenmiş HH medyanı (dB)',
    'ts.fig.selected': 'Seçilen',
    'ts.fig.comparison': 'Karşılaştırma',
    'ts.fig.ylabel': 'Gamma-0 (dB)',
    'ts.fig.xlabel': 'Gerçek çekim tarihi (UTC)',
    'ts.available': '6 gözlemden {available} tanesi geçerli; {missing} eksik. Her nokta, seçilen komşuluktaki sonlu filtrelenmiş dB '
                    'değerlerinin medyanıdır. Eksik tarihler doldurulmaz; tarihler arasında ara değer hesaplanmaz. 3×3 doğrusal güç benek '
                    'filtresi zaten uygulanmıştır.',
    'ts.point_table': 'Bu noktadaki değerler',
    'ts.method': 'Sahne dağılımları, kaynak ve bilimsel yöntem',
    'ts.method_caption': 'İstatistikler sabit altı tarihli ortak ayak izini kullanır. Sahne medyanları arasındaki fark genel olarak piksel '
                         'farklarının medyanına eşit değildir.',
    'ts.method_text': '**[[nisar]] radar saçılımını ölçer**, su derinliğini değil. [[lband|L-bant]] ve [[polarization|polarizasyon]], yüzey '
                      've bitki dinamiklerini keşfetmeye yardım eder. Bu görünüm yalnızca HH (HHHH) gösterir. Altı tarihin tümü için eşleşen '
                      'HV (HVHV) pencereleri işlenmiş ve HH/HV analizinde ve araştırmacı iş akışında HH ile karşılaştırılmıştır.\n\n'
                      '**İşleme:** pozitif doğrusal güçte mevcut 3×3 maskeye duyarlı ortalama, ardından 10 log10; 10 m EPSG:32615. Tarih '
                      'başına geçerlilik korunur. Çift farkları iki tarihten birinde veri olmayan pikselleri dışarıda bırakır. Kayıtlı ortak '
                      'küp, altı tarihten herhangi birinde eksik olan her pikseli dışarıda bırakır.\n\n**Keşif amaçlı anomali:** seçilen '
                      'tarihin dB değeri eksi piksel başına altı tarihli zamansal medyan, dB cinsinden. Bir z-puanı ya da kalibre edilmiş '
                      'olasılık değildir. Sıfır değişkenlik sıfır verir; dörtten az sonlu tarihi olan geçmişler bilinmeyen kalır. Altı seyrek '
                      'tarih bir iklim ortalaması ya da olay zamanlaması oluşturmaz.\n\n**Sahne normalizasyonu uygulanmadı.** Sahne geneli '
                      'kararma çevresel, geometrik, gürültü ya da işleme etkilerini yansıtabilir; algılayıcı yanlılığı kanıtlanmamıştır. '
                      'Burada nedensel bir atıf ya da yeni bir radyometrik düzeltme yapılmaz.\n\n**Sınırlar:** geri saçılım değişimi tek '
                      'başına taşkın değildir. [[speckle|Benek gürültüsü]], bitki örtüsü, rüzgâr, nem, karışık pikseller, hizalama ve geçici '
                      'işleme yorumu etkiler. Uygun bağımsız eşleşmiş doğrulama hâlâ mevcut değil. Sentinel-1 kıyaslaması farklı bir '
                      'uyarlamayı değerlendirir.',
    'geo.title': 'Vaka çalışması: Louisiana · Coğrafi harita',
    'geo.warning': 'Doğrulanmamış aday yüzey suyu değişimleri. Taşkın TEYİT EDİLMEMİŞTİR. Bağımsız doğrulama mevcut değil.',
    'geo.caption': 'Gerçek NISAR GCOV frekans A HH / HHHH · 21 Haziran → 3 Temmuz 2026. Sentinel-1 kıyaslama puanları burada geçerli değildir.',
    'geo.none': 'İşlenmiş coğrafi çıktı bulunamadı. Önce scripts/process_geographic_area.py betiğini yerelde çalıştırın. Hiçbir indirme denenmedi.',
    'geo.coverage': 'İşlenmiş kapsama',
    'geo.spinner': 'Önbellekteki coğrafi katmanlar hazırlanıyor…',
    'geo.error': 'Coğrafi çıktı doğrulanamadı ({error}). Orijinal NISAR çalışma alanı kullanılabilir.',
    'geo.m.expansion': 'Aday genişleme',
    'geo.m.recession': 'Aday çekilme',
    'geo.m.valid': 'Gerçek geçerli karşılaştırma alanı',
    'geo.requested': 'İstenen {size} × {size} km; sınır gerçek ortak geçerli pikselleri gösterir. Ölçümler tam çözünürlüklü 10 m EPSG:32615 '
                     'hücrelerini kullanır. Su eşiği −16 dB; |değişim| ≥3 dB; 3×3 doğrusal güç filtresi; tekil piksel bastırma KAPALI.',
    'geo.alt': 'Etkileşimli Louisiana NISAR aday su haritası',
    'geo.howto': 'Yakınlaştırmak için +/− ya da fare tekerleğini, kaydırmak için sürüklemeyi, adayları göstermek/gizlemek için katman '
                 'kutularını kullanın. Katmanlar en yakın komşu ile yeniden örneklenmiş Web Mercator gösterim rasterleridir (kenar başına '
                 '≤768 piksel); veri olmayan alanlar saydam kalır. Küçük özellikler gösterim ölçeğinde kaybolabilir. Alan hesapları her '
                 'zaman özgün çözünürlüğü kullanır.',
    'geo.internet': 'OSM altlığı ve Leaflet kütüphaneleri internet bağlantısı gerektirir; radar katmanları ve ölçümler yalnızca yerel '
                    'önbellek çıktılarını kullanır. Harita doğrulanmış bir taşkın haritası değildir.',
    'geo.provenance': 'Kapsama ve verinin kaynağı',
    'pol.title': 'Vaka çalışması: Louisiana · Polarizasyon analizi',
    'pol.warning': 'Keşif amaçlı HH/HV saçılımı. Taşkın ya da su basmış bitki örtüsü TEYİT EDİLMEMİŞTİR. Bağımsız doğrulama mevcut değil.',
    'pol.caption': 'Gerçek NISAR frekans A HHHH / HVHV · orijinal Louisiana ilgi alanı. Sentinel-1 kıyaslama puanları NISAR doğruluğunu kanıtlamaz.',
    'pol.spinner': 'Yerel HH/HV gözlemleri doğrulanıyor…',
    'pol.error': 'Doğrulanmış polarizasyon çıktıları eksik ya da tutarsız. data/polarization_analysis/ klasörünü geri yükleyin ya da '
                 'scripts/process_polarization.py betiğini yerelde çalıştırın. Hiçbir indirme denenmedi.',
    'pol.sidebar': 'Polarizasyonları karşılaştır',
    'pol.first': 'Seçilen tarih',
    'pol.second': 'Karşılaştırma tarihi',
    'pol.band': 'Radar bandı',
    'pol.sidebar_note': 'Ortak geçerli doğrusal güçte 3×3 ortalama; ardından dB. Yeni sınıflandırıcı ya da sahne düzeltmesi yok.',
    'pol.ratio_label': 'HH/HV güç oranı (dB)',
    'pol.band_label': '{band} gamma-0 (dB)',
    'pol.footprint': 'Tüm tarihlerde ortak HH/HV geçerli ayak izi',
    'pol.legend_range': '{low} → {high} dB (yalnızca gösterim)',
    'pol.legend_dark': 'Karanlık → açık = düşük → yüksek güç',
    'pol.legend_ratio': 'Mor → sarı = düşük → yüksek oran',
    'pol.legend_nodata': 'Saydam = Veri yok · 10 m özgün pikseller',
    'pol.legend_note': 'Keşif amaçlı saçılım; taşkın TEYİT EDİLMEDİ.',
    'pol.m.area': 'Çiftin ortak geçerli alanı',
    'pol.m.dhh': 'Medyan Δ HH',
    'pol.m.dhv': 'Medyan Δ HV',
    'pol.selected': '{n} gerçek HH/HV tarihi · seçilen {first} → karşılaştırma {second}. Δ = karşılaştırma eksi seçilen. Sabit tüm tarihli '
                    'ortak alan {area} km².',
    'pol.identical': 'Aynı tarihler: geçerli HH ve HV değişimleri sıfır; korelasyon tanımsız.',
    'pol.geo_title': 'Bantların coğrafi karşılaştırması',
    'pol.ratio_info': 'Birimsiz doğrusal güç oranı = filtrelenmiş HH gücü / filtrelenmiş HV gücü. dB cinsinden: 10 log10(HH/HV) = HH_dB − '
                      'HV_dB. Bu bir bitki/taşkın olasılığı değildir; zayıf HV oranları kararsızlaştırabilir.',
    'pol.role.selected': 'Seçilen',
    'pol.role.comparison': 'Karşılaştırma',
    'pol.maps_caption': 'HH/HV radar haritaları ortak bir mutlak dB ölçeği kullanır; tüm önce/sonra değişim panelleri simetrik bir ölçeği '
                        'paylaşır. Özgün değerler asla kırpılmaz. Harita gösterimi kenar başına ≤640 piksele en yakın komşu ile yeniden '
                        'örneklenir; OSM/Leaflet internet gerektirir.',
    'pol.change_title': 'HH ve HV: önce, sonra ve değişim',
    'pol.relation': 'HH ve HV değişimi ve zamansal istatistikler',
    'pol.undefined': 'tanımsız (sabit değişim)',
    'pol.pearson': 'Uzamsal Pearson r = {r}; betimleyici bir ilişki, doğruluk DEĞİL. {pixels} uzamsal olarak bağımlı piksel. Medyan ΔHH − ΔHV = {diff} dB.',
    'pol.fig.median': '{band} uzamsal medyan',
    'pol.fig.ylabel': 'Filtrelenmiş gamma-0 (dB)',
    'pol.fig.xlabel': 'Gerçek çekim zamanı (UTC)',
    'pol.stats_caption': 'Uzamsal medyanlar/ÇAA\'lar sabit bir tüm tarihli ortak maske kullanır. Medyanların farkı piksel bazında değişimin '
                         'medyanına eşit olmak zorunda değildir. Düzensiz tarihler arasında ara değer hesaplanmaz; bunlar belirsizlik '
                         'aralıkları değil, uzamsal dağılımlardır.',
    'pol.physics': 'Fiziksel yorum, kaynak katmanlar ve sınırlar',
    'pol.physics_text': '**[[hh]]** yatay polarizasyonla gönderir ve alır. **[[hv]]** yatay gönderir ve dikey alır. Farklı tepkileri saçılım '
                        'yapısını ve depolarizasyonu keşfetmeye yardım edebilir.\n\nDüz açık su iki kanalda da zayıf olabilir; bitki yapısı, '
                        'yüzey pürüzlülüğü, rüzgâr, nem, geometri ve karışık pikseller de dönüşleri değiştirebilir. Bir saçılım farkı bir '
                        'gözlemdir; fiziksel nedeni bir çıkarım olarak kalır. Artan HH ya da HH/HV karşıtlığı tek başına su basmış bitki '
                        'örtüsünü **belirlemez**.\n\nYeni bir su/bitki sınıflandırıcısı, güven puanı, normalizasyon ya da gürültü tabanı '
                        'düzeltmesi uygulanmadı. Zayıf çapraz polarize dönüşler gürültüye duyarlı olabilir (Bilimsel tanılamalardaki '
                        '[[noise_floor|gürültü tabanı]] notlarına bakın). Orijinal HH eşik aracı ve sonuçları değişmedi. Tarihi eşleşen '
                        'bağımsız referans doğrulaması hâlâ mevcut değil.',
    'inv.title': 'Vaka çalışması: Louisiana · İnceleme gezgini',
    'inv.warning': 'Radar değişimi inceleme adayları. Doğrulanmış taşkın, taşkın riski, çevresel hasar ya da kalibre edilmiş güven DEĞİLDİR. '
                   'Bağımsız teyit mevcut değil.',
    'inv.caption': 'Araştırmacıların nerede ve ne zaman inceleme yapacaklarına karar vermesine yardım eder. Altı gerçek NISAR HH/HV gözlemi · '
                   'Louisiana · orijinal işlenmiş ilgi alanı. Sentinel-1 kıyaslama ölçütleri bu adaylara uygulanmaz.',
    'inv.spinner': 'Önbellekteki inceleme bölgeleri doğrulanıyor…',
    'inv.error': 'Doğrulanmış inceleme çıktıları eksik ya da tutarsız. data/investigation_engine/ klasörünü geri yükleyin ya da '
                 'scripts/build_investigations.py betiğini yerelde çalıştırın. Hiçbir indirme ya da orijinal sonuç yeniden hesaplaması denenmedi.',
    'inv.none': 'Belirtilen kuralları karşılayan anlamlı yerel aday bölge yok. Yapay bir bölge ya da zorla ilk beş sonucu konmadı.',
    'inv.select': 'İnceleme bölgesi',
    'inv.region': 'Bölge {id}',
    'inv.select_note': 'Grafiği ve raporu güncellemek için buradan bir bölge seçin. Harita açılır pencereleri konum bağlamı sağlar; numaralar sezgisel sıradır.',
    'inv.m.area': 'Seçilen özgün ızgara alanı',
    'inv.m.notable': 'Dikkat çekici örneklenmiş aralıklar',
    'inv.m.common': 'İşlenmiş ortak alan',
    'inv.point': 'Bölge {id}: temsilî boylam {lon}°, enlem {lat}° · {pixels} ortak geçerli 10 m hücre. Temsilî nokta gerçek çokgenin içindedir.',
    'inv.map.alt': 'Numaralandırılmış Louisiana inceleme bölgeleri',
    'inv.map.footprint': 'Gerçek altı tarihli işlenmiş ayak izi',
    'inv.map.footprint_tip': 'Gerçek ortak işlenmiş alan: {area} km²',
    'inv.map.group': 'İnceleme adayları (sezgisel sıra)',
    'inv.map.label': 'Bölge {id} · {area} km² · 5 aralıktan {count} tanesi dikkat çekici',
    'inv.map.popup': 'Zaman serisini incelemek için bu numarayı bölge listesinde seçin.',
    'inv.map.legend': '<b>Radar değişimi inceleme adayları</b><br>Numaralar = sezgisel sıra, risk/güven DEĞİL.<br>Turuncu = seçilen; turkuaz = '
                      'diğer adaylar.<br>Sınır = gerçek işlenmiş ayak izi.<br>Doğrulanmamış; taşkın ya da hasar teyit edilmedi.',
    'inv.map_caption': 'Seçim için numaralı bölge listesini kullanın. İlk harita adaylara sığar; {area} km²\'lik işlenmiş sınırın tamamını '
                       'görmek için uzaklaştırın. Harita açılır pencereleri/katmanları bağlam sağlar. OSM/Leaflet internet gerektirir; '
                       'bilimsel veriler ve dışa aktarımlar yereldir.',
    'inv.why': 'Bölge {id} neden incelenmeli?',
    'inv.ranges': 'Piksel bazında altı tarihli medyan aralık: HH {hh} dB; HV {hv} dB. Bu aralıklar gözlenen değişkenliği tanımlar, çevresel bir şiddet puanı değildir.',
    'inv.adjacent': 'Dikkat çekici bitişik aralıklar bağımsız tekrarlayan olaylar değildir: tek bir olağandışı tarih hem bir yükselişe hem bir '
                    'düşüşe yol açabilir. Gözlenen süreklilik, çekimler arasındaki koşulların sürekli olduğunu kanıtlamaz.',
    'inv.chart_title': 'Bu sabit coğrafi bölgedeki HH/HV gözlemleri',
    'inv.fig.median': '{band} uzamsal medyan/ÇAA',
    'inv.fig.ylabel': 'Filtrelenmiş gamma-0 (dB)',
    'inv.fig.xlabel': 'Gerçek çekim zamanı (UTC)',
    'inv.chart_caption': 'Altı gözlemin tümü seçilen sabit hücrelerde geçerlidir. Çubuklar güveni değil, uzamsal ÇAA\'yı gösterir. 12/24 '
                         'günlük örnekleme boşlukları arasında ara değer hesaplanmaz; 10 m aralık bağımsız örnekler anlamına gelmez.',
    'inv.stats_table': 'Bu bölge için tarih başına istatistikler',
    'inv.dates': 'Tarihler, tekrarlanma ve gözlenen sapmalar',
    'inv.dates_caption': 'Piksel bazında medyan farklar, bölge medyanlarının farkına eşit olmak zorunda değildir. Sahne medyanları ve '
                         'yüzdelik sınırlar bağlamdır, verilerden çıkarılan kaymalar değildir.',
    'inv.longest': 'Tohum yönünde gözlenen ≥3 dB sapmaların en uzun dizisi: {n} örneklenmiş tarih. Bu sürekli bir olay süresi değildir.',
    'inv.sensitivity': 'Duyarlılık ve bilimsel yorum',
    'inv.retained': 'Belirtilen dokuz filtre/büyüklük ayarı boyunca bu {pixels} hücrenin {low}–{high} tanesi uygun bağlantılı değişim '
                    'bölgelerinde kalıyor. Bunlar güven değil, örtüşme sayılarıdır; bölgeler çarpıcı bir sonuç için yeniden sıralanmaz.',
    'inv.variants': 'Varyantlar: 1/3/5 piksel doğrusal ortalama ve 2,5/3/3,5 dB büyüklük tabanları. Her biri sahne mutlak değişim yüzdeliğini '
                    'yeniden hesaplar ve aynı bağlantılı büyüklük kuralını uygular; korunma, yumuşatmayla tekdüze değişmek zorunda değildir.',
    'inv.next': 'Önerilen sonraki bilimsel adım: ',
    'inv.phase4': 'Orijinal çift için 4. aşama zamansal ölçekli tanılama desteği: {pixels} hücreden {support}. Bu farklı, sabit çiftli bir '
                  'tanılamadır; bağımsız doğrulama ya da sıralama girdisi değildir.',
    'inv.rules': 'Seçim kuralları, kaynak ve sınırlar',
    'inv.rules_text': 'Kalibre edilmiş HV [[noise_floor|gürültü tabanı]] çözümlenmediği için taramayı yalnızca HH yönlendirir. Her tohum, sahne '
                      'mutlak değişiminin %90\'lık yüzdeliğini ve 3 dB tabanını aşmalı ve en az 25 aynı tarih/işaretli dört-bağlantılı '
                      'hücreye sahip olmalıdır. Yüzdelik, ilgi alanına göreli bir kuyruk kuralıdır, istatistiksel anlamlılık değildir. '
                      'Tekdüze sahne kaymalarının yerel bir kuyruğu yoktur ve inceleme çokgenlerine dönüştürülmez.',
    'inv.download': 'Seçilen inceleme raporunu indir (Markdown)',
    'inv.export_caption': 'Dışa aktarım gerçek çekim kimliklerini, koordinatları, istatistikleri, ölçütleri, ayar duyarlılığını, sınırları ve '
                          'önerilen bir inceleme adımını içerir (İngilizce). Orijinal su değişimi ve kıyaslama sonuçları ayrı ve değişmeden kalır.',
    'diag.title': 'Vaka çalışması: Louisiana · Bilimsel tanılamalar',
    'diag.warning': 'Keşif amaçlı güvenilirlik tanılamaları. Bağımsız olarak doğrulanmış taşkın, gürültü olasılıkları ya da kalibre edilmiş '
                    'belirsizlik DEĞİLDİR. Orijinal ölçümler ve sınıflandırıcı değişmedi.',
    'diag.spinner': 'Önbellekteki bilimsel tanılamalar yükleniyor…',
    'diag.error': 'Bilimsel tanılama çıktıları eksik ya da tutarsız. data/scientific_diagnostics/ klasörünü geri yükleyin. Hiçbir indirme ya '
                  'da üretim yeniden hesaplaması denenmedi.',
    'diag.sidebar': 'Güvenilirliği incele',
    'diag.band': 'Tanılama bandı',
    'diag.interval': 'Değişim aralığı',
    'diag.sidebar_note': 'Önbellekteki altı gerçek tarih · NASA erişimi yok · kıyaslama testine göre ayar yok.',
    'diag.m.median': 'Seçilen medyan değişim',
    'diag.m.mad': 'Dayanıklı uzamsal dağılım (1,4826 MAD)',
    'diag.m.area': 'Ortak karşılaştırma alanı',
    'diag.chosen': '{band}: {comparison} eksi {selected} · {count} uzamsal olarak bağımlı piksel. Dağılım algılayıcı hatası ya da güven '
                   'değildir. Sentinel-1 kıyaslama puanları NISAR doğruluğunu kanıtlamaz.',
    'diag.tab.dist': 'Zamansal dağılımlar',
    'diag.tab.methods': 'Temel ve alternatif',
    'diag.tab.sens': 'Eşik duyarlılığı',
    'diag.tab.noise': 'Doku ve kalite',
    'diag.fig.median': '{band} uzamsal medyan/ÇAA',
    'diag.fig.ylabel': 'Filtrelenmiş gamma-0 (dB)',
    'diag.fig.xlabel': 'Gerçek çekim zamanı (UTC)',
    'diag.fig.hist_x': '{band} değişimi (dB) · {comparison} eksi {selected}',
    'diag.fig.hist_y': 'Kutu başına piksel sayısı',
    'diag.tails': '±15 dB dışındaki histogram kuyrukları: altında {below}, üstünde {above}. Kayıtlı dayanıklı istatistikler tüm geçerli '
                  'pikselleri içerir. Medyan normalizasyonu uygulanmadı.',
    'diag.pairwise_table': 'Tüm ikili dağılımlar',
    'diag.col.region': 'Bölge', 'diag.col.hh': 'HH medyan Δ dB', 'diag.col.hv': 'HV medyan Δ dB', 'diag.col.row': 'Özgün satır',
    'diag.col.column': 'Özgün sütun',
    'diag.quiet': 'Sakin görünen aday yamalar',
    'diag.quiet_caption': 'Yukarıda orijinal 21 Haziran/3 Temmuz değişimleri. Üç 210 m\'lik pafta, sonraki dört tarihteki kararlılık ve '
                          'uzamsal dokuya göre, tarihî su yollarından uzakta seçildi. Seçilen bu yamalar doğrulanmış değişmez kalibrasyon '
                          'hedefleri değildir; çevresel etkileri algılayıcı/geometri etkilerinden ayıramazlar.',
    'diag.fixed': '**Sabit orijinal karşılaştırma: 21 Haziran → 3 Temmuz, HH ≤ −16 dB, 3×3 doğrusal güç filtresi.** Aralık/bant seçicileri '
                  'yalnızca dağılım görünümünü etkiler.',
    'diag.col.gate': 'Tanılama kapısı', 'diag.col.expansion': 'Genişleme adayı km²', 'diag.col.recession': 'Çekilme adayı km²',
    'diag.gate.fixed': 'Orijinal |Δ| ≥3 dB',
    'diag.gate.scaled': 'Referansa göre zamansal ölçekli |S| ≥3',
    'diag.fig.expansion': 'Genişleme adayı',
    'diag.fig.recession': 'Çekilme adayı',
    'diag.fig.fixed': 'Sabit 3 dB',
    'diag.fig.scaled': 'Zamansal ölçekli tanılama',
    'diag.fig.km2': 'Aday km²',
    'diag.reference_scale': 'Referans ölçeği yalnızca 15 Temmuz, 27 Temmuz, 20 Ağustos ve 1 Eylül\'ü kullanır; **21 Haziran ve 3 Temmuz '
                            'dışarıda bırakılır**. Payda yalnızca gürültüyü değil, çevresel zamansal değişkenliği de içerir. 1 dB taban ve '
                            'birimsiz 3 sınırı keşif amaçlı düzenleyicilerdir, **gürültü tahmini ya da 3σ anlamlılık değildir**. Sıfır '
                            'referans yayılımı tabanı kullanır; eksik referanslar bilinmeyen kalır.',
    'diag.retrospective': 'Yalnızca geriye dönük tanılama: sonraki referans tarihlerindeki gerçek değişimler MAD\'ı şişirip gerçek geçişleri '
                          'bastırabilir. Dört referans, kalibre edilmiş kararlı bir temel ya da gerçek zamanlı tespit kuralı oluşturamaz.',
    'diag.effective': 'Etkin kapı: medyan {median} dB; %95\'lik uzamsal yüzdelik {p95} dB. Taban ≥3 dB\'lik bir kapıyı garanti ettiğinden, '
                      'yapı gereği daha az aday beklenir ve bu daha iyi doğruluk kanıtlamaz. Orijinal sınıflandırıcının yerine konmadı.',
    'diag.quantity': 'Duyarlılık büyüklüğü',
    'diag.q.expansion_km2': 'genişleme_km2',
    'diag.q.recession_km2': 'çekilme_km2',
    'diag.fig.filter': '{size}×{size} doğrusal ortalama',
    'diag.fig.threshold': 'Keşif amaçlı HH su eşiği (dB)',
    'diag.fig.area': 'Aday alan (km²)',
    'diag.sens_table': 'Tüm duyarlılık ayarları',
    'diag.sens_caption': 'Sabit 3 dB değişim kapısı; hiçbir eşik doğrulama/test etiketlerine göre optimize edilmedi. Her varyasyon ayrı bir '
                         'tanılamadır, üretim sonucu değildir. Tüm alanlar özgün projeksiyonlu 10 m hücreleri kullanır.',
    'diag.stability': '12 senaryonun tümünde: herhangi bir ayarda genişleme {any} km²; her ayarda {all} km². Katı −20 dB yumuşatılmış ayarlar '
                      'sıfır aday verir; bu yüzden tüm aralıkta sıfır kesişim, her adayın yanlış olduğunun kanıtı değildir.',
    'diag.waterways': '{total} temel genişleme pikselinden {near} tanesi tarihî haritalanmış su yollarına yakın. Bu uzamsal bağlamdır, taşkın '
                      'teyidi değil; yakınlık nedeniyle hiçbiri çıkarılmadı.',
    'diag.families': 'Kararlılık aileleri',
    'diag.families_caption': 'Aile içi kesişimler, yalnızca filtre boyutu ya da yalnızca −14/−16/−18 eşikleri altında kararlı desenleri ayırır. '
                             'Bu doğrulama ya da güven oluşturmaz.',
    'diag.metadata': 'Gerçek GCOV kalite üst verisi: yalnızca orijinal çift',
    'diag.col.date': 'Tarih', 'diag.col.looks_med': 'Bakış sayısı medyanı', 'diag.col.looks_min': 'Bakış sayısı en az',
    'diag.col.looks_max': 'Bakış sayısı en çok', 'diag.col.codes': 'Maske kodları',
    'diag.looks_caption': 'numberOfLooks, uyarlamalı ortalama topluluğunu sayar; ölçülmüş bir ENL ya da bağımsız örnek sayısı değildir. '
                          'İncelenen iki ilgi alanı maskesi de kod 1\'dir (geçerli alt şerit); kod 0 kısmen odaklanmış/geçersiz topluluk, 255 '
                          'ise kapsam dışı anlamına gelir. Mevcut sonlu-pozitif maskeler değiştirilmedi.',
    'diag.texture_table': 'Yerel doku istatistikleri',
    'diag.texture': '**Doku saf gürültü değildir.** Ham yerel değişim katsayısı, uzamsal eğilimler ve komşu piksel korelasyonu '
                    '[[speckle|benek gürültüsünü]] ve gerçek yapıyı karıştırır. Koşullu ENL yalnızca belirtilen durağanlık, korelasyon ve '
                    'bakış tekdüzeliği kontrollerini geçen ham yamalar için raporlanır; geçici bir uzamsal moment tahminidir, ısıl gürültü '
                    'kalibrasyonu değildir. Filtrelenmiş pikseller ENL için asla kullanılmaz.',
    'diag.hv_floor': '**HV [[noise_floor|gürültü tabanı]] hâlâ çözümlenmedi.** Gürültü eşdeğeri HH/HV üst verileri kaba bir ızgarada mevcut '
                     'ama **DN²** olarak tanımlanıyor; bilim dizilerimiz ise kalibre edilmiş gamma-0. Doğrulanmış bir kalibrasyon dönüşümü '
                     'olmadan doğrudan bölme, gürültü tabanı değeri ya da SNR raporlanmaz. İncelenen iki ürün de '
                     '`noiseCorrectionApplied=False` bildiriyor; bu, her pikselde bilinen toplamsal bir hatanın kanıtı değildir.',
    'diag.limits': '**Sınırlar:** altı tarih bir iklim ortalaması oluşturmaz; sahne geneli ve yerel değişkenlik nem, bitki örtüsü, rüzgâr, '
                   'gelgit/drenaj, hizalama, geometri, benek gürültüsü ya da işlemeyi yansıtabilir. Hiçbir kaynak tek başına belirlenmez. Ne '
                   'sabit kapı ne de alternatif bağımsız olarak doğrulanmıştır; olasılık, doğruluk ya da güven yüzdesi üretilmez.',
    'diag.flags': 'İşleme bayrakları',
}
