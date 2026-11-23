"""Editorial gate for text reachable from a consumer projection."""
import hashlib
import json
import re
import unicodedata

LOCALES = ('en', 'kn', 'hi', 'te', 'ta', 'ml', 'es', 'fr')
TAROT_FIELD = 'glossary/entries/death-tarot.yaml/term'
TAROT_MESSAGE = 'm_' + hashlib.sha256(TAROT_FIELD.encode()).hexdigest()[:24]
EN_FALLBACK = {'en', 'te', 'ta', 'ml', 'es', 'fr'}
ORDINAL = r'first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth'
NUMBER = r'\d+(?:st|nd|rd|th)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|' + ORDINAL
HOUSE = r'houses?|bhavas?'
POLICIES = {
    'sensitive term': r'\b(?:m[aā]raka|deaths?|shrapit|guru[- ]?chand[aā]l|chand[aā]l[ae]?|pitru[- ]?dosha|grahan)\b'
                      r'|मारक|मृत्यु|चांडाल|चाण्डाल|श्रापित|पितृदोष|मौत|मरण|ಮಾರಕ|ಮೃತ್ಯು|ಮರಣ|ಸಾವು|ಚಾಂಡಾಲ|ಶ್ರಾಪಿತ|ಪಿತೃದೋಷ',
    'fear or judgment': r'\b(?:weak(?:ly|er|est|ness)?|curs(?:e[ds]?|ing)|doom(?:ed)?|danger(?:ous)?|bad[- ]luck)\b'
                        r'|कमज़ोर|कमजोर|अभिशाप|दुर्भाग्य|खतर|बदकिस्मती|श्राप|शापित|ದುರ್ಬಲ|ದುರದೃಷ್ಟ|ಶಾಪ|ಕೆಟ್ಟ ಅದೃಷ್ಟ|ಅಪಾಯ'
                        r'|\b(?:maldici[oó]n|d[eé]bil|peligro|mala suerte|malédiction|maudit[e]?|mort|muerte|faible|malchance|fatalidad|perdición|perdition)\b'
                        r'|சாபம்|ஆபத்து|மரணம்|பலவீன|துரதிர்ஷ்ட|శాపం|ప్రమాదం|మరణం|బలహీన|దురదృష్ట|ശാപം|അപകടം|മരണം|ദുർബല|ദൗർഭാഗ്യ',
    'numbered house': rf'\b(?:{HOUSE})\s*[-:#]?\s*(?:{NUMBER})\b|\b(?:\d+(?:st|nd|rd|th)|{ORDINAL})\s*[- ](?:{HOUSE})\b'
                      r'|(?:भाव|भव|ಭಾವ|భావం|பாவம்|ഭാവം|casa|maison)\s*[-:#]?\s*\d+'
                      r'|\d+\s*(?:ನೇ|ನೆಯ|वें|वाँ|वां|वा|ஆம்|వ|ാം)?\s*(?:ಭಾವ|भाव|பாவம்|భావం|ഭാവം)'
                      r'|(?:ಮೊದಲ|ಎರಡನೇ|ಮೂರನೇ|ನಾಲ್ಕನೇ|ಐದನೇ|ಆರನೇ|ಏಳನೇ|ಎಂಟನೇ|ಒಂಬತ್ತನೇ|ಹತ್ತನೇ|ಹನ್ನೊಂದನೇ|ಹನ್ನೆರಡನೇ)\s*ಭಾವ'
                      r'|(?:पहल[ाे]|दूसर[ाे]|तीसर[ाे]|चौथ[ाे]|पाँचव[ाेें]+|छठ[ाे]|सातव[ाेें]+|आठव[ाेें]+|नौव[ाेें]+|दसव[ाेें]+|ग्यारहव[ाेें]+|बारहव[ाेें]+)\s*भाव'
                      r'|\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)(?:,\s*|\s+(?:and|or)\s+)(?:\w+[, ]+){0,6}(?:houses?|places?)\b',
    'public score': r'[%٪]|\d+(?:\.\d+)?\s*(?:out of|of|/|sur|de)\s*36\b|३६\s*में से|36\s*में से'
                    r'|\b(?:point[- ]total|total points|bindu count)s?\b|\d+\s*(?:traditional\s+)?(?:points?|bindus?|percent|अंक|बिंदु|ಅಂಕ|ಬಿಂದು)'
                    r'|\d+\s*(?:por ciento|pour cent|प्रतिशत|ಶೇಕಡಾ|प्रतिशत|ಶತಾಂಶ|புள்ளிகள்|పాయింట్లు|പോയിന്റ്|puntos?|pontos?)'
                    r'|(?:36|३६|೩೬)\s*(?:ರಲ್ಲಿ|में से)|\d+\s*(?:गुण|ಗುಣ)\s*(?:मिले|अंक|ಅಂಕ)'
                    r'|(?:score|points?|bindus?|अंक|ಅಂಕ)\s*[:=]\s*\d+',
}
PATTERNS = {name: re.compile(pattern, re.I) for name, pattern in POLICIES.items()}


def check_text(text, field, locale):
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f'{field}.{locale}: missing public copy')
    if field in (TAROT_FIELD, TAROT_MESSAGE) and locale in EN_FALLBACK and text == 'Transformation (Death card)':
        return
    normalized = unicodedata.normalize('NFKC', text)
    for name, pattern in PATTERNS.items():
        match = pattern.search(normalized)
        if match:
            raise ValueError(f'{field}.{locale}: {name}: {match[0]}')


def check_public_file(path, data):
    if path.startswith('public/locales/'):
        for key, value in data['messages'].items():
            check_text(value, key, data['locale'])
        return
    def visit(value, field):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, f'{field}/{key}')
        elif isinstance(value, list):
            for child in value:
                visit(child, field)
        elif isinstance(value, str):
            check_text(value, field, 'public')
    visit(data, path)


def check_distribution(root):
    for locale in LOCALES:
        if not (root / 'dist-json/public/locales' / f'{locale}.json').is_file():
            raise ValueError(f'Missing public bundle for {locale}')
    for path in sorted((root / 'dist-json/public').rglob('*.json')):
        check_public_file(path.relative_to(root / 'dist-json').as_posix(), json.loads(path.read_text()))
