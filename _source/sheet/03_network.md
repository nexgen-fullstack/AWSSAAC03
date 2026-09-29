## 7. VPC і мережа

- **VPC** — приватна мережа в регіоні. IPv4 CIDR від /16 до /28. У кожній підмережі AWS резервує **5 IP-адрес** (перші 4 і останню).
- **Subnet** живе в **одній AZ**.
  - **Public subnet** — у route table є маршрут `0.0.0.0/0 → Internet Gateway (IGW)`.
  - **Private subnet** — маршруту на IGW немає; вихід в інтернет через **NAT Gateway**.
- **NAT Gateway** — керований, платно за годину + за кожен ГБ. Класичний (zonal) стоїть у public subnet; для HA — **по одному в кожній AZ** (інакше збій однієї AZ відріже інтернет усім, а трафік між AZ ще й коштує грошей).
- 🆕 **Regional NAT Gateway** (з листопада 2025) — один на VPC, сам розширюється на потрібні AZ, public subnet не потрібен. Іспит частіше питає класичну схему «NAT на кожну AZ».
- **NAT instance** — старий самокерований варіант (EC2, вимкнути Source/Destination check). Дешевший, але без HA і масштабування.
- **Egress-only Internet Gateway** — для **IPv6**: вихід в інтернет без вхідних з'єднань (аналог NAT для IPv6).
- **Security Group (SG)** — на рівні інстансу (ENI), **stateful** (відповідь дозволяється автоматично), **тільки Allow**. Можна посилатися на іншу SG як на джерело.
- **Network ACL (NACL)** — на рівні підмережі, **stateless** (треба окремо дозволити відповідь на ephemeral ports 1024–65535), є **Allow і Deny**, правила перевіряються за номером (від меншого, спрацьовує перше збігле).
- **Route table** — перемагає найспецифічніший маршрут (longest prefix match).

### Схема типової VPC

<figure class="diagram" id="fig-vpc" data-caption="Типова VPC: публічні й приватні підмережі у двох AZ">
<div class="dg-box"><div class="dg-label">Region · VPC 10.0.0.0/16 <span class="dg-node net">🌐 Internet Gateway</span><span class="dg-node sto">🪣 Gateway endpoint → S3</span></div>
<div class="dg-azs">
<div class="dg-box dg-az"><div class="dg-label">AZ a</div>
<div class="dg-sub pub"><b>Public subnet</b> 10.0.1.0/24<div class="dg-nodes"><span class="dg-node net">ALB (вузол)</span><span class="dg-node net">NAT Gateway</span></div><small>0.0.0.0/0 → IGW</small></div>
<div class="dg-sub app"><b>Private subnet — застосунок</b> 10.0.11.0/24<div class="dg-nodes"><span class="dg-node cmp">EC2 (Auto Scaling)</span></div><small>0.0.0.0/0 → NAT Gateway (AZ a)</small></div>
<div class="dg-sub db"><b>Private subnet — БД</b> 10.0.21.0/24<div class="dg-nodes"><span class="dg-node db">RDS primary</span></div><small>маршруту в інтернет немає</small></div>
</div>
<div class="dg-box dg-az"><div class="dg-label">AZ b</div>
<div class="dg-sub pub"><b>Public subnet</b> 10.0.2.0/24<div class="dg-nodes"><span class="dg-node net">ALB (вузол)</span><span class="dg-node net">NAT Gateway</span></div><small>0.0.0.0/0 → IGW</small></div>
<div class="dg-sub app"><b>Private subnet — застосунок</b> 10.0.12.0/24<div class="dg-nodes"><span class="dg-node cmp">EC2 (Auto Scaling)</span></div><small>0.0.0.0/0 → NAT Gateway (AZ b)</small></div>
<div class="dg-sub db"><b>Private subnet — БД</b> 10.0.22.0/24<div class="dg-nodes"><span class="dg-node db">RDS standby (Multi-AZ)</span></div><small>синхронна копія, читати з неї не можна</small></div>
</div>
</div></div>
<figcaption>Інтернет → IGW → ALB (публічні підмережі) → EC2 (приватні). EC2 виходять в інтернет через NAT Gateway своєї AZ. До S3 — через безкоштовний gateway endpoint. SG бази пускає лише SG серверів застосунку (порт 3306 або 5432).</figcaption>
</figure>

### Доступ до сервісів і з'єднання

- **VPC Endpoints** — доступ до сервісів AWS без інтернету і без NAT:
  - **Gateway endpoint** — тільки **S3 і DynamoDB**, безкоштовний, додається запис у route table.
  - **Interface endpoint (PrivateLink)** — ENI з приватним IP у підмережі. Майже всі сервіси (SQS, SNS, KMS, Secrets Manager, ECR, CloudWatch, S3…). Платно. Доступний з on-prem через VPN/Direct Connect.
  - **Endpoint policy** — обмежує, що можна робити через endpoint (напр., лише певні bucket).
- **AWS PrivateLink** — надати свій сервіс іншим VPC/акаунтам приватно: провайдер ставить **NLB** → endpoint service, споживач створює interface endpoint. Односторонній доступ, CIDR можуть перетинатися, масштабується на тисячі споживачів.
- **VPC Peering** — пряме з'єднання двох VPC (між акаунтами й регіонами). **Нетранзитивне** (A–B і B–C не дають A–C). CIDR **не можуть перетинатися**. Потрібно оновити route tables з обох боків.
- **Transit Gateway (TGW)** — хаб для сотень VPC, VPN і Direct Connect. **Транзитивна** маршрутизація, окремі route tables для сегментації, peering між регіонами, шариться через RAM, ECMP для VPN (сумує пропускну здатність тунелів), multicast.
- **Site-to-Site VPN** — IPsec-тунелі через інтернет: **Virtual Private Gateway (VGW)** або TGW на боці AWS + **Customer Gateway** на боці офісу. 2 тунелі для резерву. До 1,25 Gbps на тунель (🆕 з листопада 2025 — тунелі до 5 Gbps на TGW). Налаштовується за хвилини.
  - **VPN CloudHub** — кілька офісів спілкуються між собою через VGW.
  - **Accelerated VPN** — через мережу Global Accelerator (лише з TGW).
- **Direct Connect (DX)** — виділений приватний канал до AWS. Dedicated: 1/10/100/400 Gbps. Hosted (через партнера): від 50 Mbps до 25 Gbps. Стабільна затримка, дешевший вихідний трафік. Прокладання — **тижні або місяці**.
  - **Не шифрується** сам по собі → **IPsec VPN поверх DX** або **MACsec**.
  - **Direct Connect Gateway** — один DX до багатьох VPC у різних регіонах.
  - Резервування: 2 DX у **різних DX-локаціях** (максимальна стійкість) або DX + Site-to-Site VPN як дешевий бекап.
  - VIF: private (до VPC), public (до публічних сервісів AWS), transit (до TGW).
- **AWS Client VPN** — доступ окремих співробітників (ноутбуків) до VPC (OpenVPN).

### Схема гібридного з'єднання

<figure class="diagram" id="fig-hybrid" data-caption="Гібридне з'єднання: офіс ↔ AWS через VPN або Direct Connect і Transit Gateway">
<div class="flow">
<div class="st"><b>🏢 On-premises</b>Дата-центр або офіс: Customer Gateway (роутер), AD, DNS</div>
<span class="ar">⇄</span>
<div class="st"><b>🔌 Канал</b><span class="dg-node net">Site-to-Site VPN</span> IPsec через інтернет, за хвилини, 1,25 Gbps на тунель<br><span class="dg-node net">Direct Connect</span> приватний канал, тижні, 1–400 Gbps; шифрування — VPN поверх DX або MACsec</div>
<span class="ar">⇄</span>
<div class="st"><b>🔀 Transit Gateway</b>Хаб з транзитивною маршрутизацією. DX підключають через Direct Connect Gateway</div>
<span class="ar">⇄</span>
<div class="st"><b>☁️ VPC A · VPC B · VPC C</b>Інші регіони — через TGW peering. DNS між офісом і VPC — Route 53 Resolver inbound/outbound endpoints</div>
</div>
<figcaption>Дешево і швидко → VPN. Стабільно і великі обсяги → Direct Connect (+ VPN як резерв). Багато VPC → Transit Gateway замість десятків peering-з'єднань.</figcaption>
</figure>

### Решта мережевих можливостей

- **VPC Flow Logs** — метадані IP-трафіку (хто, куди, порт, ACCEPT/REJECT) → CloudWatch Logs, S3 або Firehose. Вміст пакетів не пишуть (для цього — Traffic Mirroring).
- **Доступ до приватних EC2 без SSH:** **SSM Session Manager** (жодних відкритих портів, логування сесій) або EC2 Instance Connect Endpoint. Класичний варіант — bastion host у public subnet.
- **Гібридний DNS — Route 53 Resolver endpoints:** **Inbound** — on-prem сервери резолвлять приватні DNS-імена AWS; **Outbound** + forwarding rules — VPC резолвить on-prem домени.

#### 🎯 Тригери

- Інстанси в private subnet мають завантажувати оновлення з інтернету → **NAT Gateway у public subnet (для HA — по одному на AZ)**
- Приватний EC2 звертається до S3 або DynamoDB без інтернету і безкоштовно → **Gateway VPC endpoint**
- Приватний EC2 звертається до SQS, KMS, Secrets Manager без інтернету → **Interface VPC endpoint (PrivateLink)**
- Великі рахунки за NAT Gateway через трафік до S3 → **Gateway endpoint для S3**
- Заблокувати конкретну IP-адресу → **Network ACL з Deny** (у Security Group Deny немає)
- БД має приймати трафік лише від вебсерверів → **SG бази з джерелом = SG вебсерверів**
- Надати свій сервіс сотням клієнтських VPC приватно, CIDR перетинаються → **PrivateLink (NLB + endpoint service)**
- З'єднати 2–3 VPC просто і дешево → **VPC Peering**
- З'єднати десятки або сотні VPC і on-prem з транзитивною маршрутизацією → **Transit Gateway**
- Швидко і дешево створити зашифрований канал до офісу → **Site-to-Site VPN**
- Стабільна пропускна здатність, приватне з'єднання, великі обсяги даних → **Direct Connect**
- Direct Connect + вимога шифрування → **IPsec VPN поверх DX** (або MACsec)
- Недорогий резерв для Direct Connect → **Site-to-Site VPN як backup**
- Максимальна стійкість гібридного з'єднання → **Кілька DX у різних DX-локаціях**
- Один Direct Connect до VPC у кількох регіонах → **Direct Connect Gateway**
- Віддалені співробітники підключаються до VPC → **AWS Client VPN**
- Кілька філій мають спілкуватися між собою через AWS → **VPN CloudHub**
- IPv6-інстанси виходять в інтернет, але недоступні ззовні → **Egress-only Internet Gateway**
- Адмін-доступ до EC2 без відкритого порту 22 і з логуванням сесій → **SSM Session Manager**
- On-prem сервери мають резолвити приватні DNS-імена в AWS → **Route 53 Resolver inbound endpoint**
- VPC має резолвити внутрішні домени офісу → **Route 53 Resolver outbound endpoint + forwarding rule**
- Проаналізувати відхилений трафік, хто стукає в інстанс → **VPC Flow Logs**
- Дозволити через endpoint доступ лише до кількох «своїх» bucket → **VPC endpoint policy**

#### ⚠️ Пастки

- Gateway endpoint — тільки S3 і DynamoDB. Для решти сервісів — Interface endpoint.
- Gateway endpoint не працює для трафіку з on-prem (через VPN/DX) — для цього Interface endpoint.
- VPC Peering нетранзитивний і неможливий при перетині CIDR.
- У NAT Gateway немає Security Groups. Один NAT Gateway в одній AZ — єдина точка відмови.

## 8. DNS і доставка контенту: Route 53, CloudFront, Global Accelerator

### Route 53

- Керований DNS + реєстрація доменів + health checks. SLA 100%.
- **Alias record** — вказує на ресурси AWS (ELB, CloudFront, S3 website, API Gateway, інший запис). Працює на **zone apex** (example.com). Запити до ресурсів AWS безкоштовні. **CNAME на apex не можна.**
- **Routing policies:**
  - **Simple** — один ресурс, без health checks.
  - **Weighted** — розподіл у відсотках (A/B-тести, поступова міграція, blue/green).
  - **Latency-based** — до регіону з найменшою затримкою для користувача.
  - **Failover** — active-passive: primary + secondary, перемикання за health check.
  - **Geolocation** — за країною/континентом користувача (мова, ліцензії, закони). Потрібен default-запис.
  - **Geoproximity** — за відстанню, з **bias** (змістити більше трафіку до певного регіону).
  - **Multivalue answer** — до 8 здорових записів (простий балансинг на клієнті, не заміна ELB).
  - **IP-based** — за CIDR клієнта (напр., за провайдером).
- **Health checks** перевіряють endpoint, інші health checks (calculated) або **CloudWatch alarm**. Приватні ресурси — лише через CloudWatch alarm, бо перевіряльники Route 53 працюють з інтернету.
- **Private hosted zone** — DNS тільки всередині VPC (потрібні `enableDnsHostnames` і `enableDnsSupport`).
- **S3 static website через alias** — ім'я bucket має збігатися з доменом (bucket `example.com` для запису `example.com`).

### CloudFront

- CDN: кешує контент на сотнях edge-локацій → менша затримка, менше навантаження на origin, дешевший трафік в інтернет.
- **Origins:** S3, ALB, EC2, API Gateway, будь-який HTTP-сервер (зокрема on-prem). **VPC origins** (з 2024) — приватні ALB/NLB/EC2 без публічного доступу.
- **Origin Access Control (OAC)** — bucket S3 доступний **лише через CloudFront**. OAC — сучасна заміна **OAI** (підтримує SSE-KMS).
- **Signed URL** — доступ до **одного** файлу. **Signed cookies** — до **багатьох** файлів (весь преміум-розділ) без зміни URL.
- **S3 presigned URL** — інша річ: тимчасовий доступ напряму до об'єкта S3 з правами того, хто підписав.
- **Geo restriction** — дозволити або заборонити країни.
- **Origin failover** — origin group (primary + secondary) при помилках 5xx/4xx.
- **Field-level encryption** — шифрує окремі поля форми (напр., номер картки) вже на edge.
- **CloudFront Functions** — легкий JS за мікросекунди (заголовки, редиректи, URL rewrite, прості перевірки токенів). **Lambda@Edge** — важча логіка, мережеві виклики, події origin request/response.
- **Cache behaviors** — різні правила кешу та origins за шаблоном шляху: `/static/*` → S3 з довгим кешем, `/api/*` → ALB без кешу.
- Кешування: TTL, cache policies, invalidation (краще версіонувати імена файлів).
- HTTPS: сертифікат ACM у **us-east-1**. Інтеграція з WAF і Shield.
- **Price classes** — обмежити набір edge-локацій, щоб платити менше.

### Global Accelerator

- 2 статичні **anycast IP-адреси**. Трафік заходить у найближчу edge-точку і далі йде мережею AWS до endpoint (ALB, NLB, EC2, Elastic IP) в одному або кількох регіонах.
- Швидкий failover між регіонами (не залежить від DNS-кешу), health checks, traffic dials і ваги.
- **TCP і UDP**, **нічого не кешує**. Для ігор, IoT, VoIP або HTTP, коли потрібні статичні IP і швидке перемикання регіонів.

#### 🎯 Тригери

- Направити домен example.com (apex) на ALB → **Route 53 Alias record**
- Поступово перевести 10% трафіку на нову версію → **Weighted routing**
- Користувачі мають потрапляти до найшвидшого для них регіону → **Latency-based routing**
- Active-passive DR між регіонами через DNS → **Failover routing + health checks**
- Користувачі з Німеччини бачать німецьку версію / обмеження контенту за країною → **Geolocation routing**
- Змістити більше трафіку до одного регіону → **Geoproximity routing (bias)**
- Прискорити статичний і динамічний контент для глобальних користувачів → **CloudFront**
- Заборонити прямий доступ до S3, лише через CloudFront → **OAC (Origin Access Control)**
- Платний доступ підписників до багатьох відео → **CloudFront signed cookies**
- Тимчасове посилання на один приватний файл → **CloudFront signed URL** (або S3 presigned URL)
- Заблокувати доступ до контенту з певних країн → **CloudFront geo restriction** (або WAF geo match)
- Статичні IP для глобального застосунку, UDP/ігри, швидкий failover регіонів → **Global Accelerator**
- Легкі зміни заголовків і редиректи на edge → **CloudFront Functions**
- Health check для приватного ресурсу → **CloudWatch alarm + Route 53 health check**
- Автоматично показати сторінку-заглушку з S3, якщо основний сайт впав → **Route 53 failover на S3 static website** (або CloudFront origin failover)
- Статика й API на одному домені через CloudFront, з різним кешуванням → **Cache behaviors за шляхом (/static/* → S3, /api/* → ALB)**

#### ⚠️ Пастки

- CloudFront — кеш HTTP(S)-контенту. Global Accelerator — без кешу, TCP/UDP, статичні IP.
- Route 53 failover залежить від TTL (клієнти кешують DNS). Global Accelerator перемикає швидше.

## 9. Балансувальники (ELB) і Auto Scaling

### Elastic Load Balancing

- **ALB (рівень 7: HTTP/HTTPS/gRPC/WebSocket).** Маршрутизація за path (`/api`), host (`api.example.com`), заголовками, query string, методом, IP джерела. Targets: EC2, IP, **Lambda**, ECS (dynamic port mapping). Кілька сертифікатів через **SNI**. Автентифікація через Cognito/OIDC. Sticky sessions. Редирект HTTP→HTTPS. **Статичного IP немає.**
- **NLB (рівень 4: TCP/UDP/TLS).** Мільйони запитів/с, наднизька затримка, **статичний IP на кожну AZ (можна Elastic IP)**, зберігає IP клієнта, основа для **PrivateLink**. Підтримує Security Groups.
- **GWLB (рівень 3, протокол GENEVE, порт 6081).** Прозоро пропускає трафік через **віртуальні апарати сторонніх вендорів** (файрволи, IDS/IPS, DPI) і масштабує їх.
- **CLB** — застарілий, для нових рішень не обирають.
- **Cross-zone load balancing:** ALB — увімкнено за замовчуванням, безкоштовно. NLB/GWLB — вимкнено за замовчуванням, трафік між AZ платний.
- **Deregistration delay** (connection draining) — дочекатися завершення запитів перед виведенням цілі (за замовчуванням 300 с).
- TLS можна завершувати на ELB (сертифікат ACM). Для end-to-end шифрування — HTTPS і до targets.

### Auto Scaling

- **ASG:** min / desired / max, **Launch Template** (Launch Configuration застаріла), кілька AZ, автоматична заміна нездорових інстансів.
- Health check за замовчуванням — статус EC2. **Увімкни ELB health check**, щоб ASG замінював інстанси, які «живі», але застосунок на них не відповідає.
- **Health check grace period** — час після запуску, коли ASG ще не перевіряє здоров'я (застосунку треба встигнути стартувати).
- **ELB access logs** → S3: хто, коли, який запит і з яким кодом відповіді.
- **Політики масштабування:**
  - **Target tracking** — тримати метрику на рівні (CPU 50%, запити на ціль ALB). Найпростіша і рекомендована.
  - **Step scaling** — різні кроки залежно від величини порушення аларму.
  - **Simple scaling** — одна дія + cooldown (застаріла).
  - **Scheduled** — за розкладом (відомий пік щопонеділка о 9:00).
  - **Predictive** — ML прогнозує циклічне навантаження і масштабує заздалегідь.
- **Воркери з черги SQS:** масштабуй за **backlog per instance** (`ApproximateNumberOfMessagesVisible` / кількість інстансів) через target tracking.
- **Cooldown / instance warmup** — пауза, поки новий інстанс не прогріється (default cooldown 300 с).
- **Lifecycle hooks** — дія під час запуску або видалення інстансу (встановити ПЗ, забрати логи перед термінацією).
- **Warm pools** — заздалегідь підготовлені інстанси для швидкого масштабування застосунків з довгим стартом.
- **Instance refresh** — поступово замінити всі інстанси на новий AMI / launch template.
- **Default termination policy (спрощено):** спершу AZ з найбільшою кількістю інстансів → інстанс з найстарішим launch template/configuration → найближчий до наступної години білінгу.
- **Mixed instances policy** — база On-Demand + Spot, кілька типів інстансів.
- **AWS Auto Scaling** (окремий сервіс) — масштабування кількох ресурсів разом: ASG, ECS, DynamoDB, репліки Aurora.

#### 🎯 Тригери

- Маршрутизувати `/api` і `/images` на різні групи серверів → **ALB path-based routing**
- Кілька доменів з різними сертифікатами на одному балансувальнику → **ALB + SNI**
- Статичний IP балансувальника (клієнт додає IP у whitelist) → **NLB з Elastic IP** (або Global Accelerator)
- TCP/UDP, мільйони запитів, мінімальна затримка → **NLB**
- Пропустити весь трафік через файрвол-апарат стороннього вендора → **Gateway Load Balancer**
- ALB бачить інстанс нездоровим, але ASG його не замінює → **Увімкнути ELB health check в ASG**
- Відомий пік щопонеділка о 9:00 → **Scheduled scaling**
- Щоденні циклічні піки, масштабуватися заздалегідь → **Predictive scaling**
- Тримати середній CPU близько 50% → **Target tracking scaling**
- Масштабувати воркерів за довжиною черги SQS → **Target tracking за backlog per instance**
- Застосунок довго стартує, масштабування запізнюється → **Warm pools** (або AMI з уже встановленим ПЗ)
- Забрати логи з інстансу перед його видаленням при scale-in → **Lifecycle hook**
- Користувач втрачає сесію, коли запит іде на інший сервер → **Sticky sessions** (краще — сесії в ElastiCache або DynamoDB)
- Оновити всі інстанси ASG на новий AMI без простою → **Instance refresh**
- Нові інстанси ASG одразу вважаються «нездоровими», бо застосунок довго стартує → **Збільшити health check grace period**

#### ⚠️ Пастки

- Для stateless-архітектури сесії зберігають в ElastiCache або DynamoDB, а не на самому інстансі.
- ALB не дає статичного IP. Потрібен статичний IP — NLB або Global Accelerator.
