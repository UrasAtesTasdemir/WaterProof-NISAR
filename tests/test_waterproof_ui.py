"""Brand, section removal and navigation-only globe regression checks."""
from pathlib import Path
import unittest
from unittest.mock import patch
from src.navigation import APP_NAME,apptest_open
from src.theme import contrast,css
from src.i18n import t

ROOT=Path(__file__).resolve().parents[1]

class WaterProofTests(unittest.TestCase):
    def test_brand_and_light_blue_contrast(self):
        self.assertEqual(APP_NAME,'WaterProof')
        self.assertGreaterEqual(contrast('#67C8F5','#12334a'),4.5)
        for mode in ('light','dark'):
            self.assertIn('.wp-brand',css(mode));self.assertIn('#67C8F5',css(mode))
        self.assertIn('WaterProof',t('wf.note.disclaimer',lang='en'))
        self.assertIn('WaterProof',t('bm.caption',lang='en'))

    def test_about_has_no_standalone_limits_and_language_theme_survive(self):
        from streamlit.testing.v1 import AppTest
        with patch('requests.sessions.Session.request',side_effect=AssertionError('No network')):
            app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run()
            self.assertFalse(app.exception)
            apptest_open(app,'About')
            self.assertEqual(app.title[0].value,'About WaterProof')
            for mode,lang in (('light','en'),('dark','en'),('dark','tr'),('light','tr')):
                if app.session_state['lang']!=lang:app.button(key='lang_'+lang).click().run()
                if app.session_state['theme']!=mode:app.button(key='theme_toggle').click().run()
                self.assertFalse(app.exception)
                text=' '.join(m.value for m in app.markdown)
                self.assertNotIn('#### Limits',text);self.assertNotIn('#### Sınırlar',text)
                self.assertNotIn('NISAR Change Compass',text)
                self.assertIn('WaterProof',text)

    def test_reports_use_new_brand_but_real_measurements_retained(self):
        from src.investigation import load_investigations,markdown_report
        data=load_investigations();region=data['regions'][0]
        note=markdown_report(region,data)
        self.assertTrue(note.startswith('# WaterProof — Investigation region'))
        self.assertIn(region['temporal_statistics'][0]['product_id'],note)
        self.assertIn('NOT confirmed flooding',note)
        self.assertIn(f"{region['area_km2']:.4f}",note)

    def test_globe_is_local_and_labels_are_plain_text(self):
        html=(ROOT/'assets/earth_globe/index.html').read_text()
        self.assertIn('./earth.jpg',html);self.assertIn("from './OrbitControls.js'",html)
        self.assertIn('tip.textContent=p.name||',html)
        self.assertNotIn('{name}',html)
        self.assertIn('Math.atan2(-p.z,p.x)',html)
        self.assertIn('Math.asin(p.y)',html)
        self.assertIn('e.clientX-down.x',html) # drag is not a selection
        self.assertIn('streamlit:setComponentValue',html)
        self.assertTrue((ROOT/'assets/earth_globe/earth.jpg').read_bytes().startswith(b'\xff\xd8'))
