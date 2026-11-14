"""تطبيع النصوص (عربي/فرنسي/إنجليزي) + قاموس الكلمات المفتاحية لكل القطاعات."""
import re
import unicodedata

_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
_MAP = str.maketrans({"ى": "ي", "ة": "ه", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "و", "ئ": "ي", "ڤ": "ف", "گ": "ك"})


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = _DIAC.sub("", re.sub(r"[\u0300-\u036f]", "", s)).translate(_MAP)
    s = re.sub(r"[^\w\s]|_", " ", s)
    return " ".join(t[2:] if t.startswith("ال") and len(t) > 4 else t for t in s.split())


# (القطاع، أنواع OSM بترتيب الأهمية — فارغة = القطاع كله، الكلمات)
CONCEPTS = [
 ("health", (), "صحة|صحي|طبي|طبية|santé|sante|health|medical|médical|healthcare"),
 ("health", ("doctors", "clinic", "hospital", "dentist"), "طبيب|طبيبة|دكتور|دكتورة|دوكتور|توبيب|docteur|médecin|medecin|doctor|physician|généraliste|generaliste|gp|spécialiste|specialiste|أخصائي|اخصائي"),
 ("health", ("pharmacy",), "صيدلية|صيدلي|صيدلانية|صيدلاني|فارمسي|فرمسي|pharmacie|pharmacien|pharmacy|pharmacist|pharma|drugstore"),
 ("health", ("hospital", "clinic"), "مستشفى|مستشفيات|سبيطار|سبيتار|hopital|hôpital|hospital|chu|epsp|ehs|urgences|urgence|طوارئ"),
 ("health", ("clinic", "doctors", "hospital"), "عيادة|عيادات|مصحة|مستوصف|clinique|clinic|polyclinique|salle de soins|قاعة علاج"),
 ("health", ("dentist",), "أسنان|اسنان|طبيب أسنان|جراح أسنان|dentiste|dentist|dentaire|dental|orthodontiste|dentistry"),
 ("health", ("laboratory",), "مخبر|مختبر|تحاليل|laboratoire|labo|laboratory|analyses|analyse|lab"),
 ("shopping", (), "تسوق|تجارة|تجاري|محل|محلات|سوق|commerce|magasin|boutique|shopping|shop|store|market|marché|marche"),
 ("shopping", ("supermarket", "convenience"), "سوبرماركت|سوبيرات|بقالة|ماركت|حانوت|مواد غذائية|supermarché|supermarche|supermarket|épicerie|epicerie|grocery|alimentation|superette|supérette"),
 ("shopping", ("bakery",), "مخبزة|مخابز|خبز|خباز|فران|boulangerie|boulanger|bakery|pain|patisserie|pâtisserie|حلويات"),
 ("shopping", ("clothes",), "ملابس|لباس|حوايج|كسوة|vêtements|vetements|habits|clothes|clothing|prêt-à-porter|pret a porter|mode|fashion"),
 ("shopping", ("mobile_phone", "electronics"), "هاتف|هواتف|تلفون|موبايل|إلكترونيات|الكترونيات|كمبيوتر|électronique|electronique|téléphone|telephone|phone|mobile|electronics|informatique|computer"),
 ("shopping", ("butcher",), "جزار|جزارة|لحم|لحوم|boucherie|boucher|butcher|meat|viande"),
 ("shopping", ("hardware",), "أدوات|مواد بناء|quincaillerie|hardware|bricolage"),
 ("auto", (), "سيارات|سيارة|نقل|voiture|voitures|auto|automobile|car|cars|transport|véhicule|vehicule"),
 ("auto", ("car_repair",), "ميكانيكي|ميكانيك|ميكانيسيان|ورشة|ورشة سيارات|mécanicien|mecanicien|mécanique|mecanique|garage|mechanic|repair|réparation|reparation|carrosserie|tôlier|tolier"),
 ("auto", ("fuel",), "وقود|بنزين|محطة|محطة وقود|مازوت|نفطال|station|station service|station essence|essence|carburant|gas|fuel|petrol|diesel|naftal|gaz"),
 ("auto", ("car_parts",), "قطع غيار|قطع الغيار|pièces|pieces|pièces détachées|pieces detachees|spare parts|auto parts|accessoires auto"),
 ("food", (), "مطاعم|أكل|اكل|طعام|ترفيه|restauration|manger|food|eat|dining|restaurants|bouffe"),
 ("food", ("restaurant", "fast_food"), "مطعم|restaurant|resto|pizzeria|pizza|snack|fast food|fastfood|وجبات سريعة|بيتزا|ساندويتش|ساندوتش|sandwich|مشوي|grill|rôtisserie|rotisserie|tacos|burger"),
 ("food", ("cafe",), "مقهى|مقاهي|قهوة|كافي|كافيتيريا|café|cafe|coffee|salon de thé|salon de the|cafeteria"),
 ("trades", (), "حرف|حرفي|حرفيين|صنايع|صانع|artisan|artisans|trades|craftsman|handyman|bricoleur"),
 ("trades", ("electrician",), "كهربائي|كهربا|كهرباء|électricien|electricien|electrician|électricité|electricite|electric"),
 ("trades", ("plumber",), "سباك|سباكة|بلومبي|plombier|plomberie|plumber|plumbing"),
 ("trades", ("carpenter",), "نجار|نجارة|menuisier|menuiserie|carpenter|carpentry"),
 ("trades", ("painter",), "دهان|صباغ|peintre|peinture|painter|painting"),
 ("trades", ("welder",), "لحام|حداد|soudeur|soudure|welder|ferronnier"),
 ("trades", ("builder", "tiler"), "بناء|بنّاء|بناي|تبليط|maçon|macon|maçonnerie|builder|construction|carreleur|tiler|carrelage"),
 ("trades", ("locksmith",), "قفال|serrurier|serrure|locksmith"),
 ("trades", ("tailor",), "خياط|خياطة|tailleur|couturier|couture|tailor"),
 ("public", (), "إدارة|إدارات|إدارية|مرافق|administration|administrations|public|gov|government|services publics"),
 ("public", ("post_office",), "بريد|بوسطة|poste|postal|post office|algérie poste|algerie poste"),
 ("public", ("townhall",), "بلدية|دائرة|مقر البلدية|mairie|apc|municipalité|municipalite|townhall|town hall"),
 ("public", ("police",), "شرطة|أمن|درك|commissariat|police|gendarmerie"),
 ("education", (), "تعليم|تكوين|تربية|دراسة|éducation|education|formation|study|learning|enseignement"),
 ("education", ("school", "kindergarten"), "مدرسة|مدارس|ابتدائية|متوسطة|ثانوية|روضة|école|ecole|lycée|lycee|school|primaire|crèche|creche|kindergarten|cem"),
 ("education", ("university", "college"), "جامعة|جامعات|كلية|université|universite|faculté|faculte|university|campus|college|collège|institut|معهد"),
 ("education", ("driving_school",), "مدرسة سياقة|تعليم السياقة|سياقة|auto-école|auto ecole|autoécole|driving school"),
 ("realestate", (), "عقار|عقارات|سكن|كراء|وكالة عقارية|immobilier|real estate|logement|agence immobilière|agence immobiliere|immo|estate"),
 ("sport", (), "رياضة|رياضي|نادي|sport|sports|club|jeunesse|شباب"),
 ("sport", ("fitness_centre",), "قاعة رياضة|قاعة رياضية|صالة رياضية|جيم|gym|salle de sport|fitness|musculation|كمال أجسام"),
 ("sport", ("stadium", "pitch", "sports_centre"), "ملعب|ملاعب|مركب رياضي|كرة القدم|stade|stadium|terrain|pitch|football|complexe sportif"),
 ("finance", (), "مال|مالية|مالي|finance|financier|banking|banque assurance"),
 ("finance", ("bank",), "بنك|بنوك|مصرف|banque|bank|agence bancaire|cpa|bna|bea|badr|bdl|cnep|atm|dab|موزع آلي"),
 ("finance", ("bureau_de_change",), "صرافة|صرف|bureau de change|exchange|currency|change"),
 ("finance", ("insurance",), "تأمين|تامين|assurance|insurance|caat|saa|cnma|gam"),
 ("agriculture", (), "فلاحة|فلاحي|فلاح|زراعة|مزرعة|agriculture|agricole|ferme|farm|farming"),
 ("agriculture", ("veterinary",), "بيطري|بيطرة|vétérinaire|veterinaire|vet|veterinary"),
 ("agriculture", ("agrarian",), "بذور|أسمدة|معدات فلاحية|semences|engrais|grainetier|agrarian|seeds|fertilizer|matériel agricole|materiel agricole"),
 ("tourism", (), "سياحة|سياحي|سفر|tourisme|tourism|travel|voyage|touristique|vacances|holiday"),
 ("tourism", ("hotel", "guest_house"), "فندق|فنادق|نزل|إقامة|بيت ضيافة|hôtel|hotel|auberge|gîte|gite|guest house|hostel|maison d hôtes|maison d hotes"),
 ("tourism", ("museum", "attraction"), "متحف|معلم|معالم|musée|musee|museum|attraction|site touristique|monument"),
 ("tourism", ("travel_agency",), "وكالة سفر|وكالة أسفار|وكالة سياحية|agence de voyage|agence de voyages|travel agency"),
]

KEYS = {}
for _sec, _subs, _kw in CONCEPTS:
    for _k in _kw.split("|"):
        KEYS.setdefault(norm(_k), []).append((_sec, _subs))
KEYLIST1 = [k for k in KEYS if " " not in k]

STOP = set(norm("في من على الى إلى عن مع او أو قريب قريبة بجانب جانب حول مناوبة مناوب de la le les du des d l a au aux en et "
                "pres proche autour pour for with near in at the of and or un une garde nuit 24h 24 7 ليلية").split())

_W = ("01|أدرار|Adrar;02|الشلف|Chlef;03|الأغواط|Laghouat;04|أم البواقي|Oum El Bouaghi;05|باتنة|Batna;06|بجاية|Béjaïa;"
      "07|بسكرة|Biskra;08|بشار|Béchar;09|البليدة|Blida;10|البويرة|Bouira;11|تمنراست|Tamanrasset;12|تبسة|Tébessa;"
      "13|تلمسان|Tlemcen;14|تيارت|Tiaret;15|تيزي وزو|Tizi Ouzou;16|الجزائر العاصمة|Alger;17|الجلفة|Djelfa;18|جيجل|Jijel;"
      "19|سطيف|Sétif;20|سعيدة|Saïda;21|سكيكدة|Skikda;22|سيدي بلعباس|Sidi Bel Abbès;23|عنابة|Annaba;24|قالمة|Guelma;"
      "25|قسنطينة|Constantine;26|المدية|Médéa;27|مستغانم|Mostaganem;28|المسيلة|M'Sila;29|معسكر|Mascara;30|ورقلة|Ouargla;"
      "31|وهران|Oran;32|البيض|El Bayadh;33|إليزي|Illizi;34|برج بوعريريج|Bordj Bou Arreridj;35|بومرداس|Boumerdès;"
      "36|الطارف|El Tarf;37|تندوف|Tindouf;38|تيسمسيلت|Tissemsilt;39|الوادي|El Oued;40|خنشلة|Khenchela;41|سوق أهراس|Souk Ahras;"
      "42|تيبازة|Tipaza;43|ميلة|Mila;44|عين الدفلى|Aïn Defla;45|النعامة|Naâma;46|عين تموشنت|Aïn Témouchent;47|غرداية|Ghardaïa;"
      "48|غليزان|Relizane;49|تيميمون|Timimoun;50|برج باجي مختار|Bordj Badji Mokhtar;51|أولاد جلال|Ouled Djellal;"
      "52|بني عباس|Béni Abbès;53|عين صالح|In Salah;54|عين قزام|In Guezzam;55|تقرت|Touggourt;56|جانت|Djanet;"
      "57|المغير|El M'Ghair;58|المنيعة|El Menia")
WIL = {}
for _x in _W.split(";"):
    _c, _a, _f = _x.split("|")
    for _n in (_a, _f):
        WIL[norm(_n)] = _c
for _n, _c in (("الجزائر", "16"), ("algiers", "16"), ("alger centre", "16"), ("constantina", "25"),
               ("wahran", "31"), ("setif", "19"), ("sidi bel abbes", "22"), ("sba", "22")):
    WIL[norm(_n)] = _c


def backfill(con):
    """يضمن وجود عمود البحث المطبّع s ويملؤه للسجلات الناقصة."""
    have = {r[1] for r in con.execute("PRAGMA table_info(places)")}
    if "s" not in have:
        con.execute("ALTER TABLE places ADD COLUMN s TEXT")
    rows = con.execute("SELECT osm_id,name,name_ar,name_fr,address,subtype FROM places WHERE s IS NULL").fetchall()
    con.executemany("UPDATE places SET s=? WHERE osm_id=?",
                    [(norm(" ".join(str(x) for x in r[1:] if x)), r[0]) for r in rows])
    con.commit()
