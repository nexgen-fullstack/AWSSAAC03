---
id: route53
module: Мережа
title: Route 53 — DNS, який керує трафіком
short: Route 53
emoji: 🧭
domains: resilient, performance
svc: route53
---
> 🎬 **Історія Хмаринки.** Домен `khmarynka.ua` зареєстрований в українського реєстратора, а його DNS досі обслуговує старий хостинг, де запис змінюється «протягом доби». Тарас хоче більшого: щоб `khmarynka.ua` вказував на CloudFront, `api.khmarynka.ua` — на балансувальник, щоб при аварії сайт сам перемикався на сторінку «Технічні роботи», щоб нову версію бачили спершу 10% покупців, а поляки й німці потрапляли на свою мовну версію. Усе це — не код, а **DNS-правила** в Amazon Route 53.

> 🖼️ **Образ.** Звичайний DNS — довідкова служба, що на питання «де живе khmarynka.ua?» завжди дає одну й ту саму адресу. **Route 53** — розумний диспетчер таксі: зважає, звідки ти телефонуєш (країна, відстань, затримка), хто з водіїв зараз вільний і здоровий (health checks), і навіть розподіляє замовлення у пропорції «90% старим водіям, 10% новому».

## Що вміє Route 53

**Amazon Route 53** — керований DNS-сервіс AWS з гарантією доступності **100%** (SLA). Три функції:

1. **Реєстрація доменів** (багато доменних зон: .com, .net, .org, .de… — хоча не всі; `.ua`, наприклад, реєструють місцеві реєстратори).
2. **DNS-хостинг**: відповідає на запити про твій домен з сотень edge-локацій по світу.
3. **Health checks** і **політики маршрутизації**: відповідь залежить від здоров'я серверів, розташування користувача, ваг.

**Hosted zone** — контейнер записів одного домену:

- **Public hosted zone** — відповідає всьому інтернету.
- **Private hosted zone** — відповідає лише всередині прив'язаних **VPC** (наприклад, `internal.khmarynka` → адреси баз). Потребує увімкнених у VPC `enableDnsSupport` і `enableDnsHostnames`. Можна мати публічну і приватну зони з **однаковою** назвою — різні відповіді зсередини і ззовні (split-horizon).

Щоб Route 53 обслуговував домен, куплений в іншого реєстратора, створюєш hosted zone і вписуєш у реєстратора її чотири **NS-сервери** Route 53 (делегування).

## Записи й особливий Alias {#alias}

Типи записів ті самі, що в будь-якому DNS ([розділ 3](#ch/it-networks/dns)): A, AAAA, CNAME, MX, TXT, NS, CAA… Плюс «суперсила» Route 53 — **Alias record**:

| | **CNAME** | **Alias** (Route 53) |
|---|---|---|
| На що вказує | Будь-яке інше ім'я | **Ресурси AWS**: балансувальник ELB, CloudFront, **S3 website**, API Gateway, Global Accelerator, VPC endpoint, Elastic Beanstalk, інший запис у зоні |
| **Zone apex** (`khmarynka.ua` без www) | ❌ Заборонено стандартом DNS | ✅ Можна |
| Плата за запити | Платні | **Безкоштовні** запити до ресурсів AWS |
| Зміна IP ресурсу | Відповідь через ім'я | Route 53 відстежує сам |
| TTL | Задаєш ти | Береться з ресурсу |

Тому класичне питання «направити `example.com` (apex) на Application Load Balancer» має одну відповідь — **Alias record**. Alias **не може** вказувати на ім'я сервера EC2 — лише на перелічені ресурси.

## Вісім політик маршрутизації {#routing}

<figure class="diagram" data-caption="Політики маршрутизації Route 53">
<div class="grid2">
<div class="gcard"><b>1. Simple</b>Одна відповідь (можна кілька IP — клієнт обирає випадково). Без health checks.<small>Простий сайт на одному ресурсі</small></div>
<div class="gcard"><b>2. Weighted</b>Відповіді за вагами: 90 / 10.<small>A/B-тести, поступовий реліз, міграція трафіку</small></div>
<div class="gcard"><b>3. Latency-based</b>Регіон з найменшою затримкою для цього користувача.<small>Глобальний застосунок у кількох регіонах</small></div>
<div class="gcard"><b>4. Failover</b>Primary, а якщо health check провалено — secondary.<small>Active-passive DR, сторінка «технічні роботи»</small></div>
<div class="gcard"><b>5. Geolocation</b>За країною / континентом користувача (+ запис за замовчуванням).<small>Мовні версії, ліцензії, закони, заборони</small></div>
<div class="gcard"><b>6. Geoproximity</b>За відстанню до ресурсу, з <strong>bias</strong> — «розширити» чи «стиснути» зону ресурсу.<small>Змістити частку трафіку до одного регіону</small></div>
<div class="gcard"><b>7. Multivalue answer</b>До 8 <strong>здорових</strong> записів у відповіді.<small>Простий розподіл на боці клієнта з перевіркою здоров'я (не заміна балансувальника)</small></div>
<div class="gcard"><b>8. IP-based</b>За діапазоном IP клієнта (CIDR-колекції).<small>Трафік певного провайдера — на певний endpoint</small></div>
</div>
<figcaption>Політики можна комбінувати деревом: наприклад, latency між регіонами, а всередині кожного регіону — weighted між версіями.</figcaption>
</figure>

:::mnemo 🧠 Geolocation, Geoproximity чи Latency?
**Geolocation** — «**де ти живеш**» (країна за законом чи мовою): поляки — на польську версію, навіть якщо Ірландія ближча. **Geoproximity** — «**як далеко**» + ручка **bias**, щоб перекинути частку трафіку. **Latency** — «**куди швидше**» (виміряна затримка до регіонів). Питання про закони, ліцензії, мову → Geolocation. Про швидкість → Latency. Про «зсунути більше трафіку» → Geoproximity.
:::

## Health checks і аварійне перемикання {#health}

**Health check** Route 53 регулярно перевіряє endpoint з кількох точок світу (HTTP, HTTPS або TCP; можна шукати рядок у відповіді). Три типи:

- **Endpoint** — перевірка конкретної адреси чи імені.
- **Calculated** — комбінація інших перевірок («здоровий, якщо щонайменше 2 з 3»).
- **CloudWatch alarm** — стан аларму. Це спосіб перевіряти **приватні** ресурси: перевіряльники Route 53 працюють з інтернету й не бачать приватних підмереж, а аларм CloudWatch — бачить метрики будь-чого.

**Failover-маршрутизація Хмаринки:**

<figure class="diagram" data-caption="Failover: основний сайт і сторінка «Технічні роботи»">
<div class="flow">
<div class="st"><b>👤 Покупець</b>Питає DNS: де khmarynka.ua?</div>
<span class="ar">→</span>
<div class="st"><b>🧭 Route 53</b>Health check основного endpoint: здоровий?</div>
<span class="ar">→</span>
<div class="st lanes"><b>Відповідь</b><span class="dg-node net">✅ Так → PRIMARY: CloudFront → ALB у Франкфурті</span><span class="dg-node sto">❌ Ні → SECONDARY: статична сторінка на S3 (або регіон Ірландія)</span></div>
</div>
<figcaption>Час перемикання = час виявлення збою (інтервал перевірок × кількість невдач) + <b>TTL</b>, протягом якого клієнти ще пам'ятають стару відповідь. Для швидкого failover — малий TTL.</figcaption>
</figure>

Для Alias-записів є опція **Evaluate target health** — Route 53 сам враховує здоров'я цілі (наприклад, чи має балансувальник здорові сервери) без окремого health check.

**Active-active** — усі записи здорові й отримують трафік (weighted, latency, multivalue з health checks); збійний просто випадає. **Active-passive** — резерв отримує трафік лише при збої основного (failover).

:::deep 🔬 Глибше: чому DNS-перемикання не миттєве
Клієнти й резолвери кешують відповідь на час **TTL**. Якщо TTL = 300 секунд, частина користувачів ще до 5 хвилин ходитиме на «мертву» адресу. Деякі резолвери й застосунки ігнорують TTL і тримають відповідь довше. Тому для задач «перемикання між регіонами за секунди, незалежно від DNS-кешу» на іспиті правильна відповідь — **Global Accelerator** зі статичними anycast-IP ([розділ 18](#ch/edge)). А для складних сценаріїв аварійного відновлення з контрольованим перемиканням є **Route 53 Application Recovery Controller** — перевірки готовності резервного регіону і «рубильники» маршрутизації.
:::

## DNS Хмаринки {#design}

| Запис | Тип / політика | Ціль |
|---|---|---|
| `khmarynka.ua` | **Alias**, failover primary | CloudFront distribution |
| `khmarynka.ua` | Alias, failover secondary | S3 static website «Технічні роботи» |
| `www.khmarynka.ua` | CNAME (або Alias) | `khmarynka.ua` |
| `api.khmarynka.ua` | **Alias**, weighted 90 / 10 | ALB поточної версії / ALB нової версії |
| `shop.khmarynka.ua` | **Geolocation**: Польща / Німеччина / за замовчуванням | Мовні версії |
| `db.internal.khmarynka` | Private hosted zone, CNAME | Endpoint бази RDS |
| `khmarynka.ua` | MX, TXT | Пошта, підтвердження домену для сервісів |

:::lab 🧪 Спробуй у справжньому AWS: зона, записи й тестова відповідь
**Вартість:** hosted zone — $0,50 на місяць, але **якщо видалити її протягом 12 годин після створення, плати немає**. **Час:** 15 хвилин.
1. **Route 53 → Hosted zones → Create hosted zone**: ім'я — будь-яке, навіть не твоє (наприклад, `khmarynka-lab.com`), тип **Public**. Домен купувати не треба — просто не буде делегування з інтернету.
2. Подивись створені записи **NS** і **SOA**: чотири name servers — їх вписують у реєстратора при делегуванні.
3. **Create record**: `www`, тип A, значення `192.0.2.10`, routing **Simple**.
4. Створи два записи `api` з routing **Weighted**: перший — `192.0.2.21`, weight 90, Record ID `v1`; другий — `192.0.2.22`, weight 10, Record ID `v2`.
5. Відкрий запис `api` → **Test record** (або в CloudShell: `aws route53 test-dns-answer --hosted-zone-id <ID> --record-name api.khmarynka-lab.com --record-type A`). Повтори кілька разів — здебільшого відповідь v1, іноді v2.
6. Подумай: як зробити, щоб при падінні v2 трафік на нього припинився? (Відповідь: прив'язати health check до запису.)
**Прибери за собою:** видали створені записи (крім NS і SOA), потім **Delete hosted zone** — у межах 12 годин.
:::

#### 💡 Запам'ятай

- Route 53: реєстрація доменів, DNS з SLA 100%, health checks, політики маршрутизації.
- **Public** hosted zone — для інтернету; **private** — лише для прив'язаних VPC.
- **Alias** — на ресурси AWS (ELB, CloudFront, S3 website, API Gateway…), **працює на zone apex**, безкоштовні запити. **CNAME на apex не можна.** Alias на EC2 — не можна.
- Політики: **Simple, Weighted, Latency, Failover, Geolocation, Geoproximity (bias), Multivalue (до 8 здорових), IP-based**.
- Health checks: endpoint, calculated, **CloudWatch alarm** (для приватних ресурсів).
- Швидкість DNS-перемикання обмежена **TTL**.

#### 🎯 Як питають на іспиті

- Направити `example.com` (zone apex) на Application Load Balancer → **Route 53 Alias record**
- Перевести 10% трафіку на нову версію → **Weighted routing**
- Користувачі мають потрапляти в регіон з найменшою затримкою → **Latency-based routing**
- Active-passive DR між регіонами через DNS → **Failover routing + health checks**
- Показувати контент залежно від країни (мова, ліцензії, закон) → **Geolocation routing (+ default record)**
- Змістити більше трафіку до одного регіону → **Geoproximity routing з bias**
- Повертати кілька здорових IP-адрес для простого розподілу навантаження → **Multivalue answer routing**
- Health check для ресурсу в приватній підмережі → **CloudWatch alarm + Route 53 health check**
- Імена ресурсів мають резолвитися лише всередині VPC → **Private hosted zone**
- При збої основного сайту показувати статичну сторінку-заглушку → **Failover-запис на S3 static website**

#### ⚠️ Пастки

- CNAME не можна створити для кореневого домену — лише Alias.
- Route 53 health checks не бачать приватні IP напряму — потрібен CloudWatch alarm.
- Geolocation ≠ latency: Geolocation дивиться на країну, а не на швидкість.
- Multivalue answer — не балансувальник: він лише повертає кілька здорових адрес.
- Великий TTL сповільнює аварійне перемикання.

## ✅ Перевір себе

:::quiz
? Компанія хоче, щоб домен example.com (без www) вказував на Application Load Balancer. Який запис створити в Route 53?
- CNAME-запис example.com → DNS-ім'я ALB
+ Alias-запис A для example.com на ALB
- A-запис з IP-адресою ALB
- MX-запис на ALB
= CNAME заборонено на zone apex, а IP-адреси ALB змінюються. Alias-запис Route 53 працює на apex і сам відстежує адреси ALB.

? Команда випускає нову версію API і хоче спершу спрямувати на неї 5% користувачів, поступово збільшуючи частку. Яка політика маршрутизації підходить?
- Latency-based
- Failover
+ Weighted
- Geolocation
= Weighted routing розподіляє відповіді за вагами (95/5), і ваги можна змінювати поступово. Це класичний спосіб канаркових релізів і міграцій через DNS.

? Контент стримінгового сервісу ліцензований лише для Польщі. Користувачі з інших країн мають бачити іншу сторінку. Що використати?
+ Geolocation routing з записом для Польщі і записом за замовчуванням
- Latency-based routing
- Geoproximity routing з bias
- Multivalue answer routing
= Geolocation визначає країну користувача і повертає відповідний запис. Запис за замовчуванням обслуговує всіх, для кого немає окремого правила.

? Застосунок працює в регіонах eu-central-1 і us-east-1. Кожен користувач має потрапляти в регіон, де відповідь буде найшвидшою. Яка політика?
- Geolocation
+ Latency-based
- Simple
- Weighted 50/50
= Latency-based routing обирає регіон з найменшою виміряною затримкою для мережі користувача — саме «найшвидший», а не «найближчий за кордоном».

? Потрібно автоматично перемикати трафік на резервний регіон, коли основний перестає відповідати. База основного регіону — у приватній підмережі, її стан відображає аларм CloudWatch. Що налаштувати? (Оберіть 2)
+ Failover routing policy з primary і secondary записами
+ Health check Route 53, прив'язаний до аларму CloudWatch
- Health check Route 53 напряму на приватну IP бази
- Geolocation routing
- Weighted routing з вагою 0 для резерву
= Failover-політика перемикає на secondary при провалі health check. Перевіряльники Route 53 не бачать приватних адрес, тому health check будується на аларму CloudWatch.

? Сервери в VPC мають звертатися до бази за ім'ям db.internal.shop, і це ім'я не повинно резолвитися з інтернету. Що створити?
- Public hosted zone internal.shop
+ Private hosted zone internal.shop, прив'язану до VPC
- Alias-запис на базу в публічній зоні
- Route 53 Resolver inbound endpoint
= Private hosted zone відповідає лише для прив'язаних VPC. Для неї у VPC мають бути увімкнені DNS support і DNS hostnames.

? Після аварії основного регіону DNS-запис failover перемкнувся, але частина користувачів ще 10 хвилин потрапляла на старий endpoint. Що найімовірніше?
+ Великий TTL запису — клієнти й резолвери кешували стару відповідь
- Health check не працює з HTTPS
- Route 53 не підтримує failover між регіонами
- Alias-записи не враховують здоров'я цілі
= Відповідь кешується на час TTL (а деякі клієнти тримають довше). Для швидшого failover знижують TTL; для перемикання за секунди без залежності від кешу — Global Accelerator.
:::
