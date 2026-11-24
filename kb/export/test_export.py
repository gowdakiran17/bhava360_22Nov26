"""Integration checks on the JSON an engine reads. Run after build.py."""
import hashlib
from tempfile import TemporaryDirectory
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from build import HERE, SYSTEMS, Messages, snapshot, schema_name, token, source_revision, encoded, publish


class EngineExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = HERE.parent/'dist-json'
        cls.files = {p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*.json')}
        cls.docs = {p:json.loads(data) for p,data in cls.files.items()}
        cls.manifest = cls.docs['manifest.json']
        cls.source = snapshot(source_revision('HEAD'))
        cls.rules = {d['id']:d for d in cls.source.values() if isinstance(d,dict) and 'system' in d and 'rule' in d}
        cls.rows = {key:r for s in SYSTEMS for key,r in cls.docs[f'admin/{s}.json']['rules'].items()}
        cls.routes = cls.docs['admin/routing.json']['routes']
        aliases = cls.source['governance/review/rule-aliases.yaml']
        cls.aliases = aliases['evidence_aliases']
        cls.copies = aliases['copy_aliases']

    def test_confidence_copy_is_the_only_public_confidence_resource(self):
        path = 'shared/confidence/copy.yaml'
        admin = self.docs['admin/catalog.json']
        bindings = {k:v for k,v in admin['public_keys'].items() if k.startswith('shared/confidence/')}
        messages = self.source[path]['messages']
        self.assertEqual(set(bindings), {f'{path}#messages/{key}' for key in messages})
        for key, translations in messages.items():
            entry = self.docs['public/catalog.json']['entries'][bindings[f'{path}#messages/{key}']]
            self.assertEqual(set(entry), {'user_text'})
            for loc in self.manifest['locales']['required'] + self.manifest['locales']['planned']:
                text = self.docs[f'public/locales/{loc}.json']['messages'][entry['user_text']]
                self.assertEqual(text, translations.get(loc, translations['en']))
                self.assertNotRegex(text, r'\d')

    def test_squash_check_allows_only_the_provenance_pair(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp)
            original = 'a'*40
            expected = {'manifest.json':encoded(self.manifest), 'public.json':b'{}'}
            manifest = dict(self.manifest, commit=original, version='1.'+original[:12])
            def write_manifest(value):
                (dest/'manifest.json').write_bytes(encoded(value))
            write_manifest(manifest)
            payload = dest/'public.json'
            payload.write_bytes(expected['public.json'])
            publish(expected,dest,True)
            for mutation in ({'conventions':{}}, {'files':{}}, {'version':'stale'}, {'commit':'xyz'}):
                write_manifest(dict(manifest, **mutation))
                with self.assertRaises(ValueError):
                    publish(expected,dest,True)
            write_manifest(manifest)
            payload.write_bytes(b'{ }')
            with self.assertRaises(ValueError):
                publish(expected,dest,True)
            payload.unlink()
            with self.assertRaises(ValueError):
                publish(expected,dest,True)
            payload.write_bytes(expected['public.json'])
            (dest/'stale.json').write_bytes(b'{}')
            with self.assertRaises(ValueError):
                publish(expected,dest,True)

    def test_strength_words_have_only_localized_labels(self):
        path = 'vedic/strength/user-words.yaml'
        for band, row in self.source[path]['labels'].items():
            name = f'{path}#labels/{band}'
            public = self.docs['public/catalog.json']['entries'][token('p',name)]
            self.assertEqual(set(public), {'label'})
            self.assertIn(row['tone'], ['Supportive','Steady','Take care'])
            for locale in ('en','kn','hi'):
                word = self.docs[f'public/locales/{locale}.json']['messages'][public['label']]
                self.assertEqual(word,row[locale])
                self.assertNotRegex(word, r'\d|%|weak|rank')
    def test_new_reflections_only_expose_public_copy(self):
        ids = [key for key in self.rules if 'karmic-debt-' in key or key.endswith('ruler-compatibility')]
        self.assertEqual(len(ids),7)
        for key in ids:
            rendered=self.docs['public/numerology.json']['readings'][self.rows[key]['public_key']]
            self.assertEqual(set(rendered),{'user_text','tone','remedy'})
            for locale in ('en','kn','hi'):
                text=self.docs[f'public/locales/{locale}.json']['messages'][rendered['user_text']]
                self.assertNotRegex(text,r'\d|%|must pay|house [0-9]')
    def test_public_copy_gate(self):
        from public_copy import LOCALES, TAROT_FIELD, check_text, check_public_file
        for loc in LOCALES:
            with self.subTest(locale=loc), self.assertRaisesRegex(ValueError, 'weak'):
                check_public_file(f'public/locales/{loc}.json',
                                  {'locale': loc, 'messages': {'planted': 'weakly placed'}})
        for phrase in ('curse', 'doomed', 'danger', 'bad luck', '31 of 36', '31 points',
                       '७०%', 'Raman: 28 bindus', 'ninth house', 'भाव ९', '೯ನೇ ಭಾವ',
                       'மரணம்', 'దురదృష్టం', 'അപകടം', 'mala suerte', 'malédiction',
                       'not compatible', 'lucky', 'gemstone', 'crystal', 'sapphire', 'रत्न', 'ರತ್ನ', 'paid puja',
                       'lifespan', 'longevity', 'die', 'widow', 'आयु', 'ಆಯುಷ್ಯ', 'मृत', 'risk', 'जोखिम',
                       'ಅಪಾಯ', 'immediately', 'disaster', 'terrible', 'seventh lord', 'lord of the 7th',
                       'सातवाँ घर', 'ಏಳನೇ ಮನೆ', '8 out of 10', 'Death', 'Transformation (Death card)', '', None):
            with self.subTest(phrase=phrase), self.assertRaises(ValueError):
                check_text(phrase, 'probe', 'en')
        for phrase in ('household', 'compare the two house placements', '36 days', 'स्मरण', 'ಸ್ಮರಣೆ'):
            check_text(phrase, 'probe', 'en')
        check_text('Transformation (Death card)', TAROT_FIELD, 'en')
        with self.assertRaises(ValueError):
            check_text('Death', TAROT_FIELD, 'en')

    def test_glossary_visibility_and_fallback(self):
        prefix = 'glossary/entries/'
        bindings = self.docs['admin/catalog.json']['public_keys']
        hidden = prefix + 'maraka.yaml'
        self.assertIn(hidden, self.docs['admin/catalog.json']['resources'])
        self.assertNotIn(hidden, bindings)
        catalog = self.docs['public/catalog.json']['entries']
        self.assertNotIn(token('p', hidden), catalog)
        for loc in self.manifest['locales']['required'] + self.manifest['locales']['planned']:
            messages = self.docs[f'public/locales/{loc}.json']['messages']
            for field in ('term', 'meaning'):
                self.assertNotIn(token('m', hidden + '/' + field), messages)
            for slug in ('death-tarot', 'shrapit', 'guru-chandal', 'pitru-dosha', 'grahan'):
                path = prefix + slug + '.yaml'
                labels = self.source[path]['public_label']
                self.assertEqual(messages[catalog[bindings[path]]['term']], labels.get(loc, labels['en']))

    def test_personal_calendar_projection(self):
        admin=self.docs['admin/catalog.json']
        for hidden in ('ayu','mrita-age-state'):
            path=f'glossary/entries/{hidden}.yaml'
            self.assertIn(path,admin['resources'])
            self.assertNotIn(path,admin['public_keys'])
            for field in ('term','meaning'):
                for locale in self.manifest['locales']['required']+self.manifest['locales']['planned']:
                    self.assertNotIn(token('m',path+'/'+field),self.docs[f'public/locales/{locale}.json']['messages'])
        for path in ('life-areas/conflict-ladder.yaml','life-areas/pipeline.yaml',
                     'modules/home/day.yaml','modules/home/week.yaml','modules/home/month.yaml'):
            self.assertIn(path,admin['resources'])
            self.assertNotIn(path,admin['public_keys'])
        path='modules/home/copy.yaml'
        for key,words in self.source[path]['messages'].items():
            entry=self.docs['public/catalog.json']['entries'][admin['public_keys'][f'{path}#messages/{key}']]
            self.assertEqual(set(entry),{'user_text'})
            for locale in self.manifest['locales']['required']+self.manifest['locales']['planned']:
                self.assertEqual(self.docs[f'public/locales/{locale}.json']['messages'][entry['user_text']],
                                 words.get(locale,words['en']))

    def test_practice_labels(self):
        key = token('m', 'shared/traditional-practices/options.yaml#label')
        def inspect(value):
            if isinstance(value, dict):
                if 'optional' in value:
                    self.assertEqual((value['optional'], value['cost'], value['label']), (True, 'free', key))
                for child in value.values():
                    inspect(child)
        for path, doc in self.docs.items():
            if path.startswith('public/'):
                inspect(doc)

    def test_synthesis_metadata_stays_internal(self):
        internal = self.docs['admin/vedic.json']['resources']
        self.assertEqual(internal['vedic/strength/grade.yaml']['bands'], {'Strong':3,'Moderate':1})
        self.assertIn('cells', internal['vedic/lordships/functional.yaml'])
        for key,row in self.rows.items():
            self.assertEqual(row['rule']['evidence'], self.rules[key]['evidence'], key)
        for path in ('vedic/strength/grade.yaml','vedic/lordships/functional.yaml',
                     'shared/explain/tone-contribution.yaml'):
            self.assertNotIn(token('p',path), self.docs['public/catalog.json']['entries'])

    def test_manifest_integrity_and_schemas(self):
        inventory = self.manifest['files']
        self.assertEqual(set(self.files),set(inventory)|{'manifest.json'})
        for name,doc in self.docs.items():
            schema = HERE/'schema'/(schema_name(name)+'.json')
            if name in inventory:
                record = inventory[name]
                self.assertEqual(schema,HERE/record['schema'])
                self.assertEqual(len(self.files[name]),record['bytes'])
                self.assertEqual(hashlib.sha256(self.files[name]).hexdigest(),record['sha256'])
            Draft202012Validator(json.loads(schema.read_text())).validate(doc)

    def test_aliases_preserve_source_coverage_and_evaluation(self):
        pairs = [(alias,key) for key,row in self.rows.items() for alias in row['aliases']]
        self.assertEqual(len(pairs),len(self.aliases))
        self.assertEqual(dict(pairs),self.aliases)
        self.assertEqual(set(self.rows),self.rules.keys()-self.aliases.keys())
        for key,row in self.rows.items():
            self.assertEqual(row['rule']['conditions'],self.rules[key]['conditions'])
            self.assertEqual(row['copy_owner'],self.copies.get(key,key))
        self.assertEqual(self.manifest['counts']['canonical_rules'],len(self.rows))
        self.assertEqual(self.manifest['counts']['source_rules'],len(self.rules))

    def test_every_rule_and_route(self):
        for name,keys in self.routes.items():
            self.assertEqual(keys,sorted(set(keys)),name)
            self.assertTrue(set(keys)<=self.rows.keys(),name)
        routes = [set(keys) for name,keys in self.routes.items()
                  if name not in ('screen/reports','screen/admin-tester','screen/home','screen/life-areas','screen/ask')]
        self.assertEqual(set.union(*routes),set(self.rows))
        for key,rule in self.rules.items():
            canonical = self.aliases.get(key,key)
            if rule['system'] in ('vedic','jaimini','western','kp','numerology','lal-kitab'):
                for area in rule['life_areas']:
                    self.assertIn(canonical,self.routes['area/'+area])
        for name in self.source['life-areas/catalog.yaml']['areas']:
            self.assertTrue(self.routes['area/'+name])
        for tool in self.source['life-areas/catalog.yaml']['checker_ids']:
            reasons = self.source[f'checkers/{tool}/recipe.yaml']['explain_rules']
            for reason in reasons:
                key = reason['rule_id']
                self.assertIn(self.aliases.get(key,key),self.routes['tool/'+tool])
        for screen in ('today','matching','palmistry','tarot','vastu'):
            self.assertTrue(self.routes['screen/'+screen])
        for system in ('tarot','palmistry','vastu'):
            expected = {k for k,r in self.rows.items() if r['rule']['system']==system}
            self.assertEqual(expected,set(self.routes['screen/'+system]))

    def test_public_boundary_and_locales(self):
        blocked = {'tier','rectified','withheld','assessment_radius_seconds','evidence','direction','weight_class','time_scope','area_strength','maraka','polarity','grade','total','terms','lord_total','rule','rules','aliases','copy_owner','fact','conditions','points','score','sources','approval',
                   'native_review','strength_notes','exceptions','traditions_differ','confidence','admin','reason'}
        def inspect(obj):
            if isinstance(obj,dict):
                self.assertFalse(blocked.intersection(obj))
                for child in obj.values():
                    inspect(child)
            elif isinstance(obj,list):
                for child in obj:
                    inspect(child)
        for name,doc in self.docs.items():
            if name.startswith('public/'):
                inspect(doc)
        settings = self.manifest['locales']
        for loc in settings['required']+settings['planned']:
            bundle = self.docs[f'public/locales/{loc}.json']['messages']
            for key,row in self.rows.items():
                src = self.rules[key]
                pub = self.docs['public/'+src['system']+'.json']['readings'][row['public_key']]
                self.assertEqual(set(pub), {'user_text','tone','remedy'} | ({'label'} if 'public_label' in src else set()))
                self.assertEqual(bundle[pub['user_text']],src['user_text'].get(loc) or src['user_text']['en'])
                if src['remedy']:
                    text = src['remedy']['user_text']
                    self.assertEqual(bundle[pub['remedy']['user_text']],text.get(loc) or text['en'])
        msgs = Messages(settings)
        primary = msgs.add('test/partial',{'en':'one','kn':'ಒಂದು','hi':'एक','es':'uno'})
        secondary = msgs.add('test/secondary',{'en':'two','kn':'ಎರಡು','hi':'दो'})
        self.assertEqual(msgs.bundles['es'][primary],'uno')
        self.assertEqual(msgs.bundles['es'][secondary],'two')
        self.assertEqual(msgs.bundles['ta'][primary],'one')

    def test_schema_rejects_public_evidence(self):
        schema = json.loads((HERE/'schema/public-system.json').read_text())
        sample = {'system':'vedic','readings':{token('p','probe'):{
            'user_text':token('m','probe'),'tone':'Steady','remedy':None,'sources':[]}}}
        self.assertFalse(Draft202012Validator(schema).is_valid(sample))


if __name__=='__main__':
    unittest.main()
