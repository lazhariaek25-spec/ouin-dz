"""كلمات مفتاحية متعددة اللغات (فصحى، دارجة، فرنسية، إنجليزية) تربط البحث بالقطاعات والتخصصات."""
import re
import unicodedata

_DIAC = re.compile("[\u064B-\u065F\u0670\u0640]")


def norm(s):
    """توحيد النص: حروف صغيرة، بلا تشكيل ولا لهجات الألف، بلا لكنات فرنسية ولا علامات ترقيم."""
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = _DIAC.sub("", s)
    s = re.sub("[أإآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    s = re.sub(r"[^\w]|_", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_ar(t):
    for p in ("وال", "بال", "كال", "فال", "لل", "ال"):
        if t.startswith(p) and len(t) - len(p) >= 3:
            return t[len(p):]
    return t


STOP = set(norm(w) for w in """
في من على عن الى إلى ابحث اريد أريد اين أين فين وين قريب قريبة قريبين بالقرب حول عند لي ليا
dans de du des la le les un une pour pres près autour moi chez ou où trouver chercher cherche je
near me in the a an for find looking nearby around at to""".split())

# (القطاع، أنواع OSM، الكلمات)
RULES = [
 # ----- الصحة -----
 ("health", ("pharmacy",), "صيدلية صيدليات صيدلي صيدلاني صيدلانية فارمسي فرماسي دواء ادوية pharmacie pharmacien pharmacy pharmacist chemist drugstore médicament medicament"),
 ("health", ("dentist",), "طبيب اسنان طبيبة اسنان جراح اسنان اسنان dentiste dentistes dentist dentists dental dentaire"),
 ("health", ("doctors",), "طبيب اطباء طبيبة دكتور دكتورة دوكتور مختص طبيب عام médecin medecin docteur doctor physician généraliste generaliste spécialiste specialiste gp"),
 ("health", ("hospital",), "مستشفى مستشفيات سبيطار سبيطر اسعاف إسعاف طوارئ مستعجلات urgences urgence hôpital hopital hospital chu emergency"),
 ("health", ("clinic",), "عيادة عيادات مصحة مصحات مركز صحي قاعة علاج clinique cliniques polyclinique clinic"),
 ("health", ("laboratory",), "مخبر مخابر تحاليل تحليل laboratoire labo laboratory analyses analyse"),
 ("health", (), "صحة صحي طبي علاج santé sante médical medical health healthcare"),
 # ----- التجارة والتسوق -----
 ("shopping", ("bakery",), "مخبزة مخبز مخابز فران خباز خبز boulangerie boulangeries bakery bread pain"),
 ("shopping", ("supermarket",), "سوبر ماركت سوبرماركت ماركت hypermarché supermarché supermarche supermarket hypermarket"),
 ("shopping", ("convenience",), "بقالة بقال حانوت épicerie epicerie grocery convenience"),
 ("shopping", ("clothes",), "ملابس لباس ثياب كسوة vêtements vetements habits boutique clothes clothing fashion"),
 ("shopping", ("mobile_phone",), "هاتف هواتف موبايل جوال téléphone telephone portable phone mobile smartphone"),
 ("shopping", ("electronics",), "الكترونيات الكترونيك كهرومنزلي electronique electronics électroménager electromenager"),
 ("shopping", ("butcher",), "جزار جزارة لحوم لحام لحوم بوشري boucherie boucher butcher meat"),
 ("shopping", ("hardware",), "مواد بناء بريكولاج ادوات quincaillerie hardware bricolage"),
 ("shopping", ("marketplace",), "سوق اسواق marché marche market"),
 ("shopping", (), "تسوق تجارة محل محلات تجاري commerce shopping shop shops store magasin magasins"),
 # ----- النقل والسيارات -----
 ("auto", ("fuel",), "وقود بنزين محطة وقود محطة بنزين ستاسيون station service carburant essence gasoil fuel gas station petrol naftal"),
 ("auto", ("car_repair",), "ميكانيكي ميكانيسيان مكانيكي ميكانيك ورشة سيارات غاراج كراج mécanicien mecanicien mecanique garage atelier mechanic repair"),
 ("auto", ("car_parts",), "قطع غيار pièces pieces détachées detachees parts spare"),
 ("auto", (), "سيارات سيارة نقل مركبات auto voiture voitures transport car cars vehicle automobile"),
 # ----- المطاعم والترفيه -----
 ("food", ("fast_food",), "وجبات سريعة سندويتش ساندويتش بيتزا شاورما برغر fast food snack pizza pizzeria burger tacos sandwich"),
 ("food", ("restaurant",), "مطعم مطاعم ريستو مشويات شواء restaurant restaurants resto grill"),
 ("food", ("cafe",), "مقهى مقاهي قهوة كافي كافيتيريا café cafe coffee cafeteria salon de thé"),
 ("food", (), "اكل اكلات طعام مأكولات ترفيه nourriture manger food dining"),
 # ----- الحرف والخدمات -----
 ("trades", ("electrician",), "كهربائي كهرباء électricien electricien electricite electrician"),
 ("trades", ("plumber",), "سباك سباكة plombier plomberie plumber plumbing"),
 ("trades", ("carpenter",), "نجار نجارة menuisier menuiserie carpenter"),
 ("trades", ("painter",), "دهان صباغ صباغة peintre peinture painter"),
 ("trades", ("welder",), "لحام soudeur soudure welder"),
 ("trades", ("tiler",), "بلاط تبليط carreleur carrelage tiler"),
 ("trades", ("locksmith",), "حداد اقفال serrurier serrurerie locksmith"),
 ("trades", ("tailor",), "خياط خياطة couturier tailleur tailor"),
 ("trades", ("builder",), "بناء مقاول معماري maçon macon entrepreneur builder contractor"),
 ("trades", (), "حرفي حرفيين حرف صيانة خدمات منزلية artisan artisans bricoleur dépannage depannage handyman"),
 # ----- الإدارات والمرافق -----
 ("public", ("townhall",), "بلدية مقر البلدية مجلس شعبي mairie apc town hall townhall"),
 ("public", ("post_office",), "بريد بريدي بوسطة مكتب بريد poste post office"),
 ("public", ("police",), "شرطة امن درك مركز شرطة commissariat police gendarmerie"),
 ("public", (), "ادارة ادارات مرفق مرافق عمومية administration administrations public service services publics"),
 # ----- التعليم والتكوين -----
 ("education", ("school",), "مدرسة مدارس ابتدائية متوسطة ثانوية اكمالية école ecole ecoles lycée lycee collège college primaire school"),
 ("education", ("university",), "جامعة جامعات université universite university"),
 ("education", ("college",), "معهد كلية تكوين مهني cfpa institut institute centre de formation college"),
 ("education", ("kindergarten",), "روضة روضات حضانة crèche creche kindergarten maternelle"),
 ("education", ("driving_school",), "تعليم السياقة مدرسة السياقة سياقة auto école auto ecole driving school"),
 ("education", (), "تعليم دراسة تعليمي éducation education enseignement formation study"),
 # ----- العقارات والسكن -----
 ("realestate", ("estate_agent",), "وكالة عقارية عقار عقارات سمسار سمسرة agence immobilière agence immobiliere immobilier real estate estate agent property"),
 ("realestate", (), "سكن كراء شقة شقق بيع logement location appartement housing rental apartment"),
 # ----- الرياضة والشباب -----
 ("sport", ("fitness_centre",), "قاعة رياضة قاعة رياضية نادي رياضي صالة رياضة salle de sport musculation fitness gym"),
 ("sport", ("sports_centre",), "مركب رياضي مركز رياضي complexe sportif sports centre sports center"),
 ("sport", ("stadium", "pitch"), "ملعب ملاعب مدرج ستاد stade stadium terrain pitch playground"),
 ("sport", (), "رياضة رياضي شباب sport sports jeunesse football youth"),
 # ----- المال والتأمين -----
 ("finance", ("bank",), "بنك بنوك مصرف وكالة بنكية banque banques bank atm dab agence bancaire"),
 ("finance", ("bureau_de_change",), "صرف صراف صرافة change bureau de change exchange currency"),
 ("finance", (), "تأمين تامين assurance insurance caat saa مال مالية تمويل finance financier"),
 # ----- الفلاحة -----
 ("agriculture", ("veterinary",), "بيطري بيطرة طبيب بيطري vétérinaire veterinaire veterinary vet"),
 ("agriculture", ("agrarian",), "بذور اسمدة معدات فلاحية مستلزمات فلاحية semences engrais agrofourniture matériel agricole seeds fertilizer"),
 ("agriculture", (), "فلاحة فلاح فلاحي مزرعة agriculture agricole farming farmer ferme farm"),
 # ----- السياحة والسفر -----
 ("tourism", ("hotel",), "فندق فنادق hôtel hotel hotels"),
 ("tourism", ("guest_house",), "نزل دار ضيافة بيت ضيافة auberge guest house gîte gite maison d hôtes maison d hotes"),
 ("tourism", ("museum",), "متحف متاحف musée musee museum"),
 ("tourism", ("attraction",), "معلم سياحي معالم اثار site touristique attraction landmark"),
 ("tourism", ("travel_agency",), "وكالة سفر وكالة اسفار وكالة سياحية agence de voyage voyages travel agency"),
 ("tourism", (), "سياحة سفر tourisme tourism voyage touristique travel"),
]

# كل عبارة مفتاحية على حدة (تُرتّب الأطول أولاً حتى تغلب «طبيب أسنان» على «طبيب»)
_KW = []
for sector, subs, words in RULES:
    ws = words.split()
    # العبارات المتعددة الكلمات تُكتب متتالية في السلسلة، لذلك نعيد تفكيكها بالقاموس التالي
    pass

_PHRASES = {  # عبارات من أكثر من كلمة (بعد التوحيد)
    "طبيب اسنان", "طبيبه اسنان", "جراح اسنان", "طبيب عام", "مركز صحي", "قاعه علاج", "مخبزه مخبز",
    "سوبر ماركت", "مواد بناء", "محطه وقود", "محطه بنزين", "station service", "gas station", "قطع غيار",
    "pieces detachees", "spare parts", "وجبات سريعه", "fast food", "salon de the", "خدمات منزليه",
    "مقر البلديه", "مجلس شعبي", "town hall", "مكتب بريد", "post office", "مركز شرطه", "auto ecole",
    "تعليم السياقه", "مدرسه السياقه", "driving school", "centre de formation", "تكوين مهني",
    "وكاله عقاريه", "agence immobiliere", "real estate", "estate agent", "قاعه رياضه", "قاعه رياضيه",
    "نادي رياضي", "salle de sport", "مركب رياضي", "مركز رياضي", "complexe sportif", "sports centre",
    "sports center", "وكاله بنكيه", "agence bancaire", "bureau de change", "طبيب بيطري", "معدات فلاحيه",
    "مستلزمات فلاحيه", "matériel agricole", "materiel agricole", "دار ضيافه", "بيت ضيافه", "guest house",
    "maison d hotes", "وكاله سفر", "وكاله اسفار", "وكاله سياحيه", "agence de voyage", "معلم سياحي",
    "site touristique", "service public", "services publics", "public service", "كهرومنزلي",
}


def _split(words):
    """يقسّم سلسلة الكلمات إلى كلمات مفردة وعبارات معروفة."""
    toks = norm(words).split()
    out, i = [], 0
    while i < len(toks):
        for n in (3, 2):
            ph = " ".join(toks[i:i + n])
            if n > 1 and ph in _PHRASES:
                out.append(ph)
                i += n
                break
        else:
            out.append(toks[i])
            i += 1
    return out


ENTRIES = []
for _sector, _subs, _words in RULES:
    for _w in set(_split(_words)):
        ENTRIES.append((_w.split(), _sector, _subs))
ENTRIES.sort(key=lambda e: (-len(e[0]), -sum(len(x) for x in e[0])))


def _tok_match(t, k):
    s = strip_ar(t)
    if t == k or s == k:
        return True
    return len(k) >= 4 and (t.startswith(k) or s.startswith(k))


def interpret(q):
    """q نص موحّد. يعيد (القطاعات، الأنواع، الكلمات المتبقية)."""
    toks = q.split()
    used = [False] * len(toks)
    secs, subs = set(), set()
    for kw, sector, st in ENTRIES:
        n = len(kw)
        for i in range(len(toks) - n + 1):
            if any(used[i:i + n]):
                continue
            if all(_tok_match(toks[i + j], kw[j]) for j in range(n)):
                for j in range(n):
                    used[i + j] = True
                secs.add(sector)
                subs.update(st)
    rest = [strip_ar(t) for t, u in zip(toks, used) if not u and t not in STOP and len(t) >= 2]
    return secs, subs, rest
