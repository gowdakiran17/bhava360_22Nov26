"""Integration checks on the JSON an engine reads. Run after build.py."""
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from build import HERE, SYSTEMS, Messages, snapshot, schema_name, token


class EngineExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = HERE.parent/'dist-json'
        cls.files = {p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*.json')}
        cls.docs = {p:json.loads(data) for p,data in cls.files.items()}
        cls.manifest = cls.docs['manifest.json']
        cls.source = snapshot(cls.manifest['commit'])
        cls.rules = {d['id']:d for d in cls.source.values() if isinstance(d,dict) and 'system' in d and 'rule' in d}
        cls.rows = {key:r for s in SYSTEMS for key,r in cls.docs[f'admin/{s}.json']['rules'].items()}
        cls.routes = cls.docs['admin/routing.json']['routes']
        aliases = cls.source['governance/review/rule-aliases.yaml']
        cls.aliases = aliases['evidence_aliases']
        cls.copies = aliases['copy_aliases']

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
        blocked = {'rule','rules','aliases','copy_owner','fact','conditions','points','score','sources','approval',
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
                self.assertEqual(set(pub),{'user_text','tone','remedy'})
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
