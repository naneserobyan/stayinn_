import os, json, random, hashlib
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from datetime import datetime, date, timedelta
from flask import Flask, abort, render_template, request, redirect, url_for, flash, session, jsonify
from booking_system import BookingSystem, PropertyNotFoundError, NotAvailableError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stayinn-demo-secret-key'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
booking_system = BookingSystem(os.path.join(BASE_DIR, 'data.json'))
SITE_NAME = 'stayinn.com'
AMD_RATE = 390
# Display currencies. All internal filtering/booking prices remain AMD.
CURRENCY_RATES = {'AMD': 1.0, 'RUB': 0.215, 'USD': 0.00256}
CURRENCY_SYMBOLS = {'AMD': 'AMD', 'RUB': 'RUB', 'USD': 'USD'}
LANGS = {'RU': 'Русский',  'EN': 'English'}
TRANSLATIONS = {
    'RU': {
        'home':'Главная','all_properties':'Все объекты','my_bookings':'Мои бронирования','logout':'Выйти','where': 'Куда',
        'register':'Зарегистрироваться','login_account':'Войти в аккаунт','login':'Войти','create_account':'Создать аккаунт',
        'price_night':'Цена за ночь','stars':'Звёзды','rating':'Оценка','amenities':'Удобства','sorting':'Сортировка',
        'accommodation_type':'Тип размещения','hotels':'Отели','apartments':'Апартаменты/квартиры','guesthouses':'Гостевые дома','villas':'Виллы',
        'any':'Любая','excellent':'Превосходно','breakfast':'Завтрак','parking':'Парковка','central':'В центре',
        'default':'По умолчанию','cheaper':'Сначала дешевле','expensive':'Сначала дороже','by_rating':'По оценке',
        'apply':'Применить','found':'Найдено','open_map':'Открыть большую карту →','nothing':'Ничего не найдено.',
        'about':'Об этом жилье','guest_reviews':'Отзывы гостей','availability':'Наличие мест','checkin':'Заезд','checkout':'Отъезд','city_or_property': 'Город или объект',
        'guests': 'Гости','search': 'Поиск','show_on_map': 'Показать на карте','adults': 'Взрослые','children': 'Дети','change_search_params': 'Изменить параметры поиска',
        'from':'С','until':'До','child_beds':'Кровати для детей','children_rules':'Правила размещения детей',
        'special_requests':'Условия размещения','special_requests_text':'принимает особые пожелания — добавьте их на следующем шаге',
        'cash_only':'Только наличные','cash_text':'Этот объект размещения принимает только наличные.',
        'pets':'Домашние животные','no_pets':'Размещение с домашними животными не допускается.',
        'any_age':'Разрешается проживание детей любого возраста.',
        'children_fee':'В этом объекте размещения за детей в возрасте 3 лет и старше будет взиматься оплата как за взрослых гостей.',
        'children_search':'Чтобы увидеть точные цены и информацию о наличии мест, при поиске укажите количество детей в вашей группе',
        'show_more':'Ещё','collapse':'Свернуть','reserve':'Я бронирую','nothing_pay':'Вы пока ничего не платите',
        'included':'Включая налоги и сборы','Кондиционер': 'Кондиционер','Семейные номера': 'Семейные номера','Номера для некурящих': 'Номера для некурящих','Завтрак включён': 'Завтрак включён',
        'Бесплатная парковка': 'Бесплатная парковка'
    },
    
    'EN': {
        'home':'Home','all_properties':'All Properties','my_bookings':'My Bookings','logout':'Log out','where': 'Where',
        'register':'Register','login_account':'Log in to account','login':'Log in','create_account':'Create account',
        'price_night':'Price per night','stars':'Stars','rating':'Rating','amenities':'Amenities','sorting':'Sorting',
        'accommodation_type':'Accommodation type','hotels':'Hotels','apartments':'Apartments','guesthouses':'Guesthouses','villas':'Villas',
        'any':'Any','excellent':'Excellent','breakfast':'Breakfast','parking':'Parking','central':'Central',
        'default':'Default','cheaper':'Cheaper first','expensive':'More expensive first','by_rating':'By rating',
        'apply':'Apply','found':'Found','open_map':'Open large map →','nothing':'Nothing found.',
        'about':'About this property','guest_reviews':'Guest reviews','availability':'Availability','checkin':'Check-in','checkout':'Check-out',
        'city_or_property': 'City or property','guests': 'Guests','search': 'Search','show_on_map': 'Show on map','adults': 'Adults','children': 'Children','change_search_params': 'Change search parameters',
        'from':'From','until':'Until','child_beds':'Child beds','children_rules':'Children rules',
        'special_requests':'Special requests','special_requests_text':'accepts special requests — add them on the next step',
        'cash_only':'Cash only','cash_text':'This property only accepts cash payments.',
        'pets':'Pets','no_pets':'Pets are not allowed.',
        'any_age':'Children of any age are welcome.',
        'children_fee':'Children aged 3 years and older will be charged as adults at this property.',
        'children_search':'To see exact prices and occupancy information, please add the number of children in your group to your search',
        'show_more':'Show more','collapse':'Collapse','reserve':'I’ll reserve','nothing_pay':'You won’t pay anything yet',
        'included':'Includes taxes and charges',
        'Кондиционер': 'Air conditioning',
        'Семейные номера': 'Family rooms',
        'Номера для некурящих': 'Non-smoking rooms',
        'Завтрак включён': 'Breakfast included',
        'Бесплатная парковка': 'Free parking',
        'В центре города': 'Central',
        'В центре': 'Central'
    }
}

ACCOM_TYPES = {'hotel':'hotels','apartment':'apartments','guesthouse':'guesthouses','villa':'villas'}
ACCOM_BY_ID = {
    '10c0c44d':'apartment','85d50462':'apartment','300b7e21':'hotel','6302455d':'hotel',
    '3b12a501':'apartment','655467d3':'villa','72b4e256':'apartment','da3e99d9':'villa',
    '0f00f0b6':'apartment','6f2bc206':'guesthouse'
}

def load_json(name):
    with open(os.path.join(BASE_DIR, name), encoding='utf-8') as f: return json.load(f)
AMENITIES, PHOTOS, EXTRAS = load_json('amenities.json'), load_json('photos.json'), load_json('extras.json')
COUNTRY_RU={'Armenia':'Армения','Georgia':'Грузия','France':'Франция','Italy':'Италия','Spain':'Испания'}
CITY_ALIASES={
 'Ереван':['ереван','yerevan','armenia','армения','հայաստան'], 'Тбилиси':['тбилиси','tbilisi','georgia','грузия'],
 'Батуми':['батуми','batumi','georgia','грузия'], 'Париж':['париж','paris','france','франция'],
 'Прованс':['прованс','provence','france','франция'], 'Рим':['рим','rome','italy','италия'],
 'Амальфи':['амальфи','amalfi','italy','италия'], 'Барселона':['барселона','barcelona','spain','испания'],
 'Андалусия':['андалусия','andalusia','spain','испания']}
REVIEWERS=[('Евгения','Россия'),('Тамара','Армения'),('Анна','Россия'),('Давид','Армения'),('Marie','Франция'),('Giorgi','Грузия'),('Elena','Украина'),('Luca','Италия'),('Sophie','Германия'),('Arman','Армения'),('Nino','Грузия'),('Carlos','Испания'),('Tatyana','Россия'),('Ирина','Беларусь'),('Vahagn','Армения'),('Katarina','Польша')]
REVIEW_POS=[
    'Локация прекрасная, хозяин отзывчивый и во всём старался помочь. Квартира полностью соответствует фотографиям, чисто и уютно — вернёмся ещё раз, если будем в этом городе.',
    'Очень удобное расположение и комфортное жильё с продуманной планировкой. Хозяин встретил нас лично, показал всё вокруг и посоветовал, где вкусно поесть.',
    'Заселение прошло быстро, без задержек. Кровать удобная, в комнате тихо даже несмотря на то, что рядом центр города. Отдельное спасибо за бесплатный трансфер.',
    'Место превзошло ожидания: просторно, светло, всё необходимое для готовки есть на кухне. Wi-Fi стабильный, работали удалённо без проблем всю неделю.',
    'Приятно удивило соотношение цены и качества — за эти деньги ожидали меньшего. Постельное бельё свежее, полотенца тоже, в ванной был весь набор косметики.',
    'Хозяева очень гостеприимные, всегда были на связи и быстро отвечали на вопросы. Вид из окна оказался даже лучше, чем на фотографиях в объявлении.',
    'Останавливались с ребёнком — хозяин заранее подготовил детскую кроватку и рассказал про ближайшую детскую площадку. Очень внимательное отношение.',
    'Жильё в отличном состоянии, ремонт свежий, никаких посторонних запахов. Из минусов — не хватило вешалок в шкафу, но в остальном всё отлично.',
    'Идеально для короткой деловой поездки: рядом метро, кафе и коворкинг. Заселение через смарт-замок прошло без единой задержки.',
    'Тихий двор, парковка нашлась без проблем даже поздним вечером. Кондиционер работал отлично, несмотря на жару на улице.',
]
REVIEW_NEG=[
    '', '',
    'Немного шумно вечером с улицы — стоит взять беруши, если чутко спите.',
    'Хотелось бы больше розеток рядом с кроватью, пришлось пользоваться удлинителем.',
    'Парковку пришлось искать самостоятельно в соседних дворах, свободных мест у дома не было.',
    'Лестница в подъезде довольно крутая, с тяжёлыми чемоданами подниматься неудобно.',
    'Горячая вода шла с небольшой задержкой по утрам, минут пять приходилось подождать.',
    '', '',
    'Wi-Fi иногда пропадал вечером, но быстро восстанавливался сам.',
]
MONTHS=['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']

def to_amd(v): return round(float(v)*AMD_RATE) if v is not None else None

def current_lang():
    return request.args.get('lang') if request.args.get('lang') in LANGS else session.get('lang','RU')

def current_currency():
    c=request.args.get('currency')
    if c not in CURRENCY_RATES: c=session.get('currency','AMD')
    return c

def money(v_amd):
    c=current_currency()
    value=float(v_amd)*CURRENCY_RATES[c]
    return f'{value:,.0f}'.replace(',',' '), c

def tr(key):
    return TRANSLATIONS.get(current_lang(), TRANSLATIONS['RU']).get(key, key)

CUSTOM_DESCRIPTIONS = {
    'Old Tbilisi House': {
        'RU': [
            'Отель Old Tbilisi House расположен в самом сердце исторического центра Тбилиси, в окружении знаменитых серных бань и колоритных улочек. К услугам гостей терраса для отдыха с видом на город, бесплатный Wi-Fi и уютные номера с элементами национального декора.',
            'Прогулка до площади Свободы и крепости Нарикала занимает около 10–12 минут.',
            'Номера оснащены телевизором с плоским экраном и кондиционером. В собственной ванной комнате есть бесплатные туалетно-косметические принадлежности и фен.',
            'Для гостей сервируется традиционный завтрак, а на круглосуточной стойке регистрации помогут организовать экскурсии по городу.'
        ],
        'EN': [
            'Old Tbilisi House is located in the heart of Tbilisi’s historic center, surrounded by famous sulfur baths and colorful streets. Guests enjoy a relaxing terrace with city views, free Wi-Fi, and cozy rooms with traditional decorative elements.',
            'A 10–12 minute walk leads to Freedom Square and Narikala Fortress.',
            'Rooms are equipped with a flat-screen TV and air conditioning. The private bathroom includes complimentary toiletries and a hairdryer.',
            'A traditional breakfast is served daily, and the 24-hour front desk can help organize city tours.'
        ]
    },
    'Riverside Studio': {
        'RU': [
            'Апартаменты Riverside Studio расположены в живописном районе Еревана, вблизи реки Раздан. К услугам гостей бесплатный Wi-Fi, кондиционер и современные апартаменты с собственной кухней.',
            'До центральной площади Республики и главных достопримечательностей можно дойти пешком примерно за 15 минут.',
            'Студия оснащена телевизором с плоским экраном, стиральной машиной и удобной мебелью. В ванной комнате подготовлены свежие полотенца и фен.',
            'На территории работает уютное кафе, где по утрам сервируют свежий завтрак.'
        ],
        'EN': [
            'Riverside Studio apartments are located in a picturesque area of Yerevan, near the Hrazdan River. Guests are offered free Wi-Fi, air conditioning, and modern self-catering accommodation.',
            'The central Republic Square and main attractions can be reached on foot in about 15 minutes.',
            'The studio is equipped with a flat-screen TV, washing machine, and comfortable furniture. Fresh towels and a hairdryer are provided in the bathroom.',
            'A cozy café on-site serves fresh breakfast every morning.'
        ]
    },
    'Republic Square Loft': {
        'RU': [
            'Отель Republic Square Loft расположен в самом центре Еревана, всего в нескольких шагах от площади Республики и Поющих фонтанов. К услугам гостей стильные лофт-номера с кондиционером и бесплатным Wi-Fi.',
            'Станция метро находится в 2 минутах ходьбы, что позволяет легко добраться до любой точки города.',
            'Номера укомплектованы телевизором со спутниковыми каналами, сейфом и современной ванной комнатой с феном и тапочками.',
            'Каждое утро для гостей сервируется сытный завтрак «шведский стол».'
        ],
        'EN': [
            'Republic Square Loft is situated in the very center of Yerevan, just a few steps from Republic Square and the Singing Fountains. Guests can enjoy stylish loft rooms with air conditioning and free Wi-Fi.',
            'The metro station is a 2-minute walk away, providing easy access to any part of the city.',
            'Rooms are equipped with satellite TV, a safe, and a modern bathroom with a hairdryer and slippers.',
            'A hearty buffet breakfast is served for guests every morning.'
        ]
    },
    'Batumi Seaview Room': {
        'RU': [
            'Отель Batumi Seaview Room расположен в Батуми, на первой линии у Черного моря и знаменитого Батумского бульвара. Из окон открывается прекрасный вид на морское побережье, а к услугам гостей бесплатный Wi-Fi и кондиционер.',
            'Пляж и популярные прибрежные кафе находятся всего в 2 минутах ходьбы от объекта.',
            'Номера оснащены телевизором с плоским экраном, холодильником и ванной комнатой со всеми необходимыми туалетными принадлежностями.',
            'По утрам сервируется завтрак, а приветливый персонал круглосуточной стойки регистрации готов помочь 24/7.'
        ],
        'EN': [
            'Batumi Seaview Room is located in Batumi, right on the front line of the Black Sea and the famous Batumi Boulevard. Rooms offer stunning sea views, free Wi-Fi, and air conditioning.',
            'The beach and popular seaside cafés are just a 2-minute walk away.',
            'Rooms feature a flat-screen TV, a refrigerator, and a bathroom with all necessary toiletries.',
            'Breakfast is served in the mornings, and the friendly 24/7 front desk staff is always ready to help.'
        ]
    },
    'Le Marais Apartment': {
        'RU': [
            'Апартаменты Le Marais Apartment расположены в историческом и модном районе Парижа — Марэ. К услугам гостей элегантные апартаменты с паркетными полами, бесплатным Wi-Fi и кондиционером.',
            'Станция метро находится всего в 150 метрах, обеспечивая быстрый доступ к Лувру и Собору Парижской Богоматери.',
            'Номера оснащены телевизором, кофеваркой и современной ванной комнатой с бесплатными туалетно-косметическими принадлежностями.',
            'Для гостей сервируют традиционный французский завтрак, а стойка регистрации работает круглосуточно.'
        ],
        'EN': [
            'Le Marais Apartment is located in Paris’s historic and trendy Le Marais district. Guests are offered elegant apartments with parquet floors, free Wi-Fi, and air conditioning.',
            'The metro station is just 150 meters away, providing quick access to the Louvre and Notre-Dame Cathedral.',
            'Rooms are equipped with a TV, a coffee machine, and a modern bathroom with complimentary toiletries.',
            'A traditional French breakfast is served, and the front desk operates 24 hours a day.'
        ]
    },
    'Provence Countryside Cottage': {
        'RU': [
            'Загородный дом Provence Countryside Cottage расположен в живописном регионе Прованс, в окружении зелени и спокойной природы. К услугам гостей уютный интерьер, бесплатный Wi-Fi и кондиционер.',
            'Объект находится в тихом районе, идеальном для пеших прогулок и отдыха от городской суеты, при этом до центральной части можно доехать за несколько минут.',
            'Номера оснащены телевизором с плоским экраном, удобной мебелью и собственной ванной комнатой с феном.',
            'По утрам сервируется домашний завтрак, а на территории обустроена приятная зона отдыха.'
        ],
        'EN': [
            'Provence Countryside Cottage is situated in the scenic Provence region, surrounded by greenery and peaceful nature. Guests enjoy a cozy interior, free Wi-Fi, and air conditioning.',
            'The property is located in a quiet area ideal for hiking and escaping the city hustle, while the center is just a few minutes away by car.',
            'Rooms feature a flat-screen TV, comfortable furniture, and a private bathroom with a hairdryer.',
            'A homemade breakfast is served every morning, and a pleasant relaxation area is available on-site.'
        ]
    },
    'Trastevere Studio': {
        'RU': [
            'Апартаменты Trastevere Studio находятся в самом колоритном районе Рима — Трастевере, известном своими уютными улочками и традиционными заведениями. К услугам гостей бесплатный Wi-Fi, кондиционер и стильная обстановка.',
            'Прогулка до реки Тибр и исторического центра занимает около 5 минут.',
            'Студия укомплектована телевизором с плоским экраном, мини-кухней и ванной комнатой с феном и полотенцами.',
            'Каждое утро во внутреннем дворике сервируется итальянский завтрак.'
        ],
        'EN': [
            'Trastevere Studio is located in Rome’s most vibrant neighborhood, Trastevere, famous for its cozy streets and traditional venues. Guests are offered free Wi-Fi, air conditioning, and a stylish setting.',
            'A walk to the Tiber River and the historic center takes about 5 minutes.',
            'The studio is equipped with a flat-screen TV, a kitchenette, and a bathroom with a hairdryer and towels.',
            'An Italian breakfast is served every morning in the inner courtyard.'
        ]
    },
    'Amalfi Coast Villa': {
        'RU': [
            'Вилла Amalfi Coast Villa расположена на скалистом побережье Амальфи, откуда открывается потрясающий панорамный вид на Тирренское море. К услугам гостей терраса для загара, бесплатный Wi-Fi и кондиционер.',
            'До пляжа и центра города можно спуститься пешком примерно за 10 минут по живописным аллеям.',
            'Номера оснащены телевизором со спутниковыми каналами, сейфом и ванной комнатой с комплектом туалетных принадлежностей.',
            'По утрам сервируется завтрак с видом на морские просторы.'
        ],
        'EN': [
            'Amalfi Coast Villa is perched on the rocky Amalfi coast, offering stunning panoramic views of the Tyrrhenian Sea. Guests enjoy a sun terrace, free Wi-Fi, and air conditioning.',
            'The beach and city center can be reached on foot in about 10 minutes via scenic pathways.',
            'Rooms feature satellite TV, a safe, and a bathroom with a set of toiletries.',
            'Breakfast is served each morning with views of the open sea.'
        ]
    },
    'Gothic Quarter Loft': {
        'RU': [
            'Отель Gothic Quarter Loft расположен в историческом Готическом квартале Барселоны, в окружении старинной архитектуры. Всего 300 метров до знаменитой улицы Лас-Рамблас. К услугам гостей бесплатный Wi-Fi и кондиционер.',
            'Станция метро находится в 2 минутах ходьбы от отеля.',
            'Номера оформлены в современном стиле, оснащены телевизором и ванной комнатой с тропическим душем.',
            'Для гостей сервируется завтрак «шведский стол», а стойка регистрации открыта круглосуточно.'
        ],
        'EN': [
            'Gothic Quarter Loft is located in Barcelona’s historic Gothic Quarter, surrounded by ancient architecture and just 300 meters from the famous Las Ramblas. Guests enjoy free Wi-Fi and air conditioning.',
            'The metro station is a 2-minute walk from the hotel.',
            'Rooms are decorated in a modern style and feature a TV and a bathroom with a rain shower.',
            'A buffet breakfast is served for guests, and the front desk is open 24 hours a day.'
        ]
    },
    'Andalusian Guesthouse': {
        'RU': [
            'Гостевой дом Andalusian Guesthouse расположен в живописном регионе Андалусия, в окружении традиционных садов. К услугам гостей открытый бассейн, терраса для отдыха, бесплатный Wi-Fi и кондиционер.',
            'Поездка до центра города занимает около 10 минут.',
            'Номера оформлены в андалузском стиле, оснащены телевизором, удобной мебелью и отдельной ванной комнатой.',
            'Каждое утро гостям подают традиционный завтрак с местными деликатесами.'
        ],
        'EN': [
            'Andalusian Guesthouse is set in the scenic Andalusia region, surrounded by traditional gardens. Guests are offered an outdoor swimming pool, a relaxation terrace, free Wi-Fi, and air conditioning.',
            'A drive to the city center takes about 10 minutes.',
            'Rooms are decorated in an Andalusian style and equipped with a TV, comfortable furniture, and a private bathroom.',
            'Every morning, guests are served a traditional breakfast featuring local delicacies.'
        ]
    }
}
def property_description(prop, meta):
    name = prop.name
    city = meta.get('city', '')
    lang = current_lang()
    
   
    if name in CUSTOM_DESCRIPTIONS:
        return CUSTOM_DESCRIPTIONS[name].get(lang, CUSTOM_DESCRIPTIONS[name]['EN'])
    
    
    if lang == 'RU':
        return [
            f'{name} расположен в городе {city}. К услугам гостей бесплатный Wi-Fi, кондиционер и всё необходимое для комфортного проживания.',
            'Основные достопримечательности и городские удобства находятся в удобной транспортной доступности.',
            'Все номера оснащены телевизором с плоским экраном, удобной мебелью и собственной ванной комнатой.',
            'Для гостей сервируется завтрак, а стойка регистрации работает круглосуточно.'
        ]
    
    return [
        f'{name} is located in {city}. Guests are offered free Wi-Fi, air conditioning, and everything needed for a comfortable stay.',
        'Main attractions and city amenities are within easy reach.',
        'All rooms are equipped with a flat-screen TV, comfortable furniture, and a private bathroom.',
        'Breakfast is served for guests, and the front desk operates 24/7.'
    ]

def rating_word(v):
    if current_lang() == 'RU':
        return 'Превосходно' if v >= 9 else ('Отлично' if v >= 8.5 else ('Очень хорошо' if v >= 8 else 'Хорошо'))
    return 'Exceptional' if v >= 9 else ('Excellent' if v >= 8.5 else ('Very Good' if v >= 8 else 'Good'))

def photos_for(pid):
    return PHOTOS.get(str(pid), [])

def reviews_for(pid, extra):
    count=int(extra.get('reviews',0)); rnd=random.Random(str(pid)); base=float(extra.get('rating',9)); items=[]
    pos_pool=REVIEW_POS[:]; rnd.shuffle(pos_pool)
    neg_pool=REVIEW_NEG[:]; rnd.shuffle(neg_pool)
    for i in range(count):
        author,country=REVIEWERS[rnd.randrange(len(REVIEWERS))]; score=min(10,max(1,round(base+rnd.uniform(-1.1,.7),1)))
        if rnd.random()<.12: score=rnd.randint(7,9)
        d=date.today()-timedelta(days=rnd.randint(2,720)); nights=rnd.choice([1,2,2,3,4,5,7])
        items.append({'id':i+1,'author':author,'country':country,'initial':author[0].upper(),'score':score,
            'title':'Великолепно' if score>=9 else ('Очень хорошо' if score>=8 else 'Хорошо, но есть нюансы'),
            'pos':pos_pool[i%len(pos_pool)],'neg':(neg_pool[i%len(neg_pool)] if score<9.5 else ''),
            'date':f'{d.day} {MONTHS[d.month-1]} {d.year}','stay':f'{nights} ночей','room':'Стандартный номер с видом' if rnd.random()<.65 else 'Улучшенный номер'})
    return items

def ui_meta(pid, prop):
    m=dict(AMENITIES.get(str(pid),{})); e=EXTRAS.get(str(pid),{})
    city=e.get('city',''); country=m.get('country','');
    m.update({'city':city,'country_ru':COUNTRY_RU.get(country,country),'lat':e.get('lat'),'lng':e.get('lng'),'stars':e.get('stars',3),
              'rating':float(e.get('rating',8.5)),'reviews':int(e.get('reviews',0)),'scores':e.get('scores',{}),
              'location':f'{city}, {COUNTRY_RU.get(country,country)}','description':m.get('description','')})
    m['rating_word']=rating_word(m['rating']); m['accommodation_type']=ACCOM_BY_ID.get(str(pid),'hotel'); m['accommodation_label']=ACCOM_TYPES[m['accommodation_type']]; m['amenity_labels']=['Кондиционер','Семейные номера','Номера для некурящих']
    if m.get('breakfast'): m['amenity_labels'].append('Завтрак включён')
    if m.get('parking'): m['amenity_labels'].append('Бесплатная парковка')
    if m.get('central'): m['amenity_labels'].append('В центре города')
    return m

def build_room(prop):
    m=ui_meta(prop.property_id,prop)
    return {'id':prop.property_id,'prop':prop,'meta':m,'photos':photos_for(prop.property_id),'price_amd':to_amd(prop.price_per_night)}

def all_rooms(): return [build_room(p) for p in booking_system.list_properties()]


ROOM_TYPE_TEMPLATES = [
    {'suffix': 'с 1 кроватью', 'category': 'rooms', 'beds': '1 двуспальная кровать',
     'size': 22, 'mult': 1.0, 'extra': [], 'left': None},
    {'suffix': 'с 2 отдельными кроватями', 'category': 'rooms', 'beds': '2 односпальные кровати',
     'size': 24, 'mult': 1.08, 'extra': ['Окна во внутренний дворик'], 'left': 2},
    {'suffix': 'Люкс с 2 спальнями', 'category': 'suites', 'beds': '5 односпальных кроватей, 3 двуспальные кровати',
     'size': 80, 'mult': 2.4, 'extra': ['Собственный люкс', 'Мини-кухня', 'Гостиная зона'], 'left': 2},
]
BASE_FACILITIES = ['Номер', 'Кондиционер', 'Собственная ванная комната', 'Телевизор с плоским экраном', 'Бесплатный Wi-Fi']
CHECKLIST = ['С видом', 'Бесплатные туалетно-косметические принадлежности', 'Душ', 'Туалет', 'Полотенца',
             'Постельное бельё', 'Письменный стол', 'Тапочки', 'Отопление', 'Фен',
             'Вентилятор', 'Электрический чайник', 'Услуга «звонок-будильник»', 'Шкаф или гардероб',
             'Вешалка для одежды', 'Туалетная бумага']


def room_types_for(room, adults, children, nights):
    prop = room['prop']
    variants = []
    for i, tpl in enumerate(ROOM_TYPE_TEMPLATES):
        price_per_night = round(prop.price_per_night * tpl['mult'], 2)
        total = to_amd(price_per_night * nights) if nights else None
        variants.append({
            'key': f"{prop.property_id}-{i}",
            'name': f"{'Двухместный номер' if tpl['category'] == 'rooms' else ''} {tpl['suffix']}".strip(),
            'category': tpl['category'],
            'beds': tpl['beds'],
            'size': tpl['size'],
            'facilities': BASE_FACILITIES + tpl['extra'],
            'checklist': CHECKLIST,
            'guests': adults + children,
            'price_per_night': price_per_night,
            'total_amd': total,
            'left': tpl['left'],
            'recommended': i == 0,
        })
    return variants




def find_prop(pid):
    for p in booking_system.list_properties():
        if str(p.property_id)==str(pid): return p
    abort(404)

def state():
    a=request.args.get('adults',1); c=request.args.get('children',0)
    try: a=max(1,int(a)); c=max(0,int(c))
    except ValueError: a,c=1,0
    return {'destination':request.args.get('destination','').strip(),'check_in':request.args.get('check_in',''),'check_out':request.args.get('check_out',''),'adults':a,'children':c,'infants':int(request.args.get('infants',0) or 0),'pets':int(request.args.get('pets',0) or 0)}

def parse_dates(s):
    try:
        ci=datetime.strptime(s.get('check_in',''),'%Y-%m-%d').date(); co=datetime.strptime(s.get('check_out',''),'%Y-%m-%d').date()
        if ci>=co: return None,None,'Дата выезда должна быть позже даты заезда.'
        return ci,co,None
    except (ValueError,TypeError): return None,None,None

def matches(r,q):
    if not q:return True
    q=q.lower(); city=r['meta']['city']; hay=' '.join([r['prop'].name,r['meta']['location'],r['meta']['country_ru'],city,r['meta']['description']]).lower()
    return q in hay or any(q in a or a in q for a in CITY_ALIASES.get(city,[]))

def map_point(r,ci=None,co=None):
    available=None
    if ci and co:
        try: available=booking_system.is_available(r['id'],ci,co)
        except (PropertyNotFoundError,ValueError): available=None
    return {'id':r['id'],'name':r['prop'].name,'lat':r['meta']['lat'],'lng':r['meta']['lng'],'price':r['price_amd'],'rating':r['meta']['rating'],
      'rating_word':r['meta']['rating_word'],'reviews':r['meta']['reviews'],'stars':r['meta']['stars'],
      'photo':r['photos'][0] if r['photos'] else '', 'location':r['meta']['location'],
      'available':available,'url':url_for('property_detail',property_id=r['id'])}

@app.template_filter('amd')
def amd(v): return f'{int(round(float(v))):,}'.replace(',',' ')

@app.context_processor
def globals_(): return {'SITE_NAME':SITE_NAME,'today':date.today().isoformat(),'user_email':session.get('user_email'),'lang':current_lang(),'currency':current_currency(),'currencies':CURRENCY_SYMBOLS,'langs':LANGS,'tr':tr}
@app.route('/preferences')
def preferences():
    lang=request.args.get('lang')
    currency=request.args.get('currency')
    if lang in LANGS: session['lang']=lang
    if currency in CURRENCY_RATES: session['currency']=currency
    target=request.args.get('next') or request.referrer or url_for('index')
    try:
        u=urlparse(target)
        q=[(k,v) for k,v in parse_qsl(u.query,keep_blank_values=True) if k not in ('lang','currency','next')]
        target=urlunparse((u.scheme,u.netloc,u.path,u.params,urlencode(q),u.fragment))
    except Exception:
        pass
    return redirect(target)

@app.route('/')
def index():
    rooms=all_rooms()
    sections=[('Ереван','Тихие студии и лофты',[r for r in rooms if r['meta']['city']=='Ереван']),('Тбилиси','Старый город и побережье',[r for r in rooms if r['meta']['city'] in ('Тбилиси','Батуми')]),('Европа','Париж, Рим, Барселона и не только',[r for r in rooms if r['meta']['country'] in ('France','Italy','Spain')])]
    return render_template('index.html',state=state(),sections=[x for x in sections if x[2]])

@app.route('/search')
def search():
    s=state(); ci,co,err=parse_dates(s); rooms=[r for r in all_rooms() if matches(r,s['destination'])]
    prices=[r['price_amd']*CURRENCY_RATES[current_currency()] for r in rooms] or [0]; floor,ceil=min(prices),max(prices)
    try: minp=float(request.args.get('min_price',floor)); maxp=float(request.args.get('max_price',ceil)); minr=float(request.args.get('min_rating',0))
    except ValueError: minp,maxp,minr=floor,ceil,0
    stars=[int(x) for x in request.args.getlist('stars') if x.isdigit()]
    types=[x for x in request.args.getlist('accommodation') if x in ACCOM_TYPES]
    wants={k:request.args.get(k)=='on' for k in ('breakfast','parking','central')}
    filtered=[r for r in rooms if minp<=r['price_amd']*CURRENCY_RATES[current_currency()]<=maxp and
              (not stars or r['meta']['stars'] in stars) and r['meta']['rating']>=minr and
              (not types or r['meta']['accommodation_type'] in types) and
              all(not v or r['meta'].get(k) for k,v in wants.items())]
    sort=request.args.get('sort_by');
    if sort=='price_asc': filtered.sort(key=lambda r:r['price_amd'])
    elif sort=='price_desc': filtered.sort(key=lambda r:r['price_amd'],reverse=True)
    elif sort=='rating': filtered.sort(key=lambda r:r['meta']['rating'],reverse=True)
    return render_template('search.html',state=s,rooms=filtered,map_points=[map_point(r,ci,co) for r in filtered],price_floor=floor,price_ceil=ceil,min_price=minp,max_price=maxp,min_rating=minr,stars_selected=stars,types_selected=types,want=wants,sort_by=sort or '',search_error=err)

@app.route('/map')
def map_view():
    focus_id = request.args.get('focus')
    s = state()
    ci, co, err = parse_dates(s)
    
    
    rooms = all_rooms()
    map_points = [map_point(r, ci, co) for r in rooms]
    
    return render_template('map.html', state=s, map_points=map_points, focus_id=focus_id)
@app.route('/property/<property_id>')
def property_detail(property_id):
    prop=find_prop(property_id); room=build_room(prop); s=state(); ci,co,err=parse_dates(s)
    nights=(co-ci).days if ci and co else 0
    total=to_amd(nights*prop.price_per_night) if nights else None
    available=booking_system.is_available(property_id,ci,co) if ci and co else None
    reviews=reviews_for(property_id,EXTRAS.get(str(property_id),{})); scores=room['meta']['scores']
    room_types=room_types_for(room,s['adults'],s['children'],nights)
    description_paragraphs=property_description(prop,room['meta'])
    return render_template('property_detail.html',room=room,state=s,reviews=reviews[:8],review_count=len(reviews),scores=scores,
        description_paragraphs=description_paragraphs,
        nearby=[map_point(r,ci,co) for r in all_rooms() if r['meta']['city']==room['meta']['city']],self_point=map_point(room,ci,co),
        search_error=err,ci=ci,co=co,nights=nights,total=total,available=available,room_types=room_types)

@app.route('/property/<property_id>/checkout',methods=['GET','POST'])
def checkout(property_id):
    prop=find_prop(property_id); room=build_room(prop); s=state(); ci,co,err=parse_dates(s)
    if not ci or not co:
        flash('Сначала выберите даты заезда и выезда.','error'); return redirect(url_for('property_detail',property_id=property_id,**s))
    nights=(co-ci).days
    variant_name=request.args.get('variant_name') or room['prop'].name
    try: variant_price=float(request.args.get('variant_price', room['prop'].price_per_night))
    except (TypeError,ValueError): variant_price=room['prop'].price_per_night
    total=to_amd(nights*variant_price)
    if request.method=='POST':
        first=(request.form.get('first_name') or '').strip(); last=(request.form.get('last_name') or '').strip()
        email=(request.form.get('email') or '').strip(); phone=(request.form.get('phone') or '').strip()
        guest=f'{first} {last}'.strip() or 'Гость'
        if not first or not last or not email:
            flash('Заполните имя, фамилию и email.','error')
        else:
            try:
                booking=booking_system.book(property_id,guest,ci,co)
                ref=hashlib.md5(f'{property_id}{guest}{ci}'.encode()).hexdigest()[:8].upper()
                session['last_booking']={'ref':ref,
                    'name':guest,'email':email,'phone':phone,'property':prop.name,'room_type':variant_name,'check_in':ci.isoformat(),
                    'check_out':co.isoformat(),'nights':booking.nights(),'total':total}
                add_booking_to_history(email,{'ref':ref,'property':prop.name,'room_type':variant_name,
                    'check_in':ci.isoformat(),'check_out':co.isoformat(),'total':total,
                    'created_at':datetime.now().strftime('%d.%m.%Y %H:%M')})
                return redirect(url_for('booking_confirmed'))
            except NotAvailableError:
                flash('На эти даты жильё уже забронировано.','error'); return redirect(url_for('property_detail',property_id=property_id,**s))
    return render_template('checkout.html',room=room,state=s,ci=ci,co=co,nights=nights,total=total,variant_name=variant_name)


@app.route('/api/reviews/<property_id>')
def api_reviews(property_id):
    find_prop(property_id); return jsonify(reviews_for(property_id,EXTRAS.get(str(property_id),{})))

@app.route('/booking/confirmed')
def booking_confirmed():
    b=session.get('last_booking');
    if not b:return redirect(url_for('index'))
    return render_template('booking_confirmed.html',b=b,state=state())



USERS_FILE=os.path.join(BASE_DIR,'users.json')

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE,encoding='utf-8') as f: return json.load(f)
    return {}

def save_users(d):
    with open(USERS_FILE,'w',encoding='utf-8') as f: json.dump(d,f,indent=2,ensure_ascii=False)

def add_booking_to_history(email,record):
    if not email: return
    users=load_users()
    entry=users.setdefault(email,{'name':'','bookings':[]})
    entry['bookings'].insert(0,record)
    save_users(users)


@app.route('/login',methods=['POST'])
def login():
    email=(request.form.get('email') or '').strip()
    session['user_email']=email
    users=load_users()
    users.setdefault(email,{'name':'','bookings':[]})
    save_users(users)
    flash('Вы вошли в аккаунт.','success'); return redirect(request.referrer or url_for('index'))

@app.route('/register',methods=['POST'])
def register():
    email=(request.form.get('email') or '').strip()
    name=(request.form.get('name') or '').strip()
    session['user_email']=email
    users=load_users()
    users.setdefault(email,{'name':name,'bookings':[]})
    if name: users[email]['name']=name
    save_users(users)
    flash('Аккаунт создан. Добро пожаловать!','success'); return redirect(request.referrer or url_for('index'))

@app.route('/logout')
def logout(): session.pop('user_email',None); return redirect(url_for('index'))

@app.route('/account')
def account():
    email=session.get('user_email')
    if not email:
        flash('Сначала войдите в аккаунт.','error'); return redirect(url_for('index'))
    users=load_users()
    profile=users.get(email,{'name':'','bookings':[]})
    return render_template('account.html',profile=profile,email=email,state=state())

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
