"""Resolve explicit, consented palm choices to reflections. No image input."""
def guided_reading(read, rules, *, consent, observations, dominant='unknown', locale='en'):
    catalog = read('palmistry/guided-observations/choices.yaml')['choices']
    intake = read('palmistry/guided-observations/questions.yaml')
    wording = read('shared/localization/reading.yaml')
    public, audit = [], []
    result = {'admin': audit, 'public': public}
    if consent is not True:
        return result
    if dominant not in intake['dominance']:
        raise ValueError('Invalid dominance selection')
    def localized(field):
        return field.get(locale, field['en'])
    labels = {r['en']:localized(r) for r in wording['tones']}
    answers = {}
    for choice in observations:
        if set(choice)!={'hand','feature','answer'}:
            raise ValueError('Only illustrated choice input is accepted')
        hand,feature,answer = (choice[k] for k in ('hand','feature','answer'))
        if hand not in ('left','right') or feature not in catalog or answer not in intake['answers']:
            raise ValueError('Invalid illustrated choice')
        answers[hand,feature] = answer
    confirmed = {key for key, answer in answers.items() if answer == 'confirmed'}
    for hand in ('left', 'right'):
        for exclusive in ({'hands-earth', 'hands-air', 'hands-fire', 'hands-water'},
                          {'fingers-long', 'fingers-short'}, {'fingers-thumb-long', 'fingers-thumb-short'}):
            if sum((hand, feature) in confirmed for feature in exclusive) > 1:
                raise ValueError('Choose one proportion or shape for this hand')
        for general, detailed in {'lines-life': ('lines-life-short', 'lines-life-broken'),
                                  'mounts-mars': ('mounts-mars-upper', 'mounts-mars-lower')}.items():
            if any((hand, feature) in confirmed for feature in detailed):
                confirmed.discard((hand, general))
    for hand, feature in answers:
        if (hand, feature) not in confirmed:
            continue
        rule = rules[catalog[feature]['rules'][hand]]
        role = dominant if dominant in ('unknown','mixed') else ('dominant' if hand==dominant else 'non-dominant')
        audit.append(dict(hand=hand,dominance=dominant,role=role,feature=feature,rule_id=rule['id'],
                          reason=rule['guided']['reason']))
        public.append(dict(localized_tone=labels[rule['guided']['tone']],user_text=localized(rule['user_text']),
                           reflection_footer=localized(wording['reflection'])))
    return result
