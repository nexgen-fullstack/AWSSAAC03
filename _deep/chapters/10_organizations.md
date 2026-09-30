---
id: organizations
module: Безпека і доступ
title: Багато акаунтів — AWS Organizations, SCP, Control Tower
short: Organizations і SCP
emoji: 🏢
domains: secure, cost
svc: organizations, scp, controltower, ram
---
> 🎬 **Історія Хмаринки.** Хмаринка росте. Стажер у тестовому середовищі випадково видалив базу — добре, що тестову, а не бойову: обидві жили в одному акаунті. Тепер Тарас хоче розділити: **prod** окремо від **dev**, журнали безпеки — там, де їх ніхто не зможе стерти, а для експериментів — «пісочниця» з лімітом витрат. І ще правило від юриста: жодних ресурсів поза ЄС, хоч би хто що клацнув. Як керувати п'ятьма (а згодом — п'ятдесятьма) акаунтами як одним цілим? Для цього є **AWS Organizations**.

> 🖼️ **Образ.** Корпорація з окремими філіями. Кожна філія (акаунт) має свій бюджет, персонал і сейф, і пожежа в одній не перекидається на інші. Над ними — головний офіс (management account), який оплачує всі рахунки разом (оптом дешевше) і видає **внутрішній статут** (SCP): «жодна філія не відкриває представництв поза ЄС». Статут нікого не наймає і нічого не дозволяє — він лише визначає, чого не можна робити навіть директору філії.

## Навіщо багато акаунтів

Один акаунт на все — як один спільний сейф для всієї компанії. AWS рекомендує **стратегію багатьох акаунтів**, бо акаунт — найсильніша межа ізоляції в AWS:

- **Безпека і «радіус ураження».** Помилка чи злам у dev не зачепить prod.
- **Різні правила.** У пісочниці можна експериментувати, у prod — лише через перевірені конвеєри.
- **Прозорі витрати.** Рахунок кожного акаунта — окремий рядок: видно, скільки коштує кожен проєкт.
- **Квоти.** Ліміти сервісів — на акаунт: навантаження одного проєкту не «з'їсть» квоти іншого.
- **Аудит.** Журнали безпеки — в окремому акаунті, куди мають доступ лише кілька людей.

## AWS Organizations {#org}

**AWS Organizations** об'єднує акаунти в одну структуру з централізованим керуванням. Сервіс безкоштовний.

- **Management account** (раніше — master, payer) — акаунт, що створив організацію. Він платить за всіх, керує структурою і політиками. Ресурсів робочих навантажень у ньому **не тримають**.
- **Member accounts** — усі інші. Їх можна створювати прямо з Organizations (програмно, за хвилини) або запрошувати наявні.
- **Organizational Units (OU)** — «папки» для акаунтів, можуть бути вкладеними. Політики, прикріплені до OU, успадковують усі акаунти всередині.
- **Root** — вершина дерева (не плутай з root user акаунта!).

<figure class="diagram" data-caption="Організація Хмаринки: OU і акаунти">
<div class="tiers">
<div class="tier"><span class="tl">Root</span><span class="dg-node sec">Management account — лише білінг і керування</span><span class="dg-node sec">SCP: лише регіони ЄС · заборона виходу з організації</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">OU Security</span><span class="dg-node sec">log-archive — журнали CloudTrail і Config усіх акаунтів</span><span class="dg-node sec">audit — інструменти безпеки (GuardDuty, Security Hub)</span></div>
<div class="tier"><span class="tl">OU Infrastructure</span><span class="dg-node net">network — Transit Gateway, спільні VPC, DNS</span></div>
<div class="tier"><span class="tl">OU Workloads</span><span class="dg-node cmp">shop-prod</span><span class="dg-node cmp">shop-dev</span><span class="dg-node cmp">analytics-prod</span></div>
<div class="tier"><span class="tl">OU Sandbox</span><span class="dg-node cmp">sandbox-taras — експерименти, SCP з жорсткими обмеженнями</span></div>
</div>
<figcaption>Політика на Root діє на всі акаунти; на OU — лише на акаунти в ній. Рекомендовані AWS OU: Security, Infrastructure, Workloads (Prod / NonProd), Sandbox.</figcaption>
</figure>

### Consolidated billing: один рахунок і знижки

Усі акаунти організації отримують **один спільний рахунок**:

- витрати видно окремо по кожному акаунту;
- **обсяги сумуються** — ступінчасті знижки (наприклад, у S3 за великі обсяги) досягаються швидше;
- знижки від **Reserved Instances і Savings Plans** за замовчуванням **діляться** між акаунтами: якщо в prod зарезервований сервер простоює, знижку «підхопить» такий самий сервер у dev. (Спільне використання можна вимкнути для окремих акаунтів.)

## SCP — «статут» організації {#scp}

**Service Control Policy (SCP)** — політика, що визначає **максимум дозволів** для всіх IAM-користувачів і ролей (і навіть root user) у member-акаунтах. Ключові правила — кожне на іспиті:

1. SCP **не дає** жодних прав. Щоб дія стала можливою, потрібні і дозвіл SCP, і дозвіл IAM-політики.
2. SCP **діє на всіх** у member-акаунті, включно з адміністраторами й root user акаунта. Обійти зсередини неможливо.
3. SCP **не діє на management account** — ще одна причина не тримати там робочих ресурсів.
4. SCP не обмежують **service-linked ролі** (якими сервіси AWS керують собою).
5. SCP успадковуються вниз по дереву: ефективні — **перетин** SCP усіх рівнів від Root до акаунта.

За замовчуванням до кожного рівня прикріплена SCP `FullAWSAccess` (дозволити все) — тому організація «працює як раніше», поки ти не додаси заборони. Дві стратегії:

- **Deny list** (типова): лишаємо `FullAWSAccess` і додаємо явні заборони. Простіше в підтримці.
- **Allow list**: прибираємо `FullAWSAccess` і дозволяємо лише перелічені сервіси. Суворіше, але кожен новий сервіс треба дозволяти явно.

Приклад SCP для Хмаринки — заборонити роботу поза ЄС (глобальні сервіси виключені, бо вони працюють через `us-east-1`):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyOutsideEU",
    "Effect": "Deny",
    "NotAction": ["iam:*", "organizations:*", "route53:*", "cloudfront:*", "support:*", "sts:*", "budgets:*", "ce:*"],
    "Resource": "*",
    "Condition": { "StringNotEquals": { "aws:RequestedRegion": ["eu-central-1", "eu-west-1"] } }
  }]
}
```

Інші класичні SCP:

- заборонити `organizations:LeaveOrganization` (акаунт не «втече» з-під контролю);
- заборонити вимикати CloudTrail, GuardDuty, AWS Config (`cloudtrail:StopLogging`, `cloudtrail:DeleteTrail`…);
- заборонити створювати IAM users і access keys (усі — через Identity Center);
- заборонити дії root user у member-акаунтах (умова `aws:PrincipalArn` на `arn:aws:iam::*:root`);
- дозволити лише певні типи серверів у пісочниці (щоб ніхто не запустив дорогий GPU-сервер).

## RCP — захист з боку ресурсів {#rcp}

**Resource Control Policy (RCP)** — новіший тип політик Organizations (з кінця 2024 року). Якщо SCP обмежує, що можуть робити **твої** люди й ролі, то RCP обмежує, хто може отримати доступ до **твоїх ресурсів** — навіть якщо якийсь розробник помилково відкрив bucket іншому акаунту. Класичний приклад: «до об'єктів S3, ключів KMS, секретів і черг організації не може звертатися ніхто поза організацією» (умова `aws:PrincipalOrgID`).

Разом вони будують **периметр даних** (data perimeter):

| Периметр | Питання | Інструменти |
|---|---|---|
| Ідентичності | Мої люди звертаються лише до довірених ресурсів? | SCP з умовами на ресурси |
| Ресурсів | До моїх ресурсів звертаються лише довірені особи? | RCP, resource-based політики з `aws:PrincipalOrgID` |
| Мережі | Доступ лише з моїх мереж? | VPC endpoints, умови `aws:SourceVpce`, `aws:SourceIp` |

:::note 📌 Інші політики Organizations
- **Tag policies** — стандартизують теги (наприклад, обов'язковий тег `CostCenter` з дозволеними значеннями).
- **Backup policies** — централізовані плани резервного копіювання AWS Backup для всіх акаунтів.
- **AI services opt-out policies** — заборона AWS використовувати дані для покращення AI-сервісів.
- **Declarative policies** — «бажаний стан» для сервісів (наприклад, заборонити публічні образи серверів), що діє навіть при появі нових API.
:::

## Централізоване керування безпекою {#delegated}

У багатьох сервісах безпеки є режим **delegated administrator**: management account призначає окремий акаунт (наприклад, `audit`) адміністратором сервісу для всієї організації. Так вмикають **GuardDuty, Security Hub, Macie, Inspector, AWS Config, IAM Access Analyzer, Firewall Manager** — і нові акаунти підключаються автоматично.

Інші «організаційні» можливості:

- **Organization trail** у CloudTrail — один журнал API-викликів усіх акаунтів у bucket акаунта log-archive.
- **CloudFormation StackSets** — розгорнути однакові ресурси в багатьох акаунтах і регіонах.
- **Централізоване керування root-доступом** — прибрати паролі root у member-акаунтах; рідкісні привілейовані дії виконуються короткими сесіями з management account.
- Умова **`aws:PrincipalOrgID`** у політиках ресурсів — «пускати всі акаунти моєї організації» одним рядком, замість переліку сотні номерів.

## AWS Control Tower: готова «зона приземлення» {#control-tower}

Налаштувати все вищеописане вручну — тижні роботи. **AWS Control Tower** робить це за години за кращими практиками AWS і створює **landing zone** — готове багатоакаунтне середовище:

- створює Organizations і базові OU (Security з акаунтами **Log Archive** і **Audit**);
- вмикає централізовані журнали CloudTrail і Config;
- налаштовує IAM Identity Center для входу;
- **Account Factory** — нові акаунти «за шаблоном» за кілька кліків (або з коду, наприклад через Terraform);
- **Controls (guardrails)** — готові правила з трьома типами:
  - **preventive** — не дають зробити заборонене (реалізовані через SCP/RCP): «не можна вимкнути CloudTrail»;
  - **detective** — виявляють порушення (через правила AWS Config): «знайти bucket без шифрування»;
  - **proactive** — перевіряють ресурси **до** створення (через хуки CloudFormation);
- **дашборд** відповідності і виявлення дрейфу (коли хтось змінив налаштування вручну).

:::mnemo 🧠 Organizations чи Control Tower?
**Organizations** — конструктор: акаунти, OU, політики, білінг. **Control Tower** — готовий будинок з цього конструктора за проєктом AWS: landing zone, журнали, guardrails, фабрика акаунтів. На іспиті «швидко налаштувати багатоакаунтне середовище за кращими практиками з guardrails» → **Control Tower**.
:::

## AWS RAM: ділитися ресурсами між акаунтами {#ram}

Не все треба дублювати в кожному акаунті. **AWS Resource Access Manager (RAM)** дозволяє **ділитися** ресурсами з іншими акаунтами (або з усією організацією чи OU):

- **підмережі VPC** — **VPC sharing**: мережевий акаунт володіє VPC, а акаунти застосунків запускають у спільних підмережах свої сервери (кожен керує своїми ресурсами, але мережа одна);
- **Transit Gateway** — один хаб для VPC усіх акаунтів;
- правила **Route 53 Resolver** (гібридний DNS), prefix lists, політики Network Firewall;
- **Capacity Reservations**, License Manager, Aurora-кластери для клонування та інше.

:::lab 🧪 Спробуй у справжньому AWS: перевір SCP до застосування
**Вартість:** безкоштовно. **Час:** 10 хвилин. Організацію створювати не треба: використаємо валідатор політик IAM Access Analyzer, який розуміє і SCP.
1. Відкрий **CloudShell** (під адміністратором).
2. Створи файл політики:
```bash
cat > scp.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "DenyLeaveOrg", "Effect": "Deny", "Action": "organizations:LeaveOrganization", "Resource": "*" },
    { "Sid": "ProtectTrail", "Effect": "Deny",
      "Action": ["cloudtrail:StopLogging", "cloudtrail:DeleteTrail"], "Resource": "*" }
  ]
}
JSON
```
3. Перевір її:
```bash
aws accessanalyzer validate-policy --policy-type SERVICE_CONTROL_POLICY --policy-document file://scp.json
```
Порожній список `findings` — політика коректна.
4. Навмисно зіпсуй: заміни `"Action": "organizations:LeaveOrganization"` на `"Action": "organizations:LeaveOrganisation"` (британське написання) і повтори перевірку — валідатор підкаже, що такої дії не існує.
5. Подумай: чому SCP з цими двома правилами треба прикріплювати до **Root** або OU, а не до management account?
**Прибери за собою:** `rm scp.json`.
:::

#### 💡 Запам'ятай

- Акаунт — найсильніша межа ізоляції; AWS рекомендує багато акаунтів (prod, dev, security, log archive, sandbox).
- **Organizations:** management account + member accounts + OU; **consolidated billing** — один рахунок, сумарні обсяги, спільні RI/Savings Plans.
- **SCP** — стеля прав для member-акаунтів; **не дає** прав; діє на всіх, включно з root акаунта; **не діє на management account**; не обмежує service-linked ролі.
- **RCP** — стеля для доступу до ресурсів (периметр даних): «ніхто поза організацією».
- **`aws:PrincipalOrgID`** — пустити всю організацію одним рядком.
- **Delegated administrator** — централізовано вмикає GuardDuty, Security Hub, Config тощо для всіх акаунтів.
- **Control Tower** — landing zone за кращими практиками: Log Archive + Audit, Account Factory, guardrails (preventive / detective / proactive).
- **RAM** — ділитися підмережами (VPC sharing), Transit Gateway, правилами Resolver між акаунтами.

#### 🎯 Як питають на іспиті

- Заборонити всім акаунтам в OU вимикати CloudTrail, навіть адміністраторам → **SCP з Deny**
- Дозволити роботу лише в регіонах ЄС для всіх акаунтів → **SCP з умовою aws:RequestedRegion (глобальні сервіси виключити)**
- SCP прикріплена до Root, але адміністратор management account усе ще може все → **SCP не діє на management account**
- Один рахунок і спільні знижки на всі акаунти компанії → **Organizations consolidated billing**
- Швидко створити багатоакаунтне середовище за кращими практиками, з guardrails і централізованими журналами → **AWS Control Tower**
- Виявляти (а не забороняти) порушення правил у всіх акаунтах → **detective controls (AWS Config) у Control Tower**
- Кілька акаунтів мають запускати ресурси в одній спільній VPC → **VPC sharing через AWS RAM**
- Дозволити доступ до bucket усім акаунтам організації, включно з майбутніми → **bucket policy з умовою aws:PrincipalOrgID**
- Гарантувати, що ресурси організації недоступні зовнішнім особам, навіть при помилці в політиці ресурсу → **RCP**
- Увімкнути GuardDuty в усіх акаунтах і автоматично — в нових → **delegated administrator в Organizations**
- Обов'язковий тег CostCenter з дозволеними значеннями в усіх акаунтах → **tag policies**

#### ⚠️ Пастки

- SCP — не IAM-політика: вона нічого не дозволяє, і ефективні права = перетин SCP і IAM.
- Root **організації** (вершина дерева) ≠ root **user** акаунта.
- SCP з allow-list без `FullAWSAccess` заблокує все, що явно не дозволено, — включно з сервісами, про які легко забути.
- Control Tower **використовує** Organizations, SCP і Config — це не заміна, а надбудова.

## ✅ Перевір себе

:::quiz
? У компанії 25 акаунтів в AWS Organizations. Жоден member-акаунт не повинен мати змоги вимкнути AWS CloudTrail, навіть його адміністратор. Яке рішення найефективніше?
+ SCP з Deny на cloudtrail:StopLogging і cloudtrail:DeleteTrail, прикріплена до Root або OU
- IAM-політика з Deny в кожному акаунті
- Правило AWS Config, що виявляє вимкнений CloudTrail
- Сповіщення CloudWatch при вимкненні CloudTrail
= SCP обмежує всіх principal-ів у member-акаунтах, включно з адміністраторами і root user, і її не можна змінити зсередини акаунта. IAM-політики адміністратор акаунта може змінити, а Config і CloudWatch лише виявляють порушення.

? До Root організації прикріплено SCP, що забороняє запуск серверів EC2 поза eu-central-1. Адміністратор management account запускає сервер у us-east-1. Що станеться?
- Запит буде відхилено SCP
+ Сервер запуститься, бо SCP не діє на management account
- Сервер запуститься лише з MFA
- Запит буде відхилено, якщо в організації більше 10 акаунтів
= SCP не обмежують management account. Саме тому в ньому не тримають робочих ресурсів і суворо обмежують доступ до нього.

? Користувачу в member-акаунті IAM-політика дозволяє s3:*, а SCP на його OU дозволяє лише ec2:*. Що він може робити?
- Усе в S3 і EC2
- Лише S3
- Лише EC2
+ Нічого з S3 і EC2 — потрібен дозвіл і в SCP, і в IAM
= Ефективні права — перетин. S3 не дозволено SCP, EC2 не дозволено IAM-політикою. Жодна дія не має дозволу з обох боків.

? Компанія хоче за кілька годин налаштувати багатоакаунтне середовище за кращими практиками AWS: централізовані журнали, акаунти для аудиту, готові guardrails і фабрику нових акаунтів. Що обрати?
- Вручну створити акаунти й SCP в AWS Organizations
+ AWS Control Tower
- AWS Service Catalog
- AWS Config conformance packs
= Control Tower автоматизує створення landing zone: Organizations, акаунти Log Archive і Audit, CloudTrail і Config, Identity Center, Account Factory і набір preventive/detective/proactive controls.

? Мережева команда хоче керувати однією VPC, а команди застосунків в інших акаунтах — запускати в її підмережах свої сервери. Що використати?
- VPC peering між усіма акаунтами
+ VPC sharing через AWS Resource Access Manager
- Окрему копію VPC в кожному акаунті
- Direct Connect Gateway
= AWS RAM дозволяє поділитися підмережами VPC з іншими акаунтами організації. Кожен акаунт керує своїми серверами, а мережею — власник VPC.

? Потрібно, щоб bucket S3 був доступний усім акаунтам організації, включно з тими, що з'являться в майбутньому, без редагування політики щоразу. Як це зробити?
- Перелічити в bucket policy номери всіх акаунтів
+ Використати в bucket policy умову aws:PrincipalOrgID з ідентифікатором організації
- Зробити bucket публічним
- Створити IAM-користувача для кожного акаунта
= Умова aws:PrincipalOrgID дозволяє доступ будь-якому principal з вказаної організації. Нові акаунти отримують доступ автоматично.

? Які твердження про SCP правильні? (Оберіть 2)
+ SCP обмежують дозволи навіть root user member-акаунта
- SCP надають користувачам дозволи, яких немає в IAM-політиках
+ SCP не впливають на management account
- SCP застосовуються до користувачів Cognito
- SCP можна прикріпити до окремого IAM-користувача
= SCP діють на всіх IAM-principal-ів у member-акаунтах, включно з root user, не діють на management account і прикріплюються до Root, OU або акаунтів — не до окремих користувачів. Прав вони не надають.
:::
