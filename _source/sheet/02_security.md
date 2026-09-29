## 3. Основи: інфраструктура, модель відповідальності, Well-Architected

- **Region** — географічний регіон (напр., eu-central-1). Складається з кількох (зазвичай 3+) **Availability Zones (AZ)** — ізольованих дата-центрів з окремим живленням і мережею. Висока доступність = кілька AZ; захист від падіння всього регіону = кілька регіонів.
- **Edge locations** — точки CloudFront, Route 53 і Global Accelerator поруч з користувачами.
- **Local Zones** — AWS у великому місті (одноцифрові мс до користувачів). **Wavelength** — AWS всередині 5G-мережі оператора. **Outposts** — стійки AWS у твоєму дата-центрі.
- **Shared Responsibility Model:** AWS відповідає за безпеку **OF the cloud** (залізо, дата-центри, гіпервізор, керовані сервіси). Клієнт — за безпеку **IN the cloud** (дані, IAM, шифрування, Security Groups/NACL, патчі ОС на EC2, налаштування). На RDS і Lambda ОС патчить AWS, але доступи й дані — твоя відповідальність.
- **Well-Architected — 6 стовпів:** Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability. Увесь іспит побудований на них.
- **Service Quotas** — ліміти сервісів. Soft-ліміти можна підняти. Для DR-регіону квоти треба підняти **заздалегідь**.

### Well-Architected: принципи кожного стовпа (коротко)

- **Operational Excellence:** операції як код (IaC), часті малі зворотні зміни, передбачати збої, вчитися на кожному інциденті, спостережуваність (метрики, логи, трасування).
- **Security:** сильна основа ідентичності (least privilege, без довгострокових ключів), відстежуваність (логи, аудит), захист на **всіх** рівнях (мережа, інстанс, застосунок, дані), автоматизація безпеки, шифрування in transit і at rest, «тримати людей подалі від даних», готовність до інцидентів.
- **Reliability:** автоматичне відновлення після збоїв, тестування відновлення, горизонтальне масштабування замість одного великого ресурсу, «не вгадувати потужність» (Auto Scaling), зміни через автоматизацію.
- **Performance Efficiency:** використовувати готові керовані сервіси, «глобально за хвилини» (регіони, CloudFront), serverless, часті експерименти, обирати технологію під патерн доступу.
- **Cost Optimization:** фінансове керування хмарою, модель «плати за використане», вимірювати ефективність, не витрачати на «важку рутину» (керовані сервіси), розподіляти витрати (теги, акаунти).
- **Sustainability:** розуміти свій вплив, максимізувати завантаження ресурсів, нові ефективніші типи (напр., Graviton), керовані сервіси, менше зайвих даних і трафіку.

#### 🎯 Тригери

- Дані мають фізично лишатися у своєму дата-центрі, але потрібні сервіси AWS → **AWS Outposts**
- Одноцифрова мс затримка для користувачів у конкретному місті → **AWS Local Zones**
- Ультранизька затримка для мобільних пристроїв у 5G-мережі → **AWS Wavelength**
- Перенести VMware-середовище без зміни інструментів → **VMware Cloud on AWS**
- Хто патчить ОС на EC2? → **Клієнт** (на RDS — AWS)
- Резервний регіон не зміг запустити потрібну кількість інстансів під час аварії → **Заздалегідь підняти Service Quotas у DR-регіоні**

## 4. IAM і керування доступом

- **IAM** — глобальний сервіс. Суб'єкти: users, groups (групи не вкладаються одна в одну), roles. Політика — JSON: Effect, Action, Resource, Condition (і Principal у resource-based).
- **Логіка оцінки:** явний **Deny** > явний **Allow** > неявний Deny (за замовчуванням заборонено все).
- **Root user:** лише для задач, які може тільки root. Увімкни MFA, не створюй access keys для root.
- **Least privilege** — мінімальні права. **IAM Access Analyzer** знаходить ресурси, відкриті зовнішнім акаунтам, і генерує політики з історії CloudTrail.
- **Ролі замість ключів:** EC2 → instance profile з роллю; Lambda → execution role; ECS → task role. Ніколи не зберігай access keys у коді чи на EC2.
- **STS** видає тимчасові облікові дані: `AssumeRole` (крос-акаунт, перемикання ролей), `AssumeRoleWithSAML` (корпоративний IdP), `AssumeRoleWithWebIdentity` (краще через Cognito).
- **Cross-account доступ:** роль в акаунті B з trust policy для акаунта A. Або **resource-based policy** на ресурсі (S3 bucket policy, KMS key policy, SQS/SNS policy, Lambda policy).
- **Permission boundary** — «стеля» прав для user/role. Дає делегувати: розробник може створювати ролі, але не ширші за межу.
- **Умови в політиках:** `aws:SourceIp`, `aws:RequestedRegion`, `aws:MultiFactorAuthPresent`, `aws:PrincipalOrgID` (доступ лише акаунтам твоєї організації), `aws:SecureTransport`. Теги + умови = **ABAC**.
- **AWS Organizations:** багато акаунтів в OU; **consolidated billing** (один рахунок, об'ємні знижки, спільні RI і Savings Plans).
  - **SCP** — обмежують максимум дозволів для акаунтів/OU. Самі **не дають** прав. **Не діють** на management account.
  - **RCP** (resource control policies, з 2024) — обмеження на ресурси в акаунтах, напр. «до S3 не може звертатися ніхто поза організацією».
  - Також tag policies, backup policies.
- **AWS Control Tower** — готова landing zone для багатьох акаунтів за best practices: Account Factory, controls/guardrails (preventive = SCP, detective = Config rules, proactive = CloudFormation hooks), централізовані логи.
- **IAM Identity Center** (колишній AWS SSO) — єдиний вхід співробітників у всі акаунти й бізнес-застосунки. Permission sets. Джерело користувачів: вбудоване, Active Directory або зовнішній IdP (Okta, Entra ID) через SAML 2.0 / SCIM.
- **AWS Directory Service:**
  - **Managed Microsoft AD** — справжній AD в AWS, trust з on-prem AD.
  - **AD Connector** — проксі до on-prem AD, нічого не зберігає в AWS.
  - **Simple AD** — дешевий Samba-сумісний, без trust, для малих середовищ.
- **Amazon Cognito:**
  - **User Pools** — реєстрація і вхід користувачів **застосунку** (email/пароль, соцмережі, SAML/OIDC), видає JWT-токени, інтеграція з ALB і API Gateway.
  - **Identity Pools** — видає **тимчасові AWS-credentials** користувачам (навіть гостям), щоб напряму працювати з S3, DynamoDB тощо.
- **AWS RAM** — ділитися ресурсами між акаунтами: підмережі (VPC sharing), Transit Gateway, правила Route 53 Resolver, конфігурації License Manager тощо.
- **IAM Access Advisor** (last accessed) — показує, якими сервісами роль чи користувач реально користувалися → прибрати зайві права.
- **IAM Roles Anywhere** — on-prem сервери отримують тимчасові AWS-credentials за X.509-сертифікатом, без довгострокових ключів.

### Як AWS перевіряє доступ

<figure class="diagram" id="fig-iam" data-caption="Як AWS вирішує: дозволити чи заборонити запит (спрощено)">
<div class="dec">
<div class="dec-step"><span class="dec-n">1</span><div><b>Є явний Deny у будь-якій політиці?</b> SCP/RCP, resource-based, permission boundary, identity-based</div><span class="dec-out no">Так → ❌ DENY</span></div>
<div class="down">↓ ні</div>
<div class="dec-step"><span class="dec-n">2</span><div><b>SCP (і RCP) організації дозволяють дію?</b> Діють на member-акаунти, але не на management account</div><span class="dec-out no">Ні → ❌ DENY</span></div>
<div class="down">↓ так</div>
<div class="dec-step"><span class="dec-n">3</span><div><b>Permission boundary (якщо задана) дозволяє?</b> Це «стеля» прав користувача або ролі</div><span class="dec-out no">Ні → ❌ DENY</span></div>
<div class="down">↓ так</div>
<div class="dec-step"><span class="dec-n">4</span><div><b>Identity-based або resource-based policy дає Allow?</b></div><span class="dec-out yes">Так → ✅ ALLOW</span></div>
<div class="down">↓ ні</div>
<div class="dec-step"><span class="dec-n">5</span><div><b>Неявна заборона</b> — за замовчуванням заборонено все</div><span class="dec-out no">❌ DENY</span></div>
</div>
<figcaption>Крос-акаунтний доступ: потрібен Allow і з боку того, хто звертається (IAM-політика в акаунті A), і з боку ресурсу (resource-based policy або trust policy ролі в акаунті B). У реальній логіці AWS є ще нюанси (session policies тощо), але для іспиту достатньо цієї схеми.</figcaption>
</figure>

### Приклади політик

Читання одного bucket. Зверни увагу: `s3:ListBucket` дається на ARN самого bucket, а `s3:GetObject` — на об'єкти (`/*`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::my-bucket" },
    { "Effect": "Allow", "Action": "s3:GetObject",  "Resource": "arn:aws:s3:::my-bucket/*" }
  ]
}
```

Trust policy ролі для сторонньої компанії (акаунт 111122223333) із захистом від confused deputy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::111122223333:root" },
    "Action": "sts:AssumeRole",
    "Condition": { "StringEquals": { "sts:ExternalId": "id-від-вендора" } }
  }]
}
```

#### 🎯 Тригери

- Застосунок на EC2 має читати S3 → **IAM role (instance profile)**, а не access keys
- Дати іншому акаунту доступ до своїх ресурсів → **IAM role з trust policy + STS AssumeRole**
- Заборонити всім акаунтам в OU вимикати CloudTrail або працювати поза дозволеними регіонами → **SCP**
- Розробники можуть створювати ролі, але не ширші за певні права → **Permission boundary**
- Швидко налаштувати багато акаунтів «правильно», з guardrails і логуванням → **AWS Control Tower**
- Єдиний вхід співробітників у багато акаунтів AWS через корпоративний AD або Okta → **IAM Identity Center**
- Реєстрація і вхід користувачів мобільного або веб-застосунку, вхід через соцмережі → **Cognito User Pool**
- Користувачі мобільного застосунку мають завантажувати фото напряму в S3 → **Cognito Identity Pool** (тимчасові credentials)
- Повноцінний AD в AWS з довірою (trust) до on-prem AD → **AWS Managed Microsoft AD**
- Використати наявний on-prem AD без копіювання даних в AWS → **AD Connector**
- Дозволити доступ до bucket лише акаунтам своєї організації → **Bucket policy з умовою aws:PrincipalOrgID**
- Кілька акаунтів мають працювати в одній спільній VPC → **VPC sharing через AWS RAM**
- Знайти ресурси, до яких мають доступ зовнішні акаунти → **IAM Access Analyzer**
- Один рахунок і спільні знижки RI/Savings Plans на всі акаунти → **Organizations: consolidated billing**
- Надавати доступ за тегами (відділ, проєкт) замість сотень політик → **ABAC (теги + умови)**
- Стороння компанія (SaaS-вендор) отримує доступ до акаунта через роль, треба захист від confused deputy → **Роль з умовою sts:ExternalId у trust policy**
- On-prem сервери мають отримувати тимчасові AWS-credentials без довгострокових ключів → **IAM Roles Anywhere**
- Знайти й прибрати права, якими роль ніколи не користується → **IAM Access Advisor (last accessed) / IAM Access Analyzer**
- Вимагати MFA для небезпечних дій (напр., видалення) → **Умова aws:MultiFactorAuthPresent у політиці**

#### ⚠️ Пастки

- SCP **не дає** дозволів, а лише обмежує. На management account SCP не діє.
- `s3:ListBucket` — на ARN bucket, `s3:GetObject` / `s3:PutObject` — на `bucket/*`. Переплутаєш — буде AccessDenied.
- Крос-акаунт через resource-based policy: потрібен Allow з **обох** боків (у політиці ресурсу і в IAM-політиці того, хто звертається).
- Cognito **User Pool** = автентифікація (хто ти). **Identity Pool** = доступ до AWS (тимчасові ключі).
- IAM Identity Center — для **співробітників**; Cognito — для **клієнтів** застосунку.

## 5. Шифрування, ключі, секрети, сертифікати

- **At rest** — шифрування KMS; **in transit** — TLS (HTTPS, сертифікати ACM).
- **AWS KMS** — керовані ключі, **регіональні**.
  - **AWS managed keys** (`aws/s3`, `aws/ebs`) — ротація щороку автоматично, керувати політикою не можна.
  - **Customer managed keys** — сам керуєш key policy, grants і ротацією: автоматично раз на 90–2560 днів (за замовчуванням 365) або вручну on-demand.
  - Symmetric (AES-256) і asymmetric (RSA/ECC — підпис, шифрування поза AWS).
- **Key policy** — головний контроль доступу до ключа. Cross-account: дозвіл у key policy + IAM-політика в іншому акаунті.
- **Envelope encryption:** KMS `Encrypt` шифрує максимум **4 KB**; великі дані шифрують data key (`GenerateDataKey`).
- **Multi-Region keys** — той самий ключ у кількох регіонах: зашифрував в одному, розшифрував в іншому. Без них при копіюванні снапшота в інший регіон його перешифровують ключем того регіону.
- **ThrottlingException від KMS** при масовій роботі з S3 (SSE-KMS) → **S3 Bucket Keys** (у рази менше викликів KMS і дешевше).
- **CloudHSM** — виділений (single-tenant) апаратний HSM. Ключі повністю під твоїм контролем, AWS до них доступу не має. FIPS 140 Level 3. Стандартні API (PKCS#11, JCE, CNG), Oracle TDE, SSL offload. Можна підключити до KMS як custom key store.
- **ACM (AWS Certificate Manager):** безкоштовні публічні TLS-сертифікати для ELB, CloudFront, API Gateway; **автоматичне поновлення** (для DNS-валідації). Для **CloudFront** сертифікат має бути в регіоні **us-east-1**. Імпортовані сертифікати ACM сам не поновлює — стеж за терміном (події в EventBridge, Config rule).
- **Secrets Manager** — секрети + **автоматична ротація** (вбудована для RDS, Aurora, Redshift, DocumentDB; для решти — через Lambda), реплікація в інші регіони. Платно за кожен секрет.
- **SSM Parameter Store** — конфігурація і секрети (`SecureString` з KMS), ієрархія, standard tier безкоштовний. **Вбудованої ротації немає.**
- **EBS:** увімкни *encryption by default* для регіону. Незашифрований том → snapshot → copy snapshot з шифруванням → новий том.
- **RDS:** шифрування вмикається **тільки при створенні**. Незашифрована БД → snapshot → copy з шифруванням → restore. Read replica шифрується так само, як основна БД.
- **S3:** **SSE-S3** (за замовчуванням для всіх нових об'єктів з 2023), **SSE-KMS** (аудит використання ключа в CloudTrail + окремий контроль доступу до ключа), **DSSE-KMS** (двошарове), **SSE-C** (ключ надає клієнт, тільки HTTPS), шифрування на клієнті.
- **Примусити HTTPS до S3:** bucket policy з Deny, якщо `aws:SecureTransport` = false.
- **Видалення ключа KMS** — лише із затримкою 7–30 днів (за замовчуванням 30). Поки строк не минув, видалення можна скасувати. Безпечніша альтернатива — вимкнути (disable) ключ.
- **Key policy обов'язкова:** якщо вона не дозволяє акаунту делегувати доступ через IAM, IAM-політики до ключа не діють.
- **Зашифрований снапшот для іншого акаунта:** поділитися можна лише снапшотом, зашифрованим **customer managed key** (ділишся снапшотом і даєш доступ до ключа). Снапшот з AWS managed key спершу копіюють, перешифрувавши своїм ключем.
- **CloudHSM для HA** — кластер щонайменше з 2 HSM у різних AZ.

#### 🎯 Тригери

- Потрібен аудит, хто і коли використовував ключ шифрування даних у S3 → **SSE-KMS** (виклики ключа видно в CloudTrail)
- Ключі лише під твоїм контролем в апаратному модулі, FIPS 140 Level 3, AWS не має доступу → **CloudHSM**
- Автоматично змінювати пароль до БД кожні 30 днів → **Secrets Manager (rotation)**
- Дешево зберігати конфігурацію і рядки підключення без ротації → **SSM Parameter Store**
- HTTPS на ALB або CloudFront без ручного поновлення сертифікатів → **ACM**
- Шифрувати в одному регіоні й розшифровувати в іншому тим самим ключем → **KMS Multi-Region keys**
- ThrottlingException від KMS при масовому завантаженні в S3 з SSE-KMS → **S3 Bucket Keys**
- Зашифрувати наявну незашифровану RDS → **Snapshot → copy з шифруванням → restore**
- Шифрувати через KMS файли більші за 4 KB → **Envelope encryption (data key)**
- Заборонити HTTP-доступ і незашифровані завантаження в bucket → **Bucket policy з Deny та умовами**
- Ключ має змінюватися частіше, ніж раз на рік → **Customer managed key з власним періодом ротації**
- Поділитися зашифрованим снапшотом RDS/EBS з іншим акаунтом → **Customer managed KMS key + доступ до ключа для того акаунта**
- Ключ KMS випадково запланували на видалення → **Скасувати видалення, поки не минув період очікування (7–30 днів)**

#### ⚠️ Пастки

- На існуючій RDS або EBS не можна просто «увімкнути шифрування» — тільки через копію снапшота.
- Сертифікат ACM для CloudFront — тільки в us-east-1 (для ALB — у регіоні ALB).
- Класично (і на іспиті) публічний сертифікат ACM ставиться лише на інтегровані сервіси (ELB, CloudFront, API Gateway), а не прямо на EC2.

## 6. Сервіси безпеки: захист від атак і аудит

- **AWS WAF** — файрвол рівня 7 (HTTP): SQL injection, XSS, блокування IP і країн (geo match), **rate-based rules** (ліміт запитів з одного IP), managed rule groups, Bot Control. Ставиться на **CloudFront, ALB, API Gateway, AppSync, Cognito User Pool, App Runner**. **Не на NLB і не на EC2.**
- **AWS Shield Standard** — безкоштовно й автоматично для всіх: DDoS рівнів 3–4.
- **AWS Shield Advanced** — платно (~$3 000/міс на організацію): команда **SRT** 24/7, **захист від зростання рахунку** через DDoS, розширена детекція, захист рівня 7 разом з WAF. Для CloudFront, Route 53, Global Accelerator, ELB, EC2 Elastic IP.
- **AWS Firewall Manager** — централізовано керує правилами WAF, Shield Advanced, Security Groups, Network Firewall, DNS Firewall **у всіх акаунтах Organizations**. Нові акаунти і ресурси отримують правила автоматично.
- **AWS Network Firewall** — керований файрвол на рівні VPC (stateful/stateless, IPS/IDS, фільтрація за доменами, правила Suricata). Часто — в окремій inspection VPC за Transit Gateway.
- **Route 53 Resolver DNS Firewall** — блокує DNS-запити з VPC до шкідливих доменів.
- **Amazon GuardDuty** — виявлення **загроз** за допомогою ML: аналізує CloudTrail, VPC Flow Logs, DNS-логи (+ S3, EKS, RDS, Lambda, runtime, сканування malware). Криптомайнінг, скомпрометовані ключі, зв'язок з C&C. Знахідки → EventBridge → автоматична реакція.
- **Amazon Inspector** — сканування **вразливостей** (CVE) і мережевої доступності: EC2, образи в ECR, Lambda. Працює безперервно.
- **Amazon Macie** — ML-пошук **чутливих даних** (PII, номери карток) у **S3**.
- **Amazon Detective** — **розслідування**: граф подій і першопричина знахідок GuardDuty.
- **AWS Security Hub** — єдина панель знахідок (GuardDuty, Inspector, Macie, Config, партнери) + перевірки стандартів (CIS, PCI DSS, AWS Foundational Security Best Practices).
- **AWS Artifact** — звіти відповідності AWS (SOC, PCI, ISO) і угоди (напр., BAA для HIPAA).
- **AWS Audit Manager** — автоматичний збір доказів для аудиту.
- **CloudTrail vs Config vs CloudWatch:** CloudTrail — **хто і коли** викликав API (аудит). Config — **яка конфігурація** ресурсу була і чи відповідає вона правилам (історія, compliance). CloudWatch — **метрики, логи, аларми** (продуктивність).
- **Багато акаунтів:** GuardDuty, Security Hub, Macie та Inspector вмикають централізовано через **delegated administrator** в AWS Organizations — нові акаунти підключаються автоматично.
- **Inspector знаходить, Patch Manager латає:** вразливості шукає Inspector, а патчі встановлює SSM Patch Manager.

#### 🎯 Тригери

- SQL injection, XSS, блокування країн на ALB або CloudFront → **AWS WAF**
- Обмежити кількість запитів з одного IP (HTTP flood) → **WAF rate-based rule**
- DDoS-захист + експерти 24/7 + компенсація витрат від атаки → **Shield Advanced**
- Керувати правилами WAF і Security Groups у всіх акаунтах централізовано → **Firewall Manager**
- Фільтрувати вихідний трафік VPC за доменними іменами, IPS для VPC → **AWS Network Firewall**
- Незвичні API-виклики, криптомайнінг, скомпрометований інстанс → **GuardDuty**
- Знайти вразливості (CVE) в EC2, образах ECR, Lambda → **Amazon Inspector**
- Знайти PII або персональні дані в S3 → **Amazon Macie**
- Знайти першопричину інциденту безпеки → **Amazon Detective**
- Одна панель стану безпеки всіх акаунтів + перевірки CIS/PCI → **Security Hub**
- Аудитору потрібен звіт SOC 2 або PCI від AWS → **AWS Artifact**
- Хто видалив bucket або змінив Security Group? → **CloudTrail**
- Перевіряти, що всі EBS-томи зашифровані, і бачити історію змін конфігурації → **AWS Config** (+ автовиправлення через SSM Automation)
- Автоматично реагувати на знахідку GuardDuty (ізолювати інстанс) → **EventBridge rule → Lambda / SSM Automation**
- Хтось зробив bucket публічним — треба автоматично виправити → **AWS Config rule + автовиправлення (SSM Automation)** або EventBridge → Lambda
- Увімкнути GuardDuty в усіх акаунтах організації, включно з новими → **Delegated administrator в AWS Organizations**

#### ⚠️ Пастки

- WAF не підтримує NLB. Для NLB: Shield Advanced від DDoS, фільтрація — Security Groups, NACL або Network Firewall.
- GuardDuty = загрози, Inspector = вразливості, Macie = чутливі дані в S3. Їх часто плутають.
