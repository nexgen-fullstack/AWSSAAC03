---
id: hybrid-network
module: Мережа
title: Офіс ↔ AWS — Site-to-Site VPN, Direct Connect, Client VPN і гібридний DNS
short: VPN і Direct Connect
emoji: 🏗️
domains: secure, resilient, performance, cost
svc: vpn, dx, clientvpn, r53resolver
---
> 🎬 **Історія Хмаринки.** Сайт переїхав в AWS, а склад — ні: складська програма й принтери етикеток лишаються в офісі у Львові. Але тепер склад має бачити нові замовлення з бази в AWS, а сайт — залишки товарів зі складської програми. Відкривати складську базу в інтернет? Ніколи. Потрібен **приватний захищений канал** між офісом і VPC. Швидкий і дешевий — сьогодні, стабільний і потужний — коли Хмаринка виросте. І ще дрібниця: сервери в AWS мають знати адресу `sklad.office.lan`, а комп'ютери в офісі — `db.internal.khmarynka`.

> 🖼️ **Образ.** **Site-to-Site VPN** — броньований автомобіль, що возить посилки звичайною громадською дорогою (інтернетом): швидко організувати і недорого, але на дорозі бувають затори. **Direct Connect** — власна приватна залізнична колія від твого складу до складу AWS: будувати тижнями, зате швидко, стабільно й без заторів. **Client VPN** — особиста захищена перепустка співробітника, щоб заходити в мережу з дому.

## Два способи з'єднати офіс з AWS

| | **Site-to-Site VPN** | **AWS Direct Connect** |
|---|---|---|
| Як іде трафік | Шифрованими тунелями IPsec **через інтернет** | **Приватним фізичним каналом** до мережі AWS |
| Скільки налаштовувати | **Хвилини** | **Тижні або місяці** (фізичне підключення) |
| Швидкість | До 1,25 Gbps на тунель (🆕 до 5 Gbps для великих тунелів на Transit Gateway) | 50 Mbps – 400 Gbps |
| Стабільність | Залежить від інтернету: затримка й швидкість «гуляють» | **Стабільна** затримка й пропускна здатність |
| Шифрування | **Так**, IPsec вбудований | **Ні** за замовчуванням → MACsec або VPN поверх DX |
| Ціна | Недорого: погодинно за з'єднання + трафік | Дорожче за порт, зате **дешевший вихідний трафік** на великих обсягах |
| Типова роль | Старт, невеликі обсяги, **резерв для DX** | Великі обсяги, критичні системи, передбачуваність |

## Site-to-Site VPN {#vpn}

Складові:

- **Customer Gateway (CGW)** — опис твого роутера чи файрвола в офісі (його публічна IP-адреса, тип маршрутизації).
- **Virtual Private Gateway (VGW)** — VPN-шлюз з боку AWS, прикріплений до **однієї VPC**. Або замість нього — **Transit Gateway**, якщо VPC багато.
- **VPN connection** — з'єднання між ними з **двома тунелями** IPsec, які закінчуються в **різних зонах доступності** AWS. Якщо один тунель впаде (обслуговування чи збій), трафік піде другим. Обидва тунелі треба налаштувати на офісному пристрої!
- **Маршрутизація:** статична (вписуєш діапазони вручну) або **динамічна через BGP** (роутери самі обмінюються маршрутами — рекомендовано). **Route propagation** автоматично додає маршрути до офісу в таблиці маршрутів VPC.

Корисні варіації:

- **VPN CloudHub** — кілька офісів підключено до одного VGW, і вони можуть спілкуватися **між собою** через AWS (модель «зірка»).
- **ECMP на Transit Gateway** — кілька VPN-тунелів з однаковою вартістю **сумують** пропускну здатність (наприклад, 4 тунелі × 1,25 Gbps).
- **Accelerated Site-to-Site VPN** — тунелі заходять у мережу AWS через найближчу edge-точку Global Accelerator: менше «гуляння» інтернету. Лише з Transit Gateway.

## AWS Direct Connect {#dx}

**Direct Connect (DX)** — виділене фізичне підключення твоєї мережі до AWS у спеціальній **DX-локації** (дата-центрі-партнері, де стоїть обладнання AWS). Від офісу до DX-локації канал прокладає твій провайдер.

- **Dedicated connection** — власний фізичний порт **1, 10, 100 або 400 Gbps**, замовляється в AWS.
- **Hosted connection** — через **партнера AWS**, від **50 Mbps до 25 Gbps**; часто швидше отримати і дешевше на старті.
- Від замовлення до роботи — **тижні або місяці**. Якщо даних треба перенести «вже завтра» — Direct Connect не встигне.

### Віртуальні інтерфейси (VIF)

Один фізичний канал ділиться на логічні інтерфейси:

| VIF | Куди веде | Для чого |
|---|---|---|
| **Private VIF** | До VPC (через VGW або Direct Connect Gateway) | Доступ до серверів і баз у VPC за приватними адресами |
| **Public VIF** | До **публічних** сервісів AWS (S3, DynamoDB тощо) у всіх регіонах | Великі обсяги в S3 без інтернету |
| **Transit VIF** | До **Transit Gateway** через Direct Connect Gateway | Багато VPC через один канал |

**Direct Connect Gateway** — глобальний об'єкт: **один** DX-канал до VPC (через VGW чи Transit Gateway) у **різних регіонах**. Наприклад, DX у Франкфурті дає доступ і до VPC в Ірландії.

### Шифрування і стійкість DX

Direct Connect — приватний канал, але **не зашифрований**. Якщо вимоги кажуть «encrypt in transit»:

- **MACsec** — шифрування на рівні каналу (для dedicated 10/100/400 Gbps);
- **IPsec VPN поверх Direct Connect** — зашифровані тунелі всередині приватного каналу.

Одне підключення — **єдина точка відмови**. Моделі стійкості від AWS:

<figure class="diagram" data-caption="Стійкість Direct Connect: від дешевого до максимального">
<div class="grid3">
<div class="gcard"><b>💲 DX + VPN резерв</b>Один DX-канал, а при збої — Site-to-Site VPN через інтернет<small>Найдешевший резерв; швидкість резерву нижча</small></div>
<div class="gcard"><b>💲💲 High resiliency</b>По одному каналу в <strong>двох різних DX-локаціях</strong><small>Переживає втрату цілої локації</small></div>
<div class="gcard hl"><b>💲💲💲 Maximum resiliency</b>Два канали на різних пристроях у <strong>кожній з двох DX-локацій</strong><small>Переживає і втрату локації, і збій пристрою — для критичних систем</small></div>
</div>
<figcaption>На іспиті: «максимальна стійкість гібридного з'єднання» → кілька DX у різних локаціях; «найдешевший резерв для DX» → Site-to-Site VPN.</figcaption>
</figure>

## Гібридна схема Хмаринки {#design}

<figure class="diagram" data-caption="Офіс Хмаринки ↔ AWS через VPN, згодом — Direct Connect">
<div class="flow">
<div class="st"><b>🏢 Офіс і склад (Львів)</b>Роутер (Customer Gateway), складська програма, DNS <code>office.lan</code>, мережа 192.168.1.0/24</div>
<span class="ar">⇄</span>
<div class="st lanes"><b>🔌 Канали</b><span class="dg-node net">Site-to-Site VPN: 2 тунелі IPsec</span><span class="dg-node net">Згодом: Direct Connect (hosted, 1 Gbps) + VPN як резерв</span></div>
<span class="ar">⇄</span>
<div class="st"><b>🚉 Transit Gateway</b>Хаб у мережевому акаунті; до нього — VPN, а згодом DX через Direct Connect Gateway</div>
<span class="ar">⇄</span>
<div class="st"><b>☁️ VPC shop-prod · shop-dev · analytics</b>Route 53 Resolver: inbound і outbound endpoints для DNS</div>
</div>
<figcaption>Діапазони не перетинаються: офіс 192.168.1.0/24, VPC 10.0.0.0/16, 10.1.0.0/16… — тому маршрутизація проста.</figcaption>
</figure>

## Client VPN: співробітники з дому {#client-vpn}

**AWS Client VPN** — керований VPN-сервіс для **окремих користувачів**: співробітник запускає VPN-клієнт на ноутбуці (протокол OpenVPN) і потрапляє в VPC (а через неї — і в офісну мережу, якщо налаштовано). Автентифікація — через **Active Directory**, **SAML** (наприклад, Entra ID, Okta) або сертифікати. Масштабується автоматично.

:::mnemo 🧠 Site-to-Site чи Client VPN?
**Site-to-Site** — мережа ↔ мережа (офіс ↔ VPC), налаштовується на роутері. **Client VPN** — людина ↔ мережа (ноутбук ↔ VPC). На іспиті «віддалені співробітники підключаються до VPC» → Client VPN.
:::

## Гібридний DNS: Route 53 Resolver endpoints {#dns}

Усередині VPC імена резолвить **Route 53 Resolver**. В офісі — свій DNS-сервер. Щоб вони розуміли одне одного:

- **Inbound endpoint** — «вхід» у DNS AWS для офісу: офісний DNS пересилає запити про `internal.khmarynka` на IP-адреси inbound endpoint у VPC, і офісні комп'ютери бачать приватні імена AWS.
- **Outbound endpoint + forwarding rules** — «вихід» з VPC: правило «запити про `office.lan` пересилай на офісний DNS 192.168.1.10» — і сервери в AWS знаходять `sklad.office.lan`.
- Правила можна поширити на інші VPC і акаунти через **AWS RAM**.

<figure class="diagram" data-caption="Гібридний DNS: запити в обидва боки">
<div class="grid2">
<div class="gcard"><b>🏢 → ☁️ Inbound endpoint</b>Офісний DNS: «про internal.khmarynka питай 10.0.0.53» → Resolver у VPC відповідає з private hosted zone<small>Офіс бачить імена AWS</small></div>
<div class="gcard"><b>☁️ → 🏢 Outbound endpoint</b>Правило Resolver: «office.lan → 192.168.1.10» → запит іде через VPN в офісний DNS<small>AWS бачить імена офісу</small></div>
</div>
<figcaption>Обидва endpoints — мережеві інтерфейси в підмережах VPC (краще у двох AZ); трафік іде приватним каналом VPN або DX.</figcaption>
</figure>

:::lab 🧪 Спробуй у справжньому AWS: подивись, як виглядає VPN-з'єднання
**Вартість:** VPN-з'єднання тарифікується погодинно — якщо видалити його за 15–20 хвилин, це кілька центів. Customer Gateway і Virtual Private Gateway самі по собі не тарифікуються. **Час:** 20 хвилин.
1. **VPC → Customer gateways → Create**: назва `office-lviv`, IP-адреса — будь-яка публічна для тесту (наприклад, `203.0.113.10` з документаційного діапазону), BGP ASN — залиш за замовчуванням.
2. **Virtual private gateways → Create** `vgw-khmarynka` → Actions → **Attach to VPC** (твоя VPC).
3. **Site-to-Site VPN connections → Create**: Target — Virtual private gateway, Customer gateway — `office-lviv`, Routing — **Static**, Static IP prefixes — `192.168.1.0/24`. Create.
4. Коли з'єднання створиться (кілька хвилин), відкрий вкладку **Tunnel details**: **два** тунелі з різними зовнішніми IP-адресами AWS. Статус Down — нормально, бо справжнього роутера немає.
5. **Download configuration** → Vendor: Generic → подивись файл: параметри IPsec для обох тунелів, які адміністратор вписав би в офісний роутер.
6. Відкрий таблицю маршрутів приватної підмережі → **Route propagation** → Edit → увімкни для VGW: маршрути до офісу з'являтимуться автоматично.
**Прибери за собою (обов'язково!):** видали **VPN connection** (зупиняє оплату), потім Detach і Delete VGW, потім Delete Customer gateway.
:::

#### 💡 Запам'ятай

- **Site-to-Site VPN:** IPsec через інтернет, **хвилини** на налаштування, **2 тунелі** в різних AZ, VGW (одна VPC) або Transit Gateway (багато VPC), до 1,25 Gbps на тунель; ECMP на TGW сумує тунелі.
- **Direct Connect:** приватний фізичний канал, **тижні-місяці**, dedicated 1/10/100/400 Gbps, hosted 50 Mbps–25 Gbps; стабільно і дешевший вихідний трафік; **не шифрується** сам → **MACsec** або **VPN поверх DX**.
- VIF: **private** (VPC), **public** (публічні сервіси AWS), **transit** (Transit Gateway). **Direct Connect Gateway** — один DX до VPC у різних регіонах.
- Стійкість: **DX + VPN** — дешевий резерв; **DX у двох локаціях** — висока/максимальна стійкість.
- **Client VPN** — окремі користувачі з ноутбуків; **CloudHub** — кілька офісів між собою через AWS.
- **Resolver inbound** — офіс резолвить імена AWS; **outbound + правила** — AWS резолвить імена офісу.

#### 🎯 Як питають на іспиті

- Швидко і недорого створити зашифрований канал до офісу → **Site-to-Site VPN**
- Стабільна пропускна здатність, приватний канал, великі щоденні обсяги → **AWS Direct Connect**
- Direct Connect + вимога шифрувати трафік → **IPsec VPN поверх DX** або **MACsec**
- Найдешевший резерв для Direct Connect → **Site-to-Site VPN як backup**
- Максимальна стійкість гібридного з'єднання для критичної системи → **кілька DX-з'єднань у різних DX-локаціях**
- Один Direct Connect має вести до VPC у кількох регіонах → **Direct Connect Gateway**
- Доступ до S3 через Direct Connect без інтернету → **public VIF** (або private VIF + interface endpoint для S3)
- Дані треба перенести через тиждень, а Direct Connect ще не проведено → **DX не встигне: VPN, DataSync або фізичний пристрій**
- Віддалені співробітники підключаються до ресурсів у VPC → **AWS Client VPN**
- Кілька філій мають спілкуватися між собою через AWS → **VPN CloudHub** (або Transit Gateway)
- Збільшити пропускну здатність VPN понад один тунель → **Transit Gateway з ECMP (кілька тунелів)**
- Сервери в AWS мають резолвити внутрішні імена офісу → **Route 53 Resolver outbound endpoint + forwarding rule**
- Офісні сервери мають резолвити приватні імена в AWS → **Route 53 Resolver inbound endpoint**

#### ⚠️ Пастки

- Direct Connect **не шифрує** трафік сам по собі.
- Direct Connect не підключається «за день» — у терміновій задачі він неправильна відповідь.
- Один DX-канал — єдина точка відмови; «високодоступний» DX = щонайменше два канали (або DX + VPN).
- Virtual Private Gateway прикріплюється до **однієї** VPC; для багатьох VPC — Transit Gateway чи Direct Connect Gateway.
- Client VPN ≠ Site-to-Site VPN: перший для людей, другий для мереж.

## ✅ Перевір себе

:::quiz
? Компанії потрібно за один день налаштувати зашифроване з'єднання між офісом і VPC для невеликих обсягів даних. Що обрати?
+ AWS Site-to-Site VPN
- AWS Direct Connect dedicated connection
- AWS Direct Connect hosted connection
- VPC peering з офісом
= Site-to-Site VPN налаштовується за хвилини і шифрує трафік IPsec. Direct Connect потребує тижнів на фізичне підключення і не шифрує сам. Peering з офісом неможливий — це з'єднання між VPC.

? Компанія використовує Direct Connect, і служба безпеки вимагає шифрувати весь трафік між офісом і VPC. Яке рішення правильне?
- Direct Connect шифрує трафік автоматично, нічого робити не треба
+ Налаштувати IPsec VPN поверх з'єднання Direct Connect (або MACsec на підтримуваному з'єднанні)
- Увімкнути шифрування EBS
- Замінити Direct Connect на VPC endpoint
= Direct Connect — приватний, але незашифрований канал. Шифрування in transit досягається VPN-тунелями IPsec поверх DX або MACsec на рівні каналу.

? Критичний застосунок залежить від Direct Connect. Потрібна максимальна стійкість до збоїв з'єднання і втрати цілої DX-локації. Що рекомендувати?
- Один Direct Connect з резервним Site-to-Site VPN
- Два Direct Connect-з'єднання в одній DX-локації
+ Кілька Direct Connect-з'єднань на окремих пристроях у двох різних DX-локаціях
- Один Direct Connect з більшою швидкістю порту
= Максимальна стійкість — з'єднання в кількох DX-локаціях на різних пристроях: переживає і збій пристрою, і втрату цілої локації. DX + VPN — дешевший резерв, але з меншою пропускною здатністю.

? Компанія має Direct Connect у Франкфурті й хоче через нього отримувати доступ до VPC у eu-central-1 та eu-west-1. Що використати?
- Два окремі фізичні з'єднання DX
+ Direct Connect Gateway
- VPC peering між регіонами
- Public VIF
= Direct Connect Gateway — глобальний ресурс, що з'єднує один DX-канал з VPC (через VGW або Transit Gateway) у різних регіонах.

? 150 співробітників працюють віддалено і мають безпечно підключатися до внутрішніх застосунків у VPC зі своїх ноутбуків, входячи корпоративним обліковим записом. Що обрати?
- Site-to-Site VPN з кожним ноутбуком
+ AWS Client VPN з автентифікацією через SAML або Active Directory
- Direct Connect hosted connection
- Публічні IP-адреси для внутрішніх застосунків
= Client VPN — керований VPN для окремих користувачів, з автентифікацією через AD, SAML чи сертифікати. Site-to-Site з'єднує мережі, а не окремі пристрої.

? Сервери в VPC мають звертатися до внутрішнього сервісу за іменем `erp.corp.local`, яке відоме лише офісному DNS-серверу. Що налаштувати?
- Route 53 Resolver inbound endpoint
+ Route 53 Resolver outbound endpoint і forwarding rule для corp.local на офісний DNS
- Public hosted zone corp.local у Route 53
- Запис у файлі hosts кожного сервера
= Outbound endpoint пересилає запити з VPC до зовнішніх DNS-серверів за правилами. Inbound endpoint потрібен для протилежного напрямку — коли офіс резолвить імена AWS.

? Компанія використовує Site-to-Site VPN на Transit Gateway, але одного тунелю (1,25 Gbps) не вистачає. Як збільшити пропускну здатність без Direct Connect?
- Збільшити розмір Virtual Private Gateway
+ Налаштувати кілька VPN-тунелів з ECMP на Transit Gateway
- Перейти на Client VPN
- Увімкнути VPC Flow Logs
= Transit Gateway підтримує ECMP (equal-cost multi-path) для VPN: кілька тунелів з однаковими маршрутами сумують пропускну здатність. Virtual Private Gateway цього не вміє.
:::
