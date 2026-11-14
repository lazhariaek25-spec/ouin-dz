"""فهم كلمات البحث (عربية/فرنسية/إنجليزية/دارجة) وربطها بالقطاعات والتخصصات."""
import unicodedata

_AR = str.maketrans({"ة": "ه", "ى": "ي", "ـ": "", "ؤ": "و", "ئ": "ي"})
STOP = {"في", "من", "عن", "على", "الى", "او", "و", "ال", "de", "du", "des", "la", "le", "les",
        "a", "en", "pour", "dans", "et", "the", "in", "near", "pres", "قريب", "ابحث", "اين", "وين"}


def norm(s):
    """توحيد: أحرف صغيرة، حذف التشكيل واللكنات، توحيد الألف والتاء المربوطة والياء."""
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c)).translate(_AR)
    for ch in "'’-_/,.()":
        s = s.replace(ch, " ")
    return " ".join(s.split())


# (القطاع, الأنواع في OSM أو "" لكل القطاع, الكلمات المفتاحية مفصولة بـ |)
RAW = [
 # --- الصحة ---
 ("health", "", "صحة|صحي|طبي|sante|health|medical|medicale|paramedical"),
 ("health", "doctors,clinic,dentist", "طبيب|اطباء|دكتور|دكاتره|طبيبة|doctor|docteur|medecin|generaliste|specialiste|cabinet medical|gynecolog|pediatre|cardiolog|dermatolog|ophtalmo|عيون|اطفال"),
 ("health", "dentist", "اسنان|سنان|dentist|dentiste|dental|dentaire|stomatolog"),
 ("health", "pharmacy", "صيدل|دواء|ادوية|pharmac|chemist|drugstore|medicament"),
 ("health", "hospital,clinic", "مستشفى|مستشفيات|مشفى|hopital|hopitaux|hospital|chu|urgence|urgences|طوارئ|emergency|epsp|ehs"),
 ("health", "clinic,hospital", "عيادة|عيادات|مصحة|clinique|polyclinique|clinic|polyclinic"),
 ("health", "laboratory", "مخبر|مخابر|تحليل|laboratoire|laboratory|analyses|analyse|labo"),
 # --- التعليم ---
 ("education", "", "تعليم|تكوين|تربية|education|enseignement|formation|training"),
 ("education", "school,college,kindergarten", "مدرسة|مدارس|ابتدائية|متوسطة|اكمالية|ثانوية|ecole|school|lycee|primaire|college|cem"),
 ("education", "university,college", "جامعة|جامعات|كلية|faculte|universite|university|campus"),
 ("education", "kindergarten", "روضة|حضانة|creche|kindergarten|maternelle|nursery"),
 ("education", "driving_school", "سياقة|auto ecole|autoecole|driving"),
 # --- الإدارات والمرافق ---
 ("public", "", "ادارة|مرفق|administration|service public|public"),
 ("public", "townhall", "بلدية|دائرة|mairie|apc|daira|townhall|town hall"),
 ("public", "post_office", "بريد|poste|post office|post|barid|ccp"),
 ("public", "police", "شرطة|درك|امن|commissariat|police|gendarmerie|surete"),
 # --- المطاعم والترفيه ---
 ("food", "", "مطاعم|اكل|اكلات|ترفيه|restauration|manger|food|dining|loisirs"),
 ("food", "restaurant,fast_food", "مطعم|restaurant|resto|pizzeria|traiteur"),
 ("food", "cafe", "مقهى|قهوة|cafe|coffee|salon de the|salon de the"),
 ("food", "fast_food,restaurant", "وجبات سريعة|شاورما|بيتزا|سندويش|fast food|fastfood|snack|sandwich|pizza|burger|tacos|shawarma"),
 # --- النقل والسيارات ---
 ("auto", "", "سيارات|سيارة|نقل|auto|voiture|automobile|car|transport"),
 ("auto", "fuel", "وقود|بنزين|مازوت|نفطال|station service|station essence|essence|gasoil|fuel|naftal|carburant|gas station"),
 ("auto", "car_repair", "ميكانيك|ميكانيكي|تصليح سيارات|ورشة|mecanic|mecanicien|garage|mechanic|repair|reparation|carrosserie|vidange"),
 ("auto", "car_parts", "قطع غيار|piece detachee|pieces detachees|pieces auto|spare parts|car parts|pneu|pneus|tires"),
 # --- المال والتأمين ---
 ("finance", "", "مال|مالية|تمويل|finance|financier|financial"),
 ("finance", "bank", "بنك|بنوك|مصرف|banque|bank|agence bancaire|atm|dab"),
 ("finance", "bureau_de_change,bank", "صرف|صراف|bureau de change|change|exchange|devise"),
 ("finance", "insurance", "تامين|assurance|insurance|caat|saa|cnma"),
 # --- التجارة والتسوق ---
 ("shopping", "", "تسوق|تجارة|محل|محلات|متجر|commerce|shopping|magasin|boutique|store|shop"),
 ("shopping", "bakery", "مخبز|مخبزة|خبز|boulangerie|bakery|pain|patisserie"),
 ("shopping", "supermarket,convenience", "سوبرماركت|بقالة|مواد غذائية|supermarche|supermarket|hypermarche|epicerie|grocery|alimentation|superette"),
 ("shopping", "clothes", "ملابس|لباس|الباس|vetement|vetements|clothes|clothing|habits|mode|fashion|prêt à porter|pret a porter"),
 ("shopping", "mobile_phone,electronics", "هاتف|هواتف|جوال|telephone|mobile|phone|smartphone"),
 ("shopping", "electronics", "الكترونيات|كمبيوتر|معلوماتية|electronique|electronic|informatique|computer|ordinateur|electromenager"),
 ("shopping", "butcher", "جزار|لحوم|boucherie|boucher|butcher|viande"),
 ("shopping", "hardware", "ادوات|bricolage|quincaillerie|hardware"),
 ("shopping", "marketplace,supermarket", "سوق|marche|market"),
 # --- الحرف والخدمات ---
 ("trades", "", "حرف|حرفي|حرفيين|خدمات|صيانة|artisan|artisans|metier|services|depannage|maintenance"),
 ("trades", "electrician", "كهرباء|كهربائي|electricite|electricien|electrician|electric"),
 ("trades", "plumber", "سباك|سباكة|plomberie|plombier|plumber|plumbing"),
 ("trades", "carpenter", "نجار|نجارة|menuisier|menuiserie|carpenter|carpentry"),
 ("trades", "painter", "دهان|صباغة|peintre|peinture|painter|painting"),
 ("trades", "welder", "لحام|soudeur|soudure|welder|welding|ferronnerie"),
 ("trades", "tiler", "بلاط|زليج|carreleur|carrelage|tiler|tiling|faience"),
 ("trades", "locksmith", "قفال|serrurier|serrurerie|locksmith"),
 ("trades", "tailor", "خياط|خياطة|tailleur|couturier|couture|tailor"),
 ("trades", "builder", "بناء|بناية|مقاول|macon|maconnerie|builder|construction|entrepreneur"),
 # --- العقارات ---
 ("realestate", "", "عقار|عقارات|سكن|كراء|immobilier|logement|location|real estate|property|agence immobiliere|estate agent"),
 # --- الرياضة والشباب ---
 ("sport", "", "رياضة|رياضي|شباب|sport|sports|sportif|jeunesse"),
 ("sport", "fitness_centre", "قاعة رياضة|كمال اجسام|salle de sport|gym|fitness|musculation|bodybuilding"),
 ("sport", "stadium,pitch,sports_centre", "ملعب|ملاعب|مركب رياضي|stade|stadium|terrain|pitch|football|complexe sportif|sports centre"),
 # --- الفلاحة ---
 ("agriculture", "", "فلاحة|فلاحي|مزرعة|agriculture|agricole|farm|ferme|agricultural"),
 ("agriculture", "veterinary", "بيطري|بيطرة|veterinaire|veterinary|vet"),
 ("agriculture", "agrarian", "بذور|اسمدة|اعلاف|semence|semences|engrais|agrarian|aliment betail|grains"),
 # --- السياحة والسفر ---
 ("tourism", "", "سياحة|سياحي|سفر|tourisme|tourism|touristique|voyage|travel"),
 ("tourism", "hotel,guest_house", "فندق|فنادق|hotel|auberge|resort|hebergement"),
 ("tourism", "guest_house", "نزل|دار ضيافة|maison d hote|guest house|guesthouse|gite|chambre d hote"),
 ("tourism", "museum", "متحف|متاحف|musee|museum"),
 ("tourism", "attraction,museum", "معلم|معالم|منتزه|site touristique|attraction|monument"),
 ("tourism", "travel_agency", "وكالة سفر|وكالات سفر|وكالة اسفار|agence de voyage|agence voyage|travel agency"),
]
CONCEPTS = [(sec, tuple(s.split(",")) if s else None, tuple(dict.fromkeys(norm(t) for t in terms.split("|"))))
            for sec, s, terms in RAW]


def hit(term, qn, toks):
    return (len(term) >= 4 and term in qn) or term in toks


def parse(q):
    """يعيد (النص الموحّد، المفاهيم المطابقة، الكلمات المتبقية)."""
    qn = norm(q)
    toks = set(qn.split())
    concepts = [c for c in CONCEPTS if any(hit(t, qn, toks) for t in c[2])]
    used = [t for c in concepts for t in c[2] if hit(t, qn, toks)]
    rest = [w for w in qn.split()
            if w not in STOP and not any(w == t or (len(t) >= 4 and t in w) for t in used)]
    return qn, concepts, rest


def score(sector, subtype, ntext, concepts):
    """مجموع نقاط المفاهيم: 10 تطابق نوع، 6 تطابق نص ضمن القطاع، 2 قطاع فقط."""
    total = 0
    for sec, subs, terms in concepts:
        if subs is None:
            total += 2 if sector == sec else 0
        elif subtype in subs:
            total += 10
        elif sector == sec and any(len(t) >= 4 and t in ntext for t in terms):
            total += 6
    return total
