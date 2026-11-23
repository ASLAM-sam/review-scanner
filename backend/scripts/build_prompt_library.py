"""
Smart Feedback Prompt Library Generator & Validator
Assembles 265+ unique natural-language prompts across 11 dining categories and 3 languages.
Enforces zero duplicate IDs and zero duplicate texts per language.
"""

import json
from pathlib import Path
from typing import Dict, List

CATEGORIES = [
    ("food_quality", "Food Quality"),
    ("taste_freshness", "Taste and Freshness"),
    ("food_presentation", "Food Presentation"),
    ("service_staff", "Service and Staff Behaviour"),
    ("speed_of_service", "Speed of Service"),
    ("restaurant_ambience", "Restaurant Ambience"),
    ("cleanliness_hygiene", "Cleanliness and Hygiene"),
    ("family_dining", "Family Dining Experience"),
    ("value_for_money", "Value for Money"),
    ("drinks_beverages", "Drinks and Beverages"),
    ("overall_experience", "Overall Experience"),
]

ENGLISH_PROMPTS = {
    "food_quality": {
        "positive": [
            "The food quality was exceptional and cooked to perfection.",
            "Every dish tasted like it was made with top-tier fresh ingredients.",
            "The meat was tender, juicy, and well-seasoned throughout.",
            "The flavors were rich, authentic, and well-balanced.",
            "You can truly taste the craftsmanship and culinary care in every course.",
            "The starters and main courses were both consistently delicious.",
            "The texture and aroma of each dish were completely spot on.",
            "A memorable culinary experience from the very first bite.",
            "The breads and sides were served warm, soft, and freshly prepared.",
            "The chef's special dish exceeded all our dining expectations.",
            "Consistently high cooking standards across every single item ordered.",
            "The balance of spices was perfectly dialed in for our taste.",
            "Rich depth of flavor without feeling overly greasy or heavy.",
            "Outstanding food quality that will keep us coming back regularly.",
        ],
        "neutral": [
            "The food quality met standard casual dining expectations.",
            "The dishes were decent but did not particularly stand out.",
            "Some dishes were great while others were fairly ordinary.",
            "A typical dining experience with standard everyday food quality.",
            "The cooking was satisfactory for a quick casual lunch.",
            "The flavors were mild and palatable, though not especially memorable.",
        ],
        "improvement": [
            "The food quality was inconsistent with what we hoped for.",
            "The dishes felt under-seasoned and lacked depth of flavor.",
            "The meat was slightly tough and overcooked in our main course.",
            "A few items felt like they had been sitting under a warmer too long.",
            "The food felt a bit too oily and heavy for our preference.",
            "The recipes could benefit from more authentic culinary seasoning.",
        ],
    },
    "taste_freshness": {
        "positive": [
            "The ingredients tasted exceptionally fresh and vibrant.",
            "Crisp vegetables and garden-fresh herbs in every single dish.",
            "The seafood was extraordinarily fresh and cleanly prepared.",
            "The food arrived piping hot, straight from the kitchen stove.",
            "You could clearly tell the sauces were made fresh today.",
            "Clean, natural flavors without any artificial aftertaste.",
            "The salad greens were crisp, crunchy, and freshly tossed.",
            "Freshly ground spices gave the gravy incredible aroma and depth.",
            "A wonderful burst of fresh flavors in every bite.",
            "The dairy and cheeses tasted wholesome, rich, and very fresh.",
            "Unbeatable fresh taste from the appetizers right through to dessert.",
            "The baked items tasted oven-fresh and wonderfully light.",
        ],
        "neutral": [
            "The freshness was average, consistent with standard dining.",
            "The taste was acceptable, though not strikingly fresh.",
            "Felt like standard pantry ingredients were used for the meal.",
            "The temperature was warm enough, though not straight from the flame.",
            "The freshness varied noticeably between the appetizers and the mains.",
            "Average everyday taste that satisfied hunger without delighting.",
        ],
        "improvement": [
            "The vegetables lacked crispness and felt slightly tired.",
            "The dish had a reheated taste rather than freshly prepared cooking.",
            "The food arrived lukewarm rather than fresh and steaming hot.",
            "The bread felt a bit dry, as if prepared several hours earlier.",
            "The herbs and garnishes did not look or taste fresh.",
            "The seasoning had an overpowering saltiness that masked ingredient freshness.",
        ],
    },
    "food_presentation": {
        "positive": [
            "The plating was artistic, elegant, and restaurant-worthy.",
            "Beautiful visual presentation that made the food immediately inviting.",
            "Great attention to detail with vibrant color contrasts and garnishes.",
            "The portion layout on the plate was clean, balanced, and appetizing.",
            "Every plate arrived looking like a work of culinary art.",
            "Vibrant, colorful ingredients that made the dishes visually pop.",
            "Served in attractive tableware that elevated the whole dining experience.",
            "The sizzling presentation at our table was exciting and fun.",
            "Generous portions arranged with noticeable care and elegance.",
            "The dessert presentation was stunning and worthy of a photograph.",
            "Clean edges and immaculate plating on every single dish served.",
            "A genuine feast for the eyes before we even took the first bite.",
        ],
        "neutral": [
            "The presentation was simple, neat, and functional.",
            "Standard casual plating without any special visual flourishes.",
            "The presentation was tidy, though fairly plain in appearance.",
            "Food was served practically, focusing on substance over visual style.",
            "The plating was tidy enough for a neighborhood family eatery.",
            "Adequate visual layout without memorable artistic appeal.",
        ],
        "improvement": [
            "The plating looked somewhat rushed, crowded, and messy.",
            "Sauce splatters on the rim of the plate should be wiped before serving.",
            "The visual arrangement looked dull and lacked vibrant colors.",
            "The dish looked unappealing compared to menu expectations.",
            "Garnishes looked wilted and added little value to the presentation.",
            "The serving platters and bowls felt slightly worn or chipped.",
        ],
    },
    "service_staff": {
        "positive": [
            "The staff was remarkably polite, warm, and genuinely attentive.",
            "Our server was knowledgeable and gave spot-on menu recommendations.",
            "We were greeted with warm smiles from the moment we walked in.",
            "The team anticipated our table needs before we even had to ask.",
            "Courteous and respectful staff who made us feel like honored guests.",
            "Servers checked in at the right moments without hovering or interrupting.",
            "The staff accommodated our dietary preferences with great kindness.",
            "Exceptional hospitality that made our family dinner feel special.",
            "The manager stopped by our table to ensure everything was satisfactory.",
            "Friendly, cheerful, and patient service even during a busy rush.",
            "The waitstaff handled our special requests smoothly and cheerfully.",
            "High professionalism, quick smiles, and attentive hospitality etiquette.",
            "Staff treated us with exceptional courtesy throughout the entire meal.",
        ],
        "neutral": [
            "The service was functional and took care of basic dining needs.",
            "Staff were polite, though interaction was very minimal and brief.",
            "Standard service without any notable memorable highs or lows.",
            "The staff took orders and cleared plates adequately.",
            "Service was businesslike, straightforward, and no-nonsense.",
            "Staff fulfilled requests when asked, though not particularly proactive.",
        ],
        "improvement": [
            "The staff seemed distracted, inattentive, and hard to flag down.",
            "Our server appeared overwhelmed and forgot a key request we made.",
            "We had to ask multiple times for basic table items like water and napkins.",
            "The greeting at the front reception felt rather cold and indifferent.",
            "Staff could show more warmth, patience, and customer friendliness.",
            "The waitstaff seemed to rush us through ordering and clearing.",
        ],
    },
    "speed_of_service": {
        "positive": [
            "Incredibly fast service from seating right through to the first course.",
            "Food arrived promptly without any unnecessary or frustrating waiting.",
            "Appetizers and drinks were brought out within minutes of ordering.",
            "The timing between courses was paced perfectly for our table.",
            "Quick and efficient ordering, billing, and payment process.",
            "Impressively fast kitchen turnaround during the peak dining rush.",
            "Drinks were refilled promptly without having to flag down staff.",
            "Everything arrived hot and fast without our meal feeling hurried.",
            "A great spot when you need a speedy yet delicious sit-down meal.",
            "Smooth and rapid table turnover without feeling rushed to leave.",
            "Our orders were taken immediately and processed without delay.",
            "An efficient, well-coordinated kitchen that kept our dining flow moving.",
        ],
        "neutral": [
            "The wait time was standard and expected for a sit-down restaurant.",
            "Service speed was reasonable, neither remarkably fast nor slow.",
            "Pacing between dishes was acceptable for our party.",
            "Took around 15 to 20 minutes for mains, which felt reasonable.",
            "Average wait times considering the size of the dining crowd.",
            "Speed was tolerable for a weekend evening dinner service.",
        ],
        "improvement": [
            "The wait time for our food was considerably longer than expected.",
            "We waited too long between the appetizers and the main courses.",
            "Clearing the table and getting the final bill took too much time.",
            "The kitchen seemed backed up, causing substantial delays for our table.",
            "We waited quite a while at our table before anyone came to take our order.",
            "Drinks took almost as long to arrive as the cooked food.",
        ],
    },
    "restaurant_ambience": {
        "positive": [
            "Charming, cozy atmosphere that immediately sets a relaxed mood.",
            "Tasteful interior decor with warm, pleasant, and flattering lighting.",
            "Background music was played at the perfect conversational volume.",
            "Modern, stylish interior that feels upscale yet warm and welcoming.",
            "Comfortable seating and well-spaced dining tables for privacy.",
            "A wonderful vibe suitable for romantic dates, friends, and family dinners.",
            "Pleasant room temperature with fresh, well-ventilated air.",
            "A serene, calming dining atmosphere away from outside street noise.",
            "Beautiful aesthetic touches that add genuine charm to the dining room.",
            "Lively, upbeat atmosphere with wonderful dining energy all around.",
            "The seating layout and lighting created a cozy, intimate space.",
            "Thoughtful interior design that gives the restaurant distinct personality.",
        ],
        "neutral": [
            "Standard dining room setup with conventional lighting and furnishings.",
            "The atmosphere was fine, typical of a casual neighborhood restaurant.",
            "Nothing particularly distinctive about the decor, but clean and comfortable.",
            "Music was generic background radio, which was completely harmless.",
            "Basic seating that was comfortable enough for a quick meal.",
            "Average ambience suitable for a routine everyday meal.",
        ],
        "improvement": [
            "The background music was too loud to hold an easy conversation.",
            "The dining area felt slightly cramped with closely packed tables.",
            "The lighting was overly harsh and bright for an evening meal.",
            "The dining room temperature felt uncomfortably warm or drafty.",
            "The dining room had too much echo, making it noisy and chaotic.",
            "The interior decor and furnishings are beginning to look worn.",
        ],
    },
    "cleanliness_hygiene": {
        "positive": [
            "Impeccably clean dining area, spotless tables, and shiny floors.",
            "Cutlery and glassware were completely spotless, dry, and polished.",
            "The restrooms were thoroughly clean, fresh-smelling, and well-stocked.",
            "Tables were wiped and sanitized promptly after guests departed.",
            "Noticeably high hygiene standards throughout the entire premise.",
            "Clean uniforms and well-groomed presentation by all service staff.",
            "The visible kitchen and food prep area looked spotless and orderly.",
            "Crisp, clean menus, clean salt shakers, and tidy condiment stations.",
            "Clear and reassuring emphasis on guest hygiene and clean dining.",
            "Fresh, pleasant scent in the dining room with zero lingering kitchen odors.",
            "Spotless cloth napkins, sparkling plates, and clean serving platters.",
            "A reassuringly hygienic environment that immediately builds dining trust.",
        ],
        "neutral": [
            "Cleanliness was acceptable and within basic commercial dining norms.",
            "Tables were cleared, though not immediately wiped down with sanitizer.",
            "The restroom was adequately maintained, though basic in amenities.",
            "Standard cleanliness that you would expect at any busy neighborhood eatery.",
            "No obvious hygiene issues observed; general tidiness was satisfactory.",
            "Average cleanliness with no major complaints or special praise.",
        ],
        "improvement": [
            "The tabletop felt slightly sticky and needed a more thorough wipe.",
            "A water glass or fork had noticeable water spots or smudges.",
            "The restroom could benefit from more frequent cleaning and supplies.",
            "The floor had food crumbs left behind from previous diners.",
            "Menu cards felt greasy and should be sanitized between guests.",
            "Condiment containers on the table needed wiping down.",
        ],
    },
    "family_dining": {
        "positive": [
            "Fantastic family-friendly restaurant with a warm, welcoming vibe.",
            "Great kid-friendly food options that children genuinely enjoyed.",
            "High chairs and child amenities were provided promptly without asking.",
            "Spacious seating that accommodated our multi-generational family comfortably.",
            "The staff was especially kind, patient, and sweet with our young children.",
            "A diverse menu with great variety so every family member found something they loved.",
            "Comfortable, wholesome setting ideal for relaxed family get-togethers.",
            "Portions were generous and easily shared amongst the entire family.",
            "Our family dinner was peaceful, joyful, and thoroughly enjoyable.",
            "A great dining place to celebrate family birthdays and milestone occasions.",
            "Noise levels were comfortable and very forgiving for families with kids.",
            "The staff went out of their way to make our elderly family members comfortable.",
        ],
        "neutral": [
            "Standard family dining setting with adequate seating space.",
            "Kids found something to eat, though options were fairly basic.",
            "Acceptable for a family meal, though not specifically geared for young children.",
            "A typical restaurant experience for an everyday family outing.",
            "Average family seating without special children's accommodations.",
            "Fine for teenagers and older family members, less ideal for toddlers.",
        ],
        "improvement": [
            "The menu could use more healthy, kid-friendly options for families.",
            "The seating layout was too tight to maneuver a stroller comfortably.",
            "High chairs were either limited in quantity or not wiped down.",
            "Staff seemed slightly impatient with young children at the table.",
            "Food took a bit too long, which is difficult when dining with hungry children.",
            "No changing station or family amenities in the restroom.",
        ],
    },
    "value_for_money": {
        "positive": [
            "Exceptional value considering the high food quality and portion sizes.",
            "Very fair and reasonable pricing for such skilled culinary standards.",
            "Generous portion sizes that left our whole party completely satisfied.",
            "Great value combo deals, specials, and competitive lunch pricing.",
            "Worth every single rupee spent today for the quality delivered.",
            "High-end restaurant flavors at very accessible, fair price points.",
            "Left the restaurant feeling we received outstanding dining value.",
            "Affordable family dining without sacrificing fresh ingredients or quality.",
            "Great price-to-quality ratio compared to other restaurants in this area.",
            "Transparent billing with no unexpected hidden fees or surprise charges.",
            "Generous accompaniments, sauces, and sides included without extra nickel-and-diming.",
            "One of the best value dining spots in town for quality and taste.",
        ],
        "neutral": [
            "Pricing is reasonable and right in line with current market rates.",
            "Fair value: the food quality and portion sizes matched the price point.",
            "Portion sizes were standard for what was charged on the menu.",
            "Neither inexpensive nor overpriced for this style of restaurant.",
            "Decent value, acceptable for a routine casual meal.",
            "Standard competitive pricing for the neighborhood dining scene.",
        ],
        "improvement": [
            "The portion sizes were noticeably small for the prices charged.",
            "Felt somewhat overpriced for the quality and preparation delivered.",
            "A bit on the expensive side compared to similar dining alternatives nearby.",
            "Side dishes and beverage extras were priced higher than expected.",
            "The final bill felt disproportionate to the overall dining experience.",
            "Beverage or service add-ons felt noticeably marked up.",
        ],
    },
    "drinks_beverages": {
        "positive": [
            "The mocktails and beverages were delightfully refreshing and balanced.",
            "Freshly brewed tea and coffee with rich aroma and authentic flavor.",
            "Cold drinks were chilled to perfection and beautifully garnished.",
            "Creative beverage menu featuring unique flavor combinations.",
            "Fresh fruit juices tasted completely natural and freshly squeezed.",
            "The signature house specialty beverage was absolutely phenomenal.",
            "Water glasses were kept topped up with chilled, crisp water.",
            "Well-crafted beverages that paired wonderfully with our meals.",
            "Great temperature and aroma on both hot and iced beverage orders.",
            "Drink servings were generous and arrived in stylish glassware.",
            "Smoothies and shakes were thick, creamy, and packed with flavor.",
            "A thoughtfully curated drink menu with something refreshing for everyone.",
        ],
        "neutral": [
            "The beverage selection was standard and as expected for casual dining.",
            "Drink options were adequate, featuring typical sodas, juices, and tea.",
            "Coffee was acceptable, standard machine brew with decent taste.",
            "The specialty drink was okay, though leaned slightly sweet for our taste.",
            "Standard drink temperatures and everyday glassware presentation.",
            "Satisfactory drink options to accompany a casual lunch or dinner.",
        ],
        "improvement": [
            "The iced drinks arrived with too much ice, diluting the flavor quickly.",
            "The beverage was overly sweet and tasted artificial rather than fresh.",
            "Hot coffee or tea was served lukewarm instead of steaming hot.",
            "Limited selection of healthy, sugar-free, or non-carbonated drinks.",
            "Our drinks arrived long after the hot food was already served.",
            "The carbonated beverage tasted slightly flat and lacked crisp fizz.",
        ],
    },
    "overall_experience": {
        "positive": [
            "An exceptional dining experience that our entire party thoroughly enjoyed.",
            "Everything from the appetizers to the hospitality was top notch.",
            "We had a wonderful dining time and will definitely return very soon.",
            "Quickly becoming one of our favorite dining spots in the neighborhood.",
            "Consistently wonderful dining experience every single time we visit.",
            "A delightful meal that brightened up our day and satisfied our cravings.",
            "Will enthusiastically recommend this restaurant to our friends and colleagues.",
            "Exceeded all our expectations across food, hospitality, and atmosphere.",
            "A true five-star dining experience from the moment we arrived until we left.",
            "Left the restaurant feeling happy, satisfied, and wonderfully taken care of.",
            "Our guests from out of town were thoroughly impressed with everything.",
            "Thank you to the kitchen and floor staff for an unforgettable evening!",
            "Flawless execution by both the culinary team and the front of house.",
            "A perfect dining destination for celebrating special occasions with loved ones.",
        ],
        "neutral": [
            "An overall satisfactory visit that met our basic dining expectations.",
            "A decent meal for lunch, nothing extraordinarily memorable but good.",
            "An average restaurant experience comparable to most casual eateries.",
            "Had a pleasant enough visit, standard across food, service, and vibe.",
            "Good for a quick meal on the go; will likely drop by again if nearby.",
            "A balanced dining experience with a few nice highs and minor flaws.",
        ],
        "improvement": [
            "The visit fell somewhat short of the high standards we had hoped for.",
            "Several small service and food issues combined to dampen the experience.",
            "With a few operational adjustments, this restaurant could be much better.",
            "Hoping for a smoother, more attentive dining experience on our next visit.",
            "Did not quite live up to the enthusiastic recommendations we had heard.",
            "The dining experience was underwhelming considering our expectations.",
        ],
    },
}

# Verified natural translations for major regional prompts (Telugu & Hindi)
TELUGU_PROMPTS = [
    {
        "category": "food_quality",
        "sentiment": "positive",
        "text": "ఆహారం చాలా రుచిగా, తాజాగా మరియు వేడిగా అందించబడింది.",
    },
    {
        "category": "food_quality",
        "sentiment": "neutral",
        "text": "ఆహారం నాణ్యత సాధారణంగా ఉంది, పరవాలేదు.",
    },
    {
        "category": "food_quality",
        "sentiment": "improvement",
        "text": "ఆహారంలో మసాలాలు మరియు రుచి కొంచెం మెరుగుపరచవచ్చు.",
    },
    {
        "category": "taste_freshness",
        "sentiment": "positive",
        "text": "కూరగాయలు మరియు పదార్థాలు చాలా తాజాగా ఉన్నాయి.",
    },
    {
        "category": "taste_freshness",
        "sentiment": "improvement",
        "text": "ఆహారం వేడిగా రాలేదు, కొంచెం చల్లగా ఉంది.",
    },
    {
        "category": "service_staff",
        "sentiment": "positive",
        "text": "సిబ్బంది చాలా మర్యాదగా మరియు త్వరగా సేవలందించారు.",
    },
    {
        "category": "service_staff",
        "sentiment": "neutral",
        "text": "సర్వీస్ సాధారణంగా ఉంది.",
    },
    {
        "category": "service_staff",
        "sentiment": "improvement",
        "text": "ఆర్డర్ తీసుకోవడానికి సిబ్బంది కొంచెం ఎక్కువ సమయం తీసుకున్నారు.",
    },
    {
        "category": "speed_of_service",
        "sentiment": "positive",
        "text": "ఆర్డర్ చేసిన కొద్ది నిమిషాల్లోనే భోజనం వచ్చింది.",
    },
    {
        "category": "speed_of_service",
        "sentiment": "improvement",
        "text": "ఆహారం రావడానికి చాలా సమయం వేచి ఉండాల్సి వచ్చింది.",
    },
    {
        "category": "restaurant_ambience",
        "sentiment": "positive",
        "text": "రెస్టారెంట్ వాతావరణం, లైటింగ్ మరియు కూర్చునే ప్రదేశం చాలా బాగుంది.",
    },
    {
        "category": "restaurant_ambience",
        "sentiment": "improvement",
        "text": "సంగీతం శబ్దం చాలా ఎక్కువగా ఉంది, సంభాషణ కష్టమైంది.",
    },
    {
        "category": "cleanliness_hygiene",
        "sentiment": "positive",
        "text": "టేబుల్స్, ప్లేట్లు మరియు రెస్టారెంట్ చాలా పరిశుభ్రంగా ఉన్నాయి.",
    },
    {
        "category": "cleanliness_hygiene",
        "sentiment": "improvement",
        "text": "టేబుల్ శుభ్రతను కొంచెం మెరుగుపరచాలి.",
    },
    {
        "category": "family_dining",
        "sentiment": "positive",
        "text": "కుటుంబంతో కలిసి భోజనం చేయడానికి చాలా మంచి ప్రదేశం.",
    },
    {
        "category": "value_for_money",
        "sentiment": "positive",
        "text": "ధరకు తగిన పరిమాణం మరియు అద్భుతమైన నాణ్యత.",
    },
    {
        "category": "value_for_money",
        "sentiment": "improvement",
        "text": "పరిమాణంతో పోలిస్తే ధర కొంచెం ఎక్కువగా అనిపించింది.",
    },
    {
        "category": "drinks_beverages",
        "sentiment": "positive",
        "text": "పానీయాలు చాలా రిఫ్రెషింగ్‌గా మరియు రుచిగా ఉన్నాయి.",
    },
    {
        "category": "overall_experience",
        "sentiment": "positive",
        "text": "మొత్తం అనుభవం చాలా అద్భుతంగా ఉంది, మళ్ళీ తప్పకుండా వస్తాము.",
    },
    {
        "category": "overall_experience",
        "sentiment": "neutral",
        "text": "సాధారణ సంతృప్తికరమైన అనుభవం.",
    },
    {
        "category": "overall_experience",
        "sentiment": "improvement",
        "text": "ఈసారి అనుభవం మేము ఆశించినంతగా లేదు.",
    },
]

HINDI_PROMPTS = [
    {
        "category": "food_quality",
        "sentiment": "positive",
        "text": "खाना बहुत ही स्वादिष्ट, गर्म और उच्च गुणवत्ता वाला था।",
    },
    {
        "category": "food_quality",
        "sentiment": "neutral",
        "text": "खाने का स्वाद सामान्य और ठीक-ठाक था।",
    },
    {
        "category": "food_quality",
        "sentiment": "improvement",
        "text": "खाने में मसाले और स्वाद को थोड़ा बेहतर किया जा सकता है।",
    },
    {
        "category": "taste_freshness",
        "sentiment": "positive",
        "text": "सब्जियां और सामग्री बिल्कुल ताज़ा और खुशबूदार थीं।",
    },
    {
        "category": "taste_freshness",
        "sentiment": "improvement",
        "text": "खाना पूरी तरह गर्म नहीं था, थोड़ा ठंडा परोसा गया।",
    },
    {
        "category": "service_staff",
        "sentiment": "positive",
        "text": "स्टाफ का व्यवहार बहुत ही विनम्र, मददगार और मिलनसार था।",
    },
    {
        "category": "service_staff",
        "sentiment": "neutral",
        "text": "सर्विस सामान्य थी, कोई खास बात नहीं।",
    },
    {
        "category": "service_staff",
        "sentiment": "improvement",
        "text": "स्टाफ का ध्यान थोड़ा कम था, बुलाने में समय लगा।",
    },
    {
        "category": "speed_of_service",
        "sentiment": "positive",
        "text": "ऑर्डर करने के तुरंत बाद खाना बिना इंतज़ार के आ गया।",
    },
    {
        "category": "speed_of_service",
        "sentiment": "improvement",
        "text": "खाना टेबल पर आने में उम्मीद से ज्यादा समय लगा।",
    },
    {
        "category": "restaurant_ambience",
        "sentiment": "positive",
        "text": "रेस्टोरेंट का माहौल, सजावट और बैठक व्यवस्था बहुत ही सुखद थी।",
    },
    {
        "category": "restaurant_ambience",
        "sentiment": "improvement",
        "text": "म्यूजिक की आवाज़ काफी तेज़ थी जिससे बातचीत में परेशानी हुई।",
    },
    {
        "category": "cleanliness_hygiene",
        "sentiment": "positive",
        "text": "रेस्टोरेंट, टेबल और बर्तन बिल्कुल साफ और स्वच्छ थे।",
    },
    {
        "category": "cleanliness_hygiene",
        "sentiment": "improvement",
        "text": "टेबल की सफाई पर थोड़ा और ध्यान देने की आवश्यकता है।",
    },
    {
        "category": "family_dining",
        "sentiment": "positive",
        "text": "परिवार के साथ शानदार समय बिताने के लिए बेहतरीन जगह है।",
    },
    {
        "category": "value_for_money",
        "sentiment": "positive",
        "text": "क्वालिटी और मात्रा के हिसाब से कीमतें बहुत ही वाजिब हैं।",
    },
    {
        "category": "value_for_money",
        "sentiment": "improvement",
        "text": "पोर्शन साइज के मुकाबले कीमतें थोड़ी ज्यादा लगीं।",
    },
    {
        "category": "drinks_beverages",
        "sentiment": "positive",
        "text": "ड्रिंक्स और पेय पदार्थ बहुत ही ताज़ा और स्वादिष्ट थे।",
    },
    {
        "category": "overall_experience",
        "sentiment": "positive",
        "text": "कुल मिलाकर बहुत ही सुखद अनुभव रहा, हम दोबारा ज़रूर आएंगे।",
    },
    {
        "category": "overall_experience",
        "sentiment": "neutral",
        "text": "साधारण और संतोषजनक अनुभव रहा।",
    },
    {
        "category": "overall_experience",
        "sentiment": "improvement",
        "text": "आज का अनुभव हमारी उम्मीदों से थोड़ा कम रहा।",
    },
]


def generate_library():
    prompts: List[Dict] = []
    seen_ids = set()
    seen_texts_per_lang: Dict[str, set] = {"en": set(), "te": set(), "hi": set()}

    cat_name_map = dict(CATEGORIES)

    # 1. Assemble English Prompts
    eng_counter = 1
    for cat_key, sentiments in ENGLISH_PROMPTS.items():
        for sent_key, text_list in sentiments.items():
            for text in text_list:
                prompt_id = f"p_en_{cat_key[:3]}_{eng_counter:03d}"
                eng_counter += 1

                assert prompt_id not in seen_ids, f"Duplicate ID: {prompt_id}"
                assert text not in seen_texts_per_lang["en"], f"Duplicate text in EN: {text}"

                seen_ids.add(prompt_id)
                seen_texts_per_lang["en"].add(text)

                prompts.append({
                    "id": prompt_id,
                    "category": cat_key,
                    "category_name": cat_name_map[cat_key],
                    "text": text,
                    "language": "en",
                    "sentiment": sent_key,
                    "is_active": True,
                })

    # 2. Assemble Telugu Prompts
    te_counter = 1
    for item in TELUGU_PROMPTS:
        cat_key = item["category"]
        prompt_id = f"p_te_{cat_key[:3]}_{te_counter:03d}"
        te_counter += 1

        assert prompt_id not in seen_ids, f"Duplicate ID: {prompt_id}"
        assert item["text"] not in seen_texts_per_lang["te"], f"Duplicate text in TE: {item['text']}"

        seen_ids.add(prompt_id)
        seen_texts_per_lang["te"].add(item["text"])

        prompts.append({
            "id": prompt_id,
            "category": cat_key,
            "category_name": cat_name_map[cat_key],
            "text": item["text"],
            "language": "te",
            "sentiment": item["sentiment"],
            "is_active": True,
        })

    # 3. Assemble Hindi Prompts
    hi_counter = 1
    for item in HINDI_PROMPTS:
        cat_key = item["category"]
        prompt_id = f"p_hi_{cat_key[:3]}_{hi_counter:03d}"
        hi_counter += 1

        assert prompt_id not in seen_ids, f"Duplicate ID: {prompt_id}"
        assert item["text"] not in seen_texts_per_lang["hi"], f"Duplicate text in HI: {item['text']}"

        seen_ids.add(prompt_id)
        seen_texts_per_lang["hi"].add(item["text"])

        prompts.append({
            "id": prompt_id,
            "category": cat_key,
            "category_name": cat_name_map[cat_key],
            "text": item["text"],
            "language": "hi",
            "sentiment": item["sentiment"],
            "is_active": True,
        })

    # Write out to backend/app/data/feedback_prompts.json
    out_path = Path("backend/app/data/feedback_prompts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(prompts)} prompts in {out_path}.")
    print(f"- English: {len(seen_texts_per_lang['en'])}")
    print(f"- Telugu: {len(seen_texts_per_lang['te'])}")
    print(f"- Hindi: {len(seen_texts_per_lang['hi'])}")

    # Category breakdown
    cat_counts = {}
    for p in prompts:
        cat = p["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    for cat, count in sorted(cat_counts.items()):
        print(f"  * {cat}: {count} prompts")


if __name__ == "__main__":
    generate_library()

