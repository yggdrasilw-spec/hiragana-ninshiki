"""Content appropriateness is independent of difficulty and historical register."""
REJECT_MISC={'vulg','derog','sens','X'}
CONTEXT_MISC={'arch','obs','dated','rare','sl'}

def context_notes(sense, form_tags=(), reading_tags=()):
    misc=set(sense.get('misc',[]));notes=[]
    if misc & {'arch','obs','dated'}:notes.append('古い時代や用法の言葉。')
    if sense.get('dialect'):notes.append('方言として使う言葉。')
    if 'sl' in misc:notes.append('くだけた場面で使う言葉。')
    if 'oK' in form_tags:notes.append('古い漢字表記。')
    if 'ok' in reading_tags:notes.append('古い仮名遣い。')
    if 'gikun' in reading_tags:notes.append('特殊な読み方。')
    return ''.join(notes)
