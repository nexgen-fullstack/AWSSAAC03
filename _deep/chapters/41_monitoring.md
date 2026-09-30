---
id: monitoring
module: Моніторинг, надійність і гроші
title: Моніторинг і керування — CloudWatch, CloudTrail, Config, X-Ray, Systems Manager, CloudFormation
short: CloudWatch, CloudTrail, Config
emoji: 🔭
domains: resilient, secure, performance
svc: cloudwatch, cloudtrail, config, xray, ssm, cloudformation, servicecatalog, trustedadvisor, health, licensemanager, grafana
---
> 🎬 **Історія Хмаринки.** Ніч «чорної п'ятниці». Сайт гальмує вже годину, а Тарас дізнається про це з гнівних коментарів в Instagram. Уранці — нові загадки: хтось **видалив правило** в Security Group — хто і коли? Один bucket раптом став **публічним** — як ловити таке автоматично? Оформлення замовлення триває 6 секунд — **де саме** гальмує: в API, базі чи платіжному сервісі? І як зайти на сервер, не відкриваючи SSH всьому інтернету? Цей розділ — про **очі, пам'ять і руки** архітектора.

> 🖼️ **Образ.** **CloudWatch** — приладова панель автомобіля: спідометр (метрики), бортовий журнал (логи) і лампочки, що спалахують при небезпеці (аларми). **CloudTrail** — відеореєстратор охорони: записує, **хто** зайшов і **що зробив**. **Config** — фотоархів кожної кімнати з інспектором, що звіряє стан із правилами. **X-Ray** — рентген, що показує шлях запиту крізь сервіси. **Systems Manager** — пульт керування автопарком серверів. **CloudFormation** — креслення будинку: за ним звести такий самий у будь-якому місті.

## Три запитання — три сервіси {#three}

Найчастіша плутанина на іспиті — CloudWatch, CloudTrail і Config. Розрізняй їх за запитанням:

| Запитання | Сервіс | Приклад |
|---|---|---|
| **Що відбувається** з ресурсами зараз, як вони працюють? | **CloudWatch** | CPU 95%, 500 помилок за хвилину, у логах «ERROR» |
| **Хто, що і коли зробив** через API? | **CloudTrail** | Користувач taras видалив правило SG о 02:14 з IP 93.x.x.x |
| **Яка конфігурація** ресурсу була і чи відповідає правилам? | **Config** | Bucket став публічним о 02:15; правило «S3 без публічного доступу» — NON_COMPLIANT |

:::mnemo 🧠 Watch — Trail — Config
**Cloud*Watch*** — **дивиться** на роботу (метрики, логи). **Cloud*Trail*** — **слід**, який лишає кожна дія людини чи сервісу. ***Config*** — **конфігурація** та її історія. «Хто видалив?» → Trail. «Чому повільно?» → Watch. «Що змінилося в налаштуваннях і чи це за правилами?» → Config.
:::

## CloudWatch Metrics: цифри роботи {#metrics}

**Метрика** — ряд чисел у часі: `CPUUtilization` сервера, `Latency` балансувальника, `ConsumedReadCapacityUnits` таблиці DynamoDB. Метрики згруповані в **простори імен** (`AWS/EC2`, `AWS/ApplicationELB`) і мають **виміри** (dimensions) — наприклад, `InstanceId`.

- **EC2 за замовчуванням** надсилає метрики **кожні 5 хвилин** (basic monitoring, безкоштовно); **detailed monitoring** — **кожну хвилину** (платно). Для швидкого реагування Auto Scaling вмикай detailed.
- ⚠️ **Пам'яті (RAM) і заповненості диска серед стандартних метрик EC2 немає**: гіпервізор бачить процесор, мережу і дискові операції, але не бачить, що відбувається всередині ОС. Для них встанови **CloudWatch agent** — він надсилає пам'ять, диск, процеси і логи.
- **Власні метрики** (custom) — з коду через `PutMetricData`: «замовлень за хвилину», «товарів у кошиках». **High-resolution** — з кроком до **1 секунди**.
- **Зберігання:** до **15 місяців** зі зменшенням деталізації: хвилинні точки — 15 днів, 5-хвилинні — 63 дні, годинні — 455 днів.
- **Metric Streams** — безперервний потік метрик через Firehose у S3 чи сторонні системи (Datadog, Splunk).

## CloudWatch Alarms: лампочки на панелі {#alarms}

**Аларм** стежить за метрикою і має три стани: **OK**, **ALARM**, **INSUFFICIENT_DATA**. Умова: «середній CPU > 80% протягом **3 з 5** періодів по 1 хвилині» (datapoints to alarm) — так аларм не спрацьовує на короткі сплески.

Що аларм уміє робити сам:

- надіслати сповіщення в **SNS** (пошта, SMS, Lambda, Slack через Chatbot);
- запустити **політику Auto Scaling** ([розділ 23](#ch/autoscaling));
- **дії EC2:** stop, terminate, reboot і **recover** — перезапустити сервер на **іншому хості** з тим самим ID, приватною IP, Elastic IP і метаданими (при збої `StatusCheckFailed_System`);
- викликати **Lambda** або створити запис в OpsCenter Systems Manager.

Ще два інструменти проти «шуму»:

- **Composite alarms** — поєднують аларми логікою AND/OR: «будити Тараса, лише якщо **і** CPU високий, **і** зросли помилки 5xx».
- **Anomaly detection** — ML будує «коридор нормальних значень» з урахуванням добових і тижневих циклів; аларм спрацьовує, коли метрика виходить за коридор (замість фіксованого порогу).

## CloudWatch Logs: бортовий журнал {#logs}

- **Log groups** (зазвичай одна на застосунок) → **log streams** (по одному на сервер чи контейнер) → записи.
- **Джерела:** CloudWatch agent (EC2 і власні сервери), **Lambda**, ECS і EKS, API Gateway, **VPC Flow Logs**, Route 53, CloudTrail, RDS.
- **Зберігання:** за замовчуванням — **назавжди** (платиш за кожен гігабайт роками!). Задавай **retention** — від 1 дня до 10 років. Шифрування KMS. Клас **Infrequent Access** — дешевший для рідко переглянутих логів.
- **Metric filters** — перетворюють рядки логів на метрику: кількість «ERROR» за хвилину → аларм → SNS. Класика іспиту.
- **Logs Insights** — інтерактивні запити до логів мовою запитів: «топ-10 найповільніших запитів за годину».
- **Subscription filters** — потік логів **у реальному часі** в Lambda, Kinesis Data Streams, Firehose або OpenSearch (зокрема централізовано в інший акаунт).
- **Експорт у S3** — пакетно, не в реальному часі; для аналізу в Athena. **Live Tail** — перегляд логів наживо. **Data protection** — маскування персональних даних у логах.

## Ще інструменти спостереження {#observability}

- **Dashboards** — власні панелі з графіками, зокрема з кількох регіонів і акаунтів.
- **Synthetics canaries** — скрипти, що кожні кілька хвилин «ходять» сайтом як покупець (відкрити каталог, покласти в кошик) і ловлять поломки **раніше за клієнтів**.
- **RUM** (real user monitoring) — швидкість сайту в браузерах справжніх відвідувачів.
- **Application Signals** — моніторинг застосунків (APM): затримки, помилки, SLO; **Container Insights** і **Lambda Insights** — детальні метрики контейнерів і функцій; **Contributor Insights** — «хто генерує найбільше запитів чи помилок».
- **Amazon Managed Service for Prometheus** і **Amazon Managed Grafana** — керовані Prometheus (метрики контейнерів, зокрема EKS) і Grafana (дашборди) для команд, що звикли до цих open-source-інструментів.

## AWS X-Ray: рентген запиту {#xray}

У монолітному застосунку повільний запит видно в одному лозі. У Хмаринці замовлення проходить **API Gateway → Lambda → ECS-сервіс оплати → DynamoDB → SQS**. **AWS X-Ray** збирає **трасу** (trace) кожного запиту: скільки часу він провів у кожному сервісі (**segments**, **subsegments**), де сталася помилка, і малює **карту сервісів** (service map). Частина запитів вибирається для трасування (**sampling**), щоб не платити за все.

- Інтеграції: **Lambda** (active tracing — прапорець), **API Gateway**, ECS, EKS, Elastic Beanstalk, SNS, SQS.
- 🆕 **SDK і демон X-Ray** перейшли в режим підтримки (maintenance) **25.02.2026**, кінець підтримки — **25.02.2027**. Сьогодні застосунки інструментують через **OpenTelemetry** (AWS Distro for OpenTelemetry або CloudWatch agent), а траси так само потрапляють у X-Ray і CloudWatch (Transaction Search, Application Signals).

## AWS CloudTrail: хто, що, коли {#cloudtrail}

**AWS CloudTrail** записує **виклики API** в акаунті — з консолі, CLI, SDK і від самих сервісів AWS: **хто** (користувач, роль), **що** (`DeleteSecurityGroupRule`), **коли**, **звідки** (IP, консоль чи CLI), з якими параметрами і чи вдалося.

- **Event history** — **90 днів** management events, безкоштовно й автоматично, без налаштувань.
- **Trail** — постійний запис у **S3** (для років зберігання) і за бажанням у **CloudWatch Logs** (для metric filters і алармів). Новий trail за замовчуванням — **для всіх регіонів**. **Organization trail** — один trail для **всіх акаунтів** організації (зазвичай у окремий акаунт Log Archive).
- **Типи подій:**
  - **management events** — керування ресурсами (створити сервер, змінити SG) — увімкнені за замовчуванням;
  - **data events** — операції з даними: **S3 GetObject/PutObject**, виклики Lambda, операції з елементами DynamoDB — **вимкнені** за замовчуванням, платні, бо їх дуже багато;
  - **Insights events** — незвичайна активність: раптом у 50 разів більше `TerminateInstances`, ніж зазвичай.
- **Захист журналу:** **log file integrity validation** (файли-дайджести SHA-256 доводять, що журнал не змінювали й не видаляли), шифрування **SSE-KMS**, bucket з **Object Lock** в окремому акаунті.
- **Затримка:** події потрапляють у журнал зазвичай протягом **~5 хвилин**. Щоб реагувати миттєво, використовуй правило **EventBridge** на подію CloudTrail: «хтось викликав `StopLogging` чи `DeleteBucket`» → SNS або Lambda.
- 🆕 **CloudTrail Lake** (SQL-запити до подій) **закритий для нових клієнтів з 31.05.2026**. Замість нього аналізують журнали в **CloudWatch** або запитами **Athena** до trail у S3 ([розділ 39](#ch/analytics)).

## AWS Config: стан і правила {#config}

**AWS Config** постійно записує **конфігурацію ресурсів** (configuration items) і **історію змін**: як виглядала Security Group учора о 14:00, які ресурси з нею пов'язані і хто її змінив (посилання на подію CloudTrail).

- **Config rules** — перевірки відповідності: **сотні готових** (managed) правил — «усі томи EBS зашифровані», «S3 без публічного читання», «SSH не відкритий для 0.0.0.0/0», «CloudTrail увімкнений» — і власні (Lambda або мова Guard). Перевірка — **при кожній зміні** ресурсу або **періодично**.
- **Remediation** — **автоматичне виправлення** через документи **Systems Manager Automation**: bucket став публічним → Config позначає NON_COMPLIANT → автоматично вмикається Block Public Access.
- **Conformance packs** — набори правил і виправлень (наприклад, під CIS чи PCI DSS), що розгортаються на всю організацію.
- **Aggregator** — зведений стан відповідності **всіх акаунтів і регіонів** в одному місці.
- ⚠️ Config — **детективний** контроль: він **знаходить і виправляє**, але **не забороняє** дію наперед. Заборонити — це **SCP** та IAM ([розділ 10](#ch/organizations/scp)).

## AWS Systems Manager: пульт автопарку {#ssm}

Щоб сервер став «керованим», на ньому має працювати **SSM Agent** (вже встановлений в Amazon Linux і Windows AMI) і бути **роль IAM** з політикою `AmazonSSMManagedInstanceCore`. Власні сервери в офісі теж можна підключити (hybrid activations).

| Можливість | Що робить | Типове питання |
|---|---|---|
| **Session Manager** | Командний рядок у браузері чи CLI **без SSH**: без відкритого порту 22, без bastion, без ключів; доступ за IAM; сесії пишуться в S3 і CloudWatch Logs | Безпечний доступ до серверів у приватній підмережі з журналом дій |
| **Run Command** | Виконати команду чи скрипт на сотнях серверів одночасно | Оновити конфіг на всіх серверах без входу на кожен |
| **Patch Manager** | Оновлення ОС за **базовими лініями** (patch baselines) у **вікна обслуговування** | Автоматичні патчі за розкладом із звітом відповідності |
| **Automation** | Runbooks — сценарії дій (перезапуск, створення AMI, виправлення для Config) | Автовиправлення порушень |
| **State Manager, Inventory** | Бажаний стан (агент завжди встановлений), перелік ПЗ на серверах | — |
| **Parameter Store** | Налаштування й секрети ([розділ 11](#ch/encryption/secrets)) | — |

## Інфраструктура як код: CloudFormation {#cloudformation}

**AWS CloudFormation** створює інфраструктуру за **шаблоном** (YAML або JSON). Шаблон описує **Resources** (обов'язково) і за бажанням **Parameters**, **Mappings**, **Conditions**, **Outputs**. Розгорнутий шаблон — це **стек** (stack).

```yaml
Resources:
  OrdersQueue:
    Type: AWS::SQS::Queue
    Properties:
      VisibilityTimeout: 60
  PhotosBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Retain      # при видаленні стека bucket з фото залишиться
Outputs:
  QueueUrl:
    Value: !Ref OrdersQueue
```

- **Однаково щоразу:** dev, test і prod — з одного шаблону; DR-регіон піднімається за хвилини тим самим шаблоном.
- **Change sets** — попередній перегляд змін перед застосуванням. **Rollback** — при помилці стек повертається до попереднього стану. **Drift detection** — хтось змінив ресурс руками в обхід шаблону.
- **DeletionPolicy** (`Retain`, `Snapshot`) — не втратити дані при видаленні стека. **Stack policy** — заборона змінювати критичні ресурси.
- **StackSets** — розгорнути стек **у багатьох акаунтах і регіонах** однією дією; з Organizations — **автоматично в кожен новий акаунт**.
- **AWS CDK** — інфраструктура звичайною мовою програмування (TypeScript, Python), що перетворюється на CloudFormation. **AWS SAM** — скорочені шаблони для serverless. **Infrastructure Composer** — візуальний редактор.

## Порядок і поради: Service Catalog, Trusted Advisor, Health, License Manager {#governance}

- **AWS Service Catalog** — «меню дозволених страв»: адміністратори публікують **затверджені продукти** (шаблони CloudFormation) у портфелях, а команди запускають їх **самі**, навіть без широких прав IAM (запуск іде від ролі продукту — launch constraint).
- **AWS Trusted Advisor** — автоматичний аудитор за категоріями: **вартість, продуктивність, безпека, стійкість, ліміти сервісів**, операційна досконалість. Безкоштовно — базові перевірки безпеки і лімітів; повний набір — з платними планами підтримки (у 2026 — **Business Support+** і вищі). Для лімітів є також **Service Quotas**: перегляд квот, запит на збільшення і аларм при наближенні.
- **AWS Health Dashboard** — події AWS, що зачіпають **саме твої** ресурси: планове обслуговування (наприклад, виведення хоста з експлуатації), збої в регіоні. Події йдуть у **EventBridge** → автоматична реакція.
- **AWS License Manager** — облік власних ліцензій (**BYOL**: Windows Server, SQL Server, Oracle) і правила, що **не дадуть** запустити більше, ніж куплено; керування Dedicated Hosts.

## Моніторинг Хмаринки {#design}

<figure class="diagram" data-caption="Спостереження і контроль у Хмаринці">
<div class="tiers">
<div class="tier"><span class="tl">Бачити</span><span>Метрики ALB, ECS, Aurora + <b>CloudWatch agent</b> (пам'ять, диск) → дашборд «Чорна п'ятниця»; <b>Synthetics</b> кожні 5 хв оформлює тестове замовлення</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Реагувати</span><span><b>Composite alarm</b> (p99 затримки ↑ і 5xx ↑) → <b>SNS</b> → телефон Тараса; target tracking → Auto Scaling</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Шукати причину</span><span><b>Logs Insights</b> по логах; <b>X-Ray</b>: 5 з 6 секунд — очікування платіжного API</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Аудит</span><span><b>Organization trail</b> → S3 в акаунті Log Archive (Object Lock); <b>EventBridge</b>: StopLogging, зміни SG → SNS</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Відповідність</span><span><b>Config rules</b>: EBS зашифровані, S3 не публічні, SSH закритий → автовиправлення через <b>SSM Automation</b></span></div>
</div>
<figcaption>Відтепер про гальмування Тарас дізнається від аларму за хвилину, а не з Instagram за годину. Доступ до серверів — лише через Session Manager, порт 22 закритий.</figcaption>
</figure>

## Що обрати {#choose}

| Потреба | Рішення |
|---|---|
| Пам'ять і диск EC2 | **CloudWatch agent** |
| Сповіщення, коли в логах з'являється «ERROR» | **Metric filter + alarm + SNS** |
| Логи в реальному часі в інший сервіс чи акаунт | **Subscription filter** (Lambda, Kinesis, Firehose) |
| Хто видалив чи змінив ресурс | **CloudTrail** |
| Журнал API всіх акаунтів організації | **Organization trail** |
| Довести, що журнал не підробили | **Log file integrity validation** |
| Хто читав об'єкти в S3 | **CloudTrail data events** (або S3 server access logs) |
| Миттєва реакція на небезпечний виклик API | **EventBridge rule** на подію CloudTrail |
| Відповідність налаштувань правилам + автовиправлення | **Config rules + remediation (SSM Automation)** |
| Історія конфігурації ресурсу | **Config** |
| Де гальмує запит між мікросервісами | **X-Ray** |
| Доступ до сервера без SSH і bastion | **Session Manager** |
| Патчі за розкладом | **Patch Manager** |
| Однакова інфраструктура в багатьох акаунтах і регіонах | **CloudFormation StackSets** |
| Команди запускають лише затверджені шаблони | **Service Catalog** |
| Перевірка лімітів і кращих практик | **Trusted Advisor / Service Quotas** |
| Реакція на планове обслуговування AWS | **Health Dashboard + EventBridge** |

:::lab 🧪 Спробуй у справжньому AWS: помилки в логах → аларм → лист
**Вартість:** у межах безкоштовного рівня (10 алармів, 5 GB логів). **Час:** 20 хвилин.
1. **CloudShell** — створи групу логів з retention, фільтр метрики і тему SNS (заміни email):
```bash
aws logs create-log-group --log-group-name /khmarynka/app
aws logs put-retention-policy --log-group-name /khmarynka/app --retention-in-days 7
aws logs create-log-stream --log-group-name /khmarynka/app --log-stream-name web-1
aws logs put-metric-filter --log-group-name /khmarynka/app --filter-name errors \
  --filter-pattern "ERROR" \
  --metric-transformations metricName=AppErrors,metricNamespace=Khmarynka,metricValue=1,defaultValue=0
TOPIC=$(aws sns create-topic --name khmarynka-alerts --query TopicArn --output text)
aws sns subscribe --topic-arn $TOPIC --protocol email --notification-endpoint you@example.com
```
2. Підтверди підписку в листі від AWS. Створи аларм: 3 і більше помилок за хвилину:
```bash
aws cloudwatch put-metric-alarm --alarm-name khmarynka-errors \
  --namespace Khmarynka --metric-name AppErrors --statistic Sum --period 60 \
  --evaluation-periods 1 --threshold 3 --comparison-operator GreaterThanOrEqualToThreshold \
  --treat-missing-data notBreaching --alarm-actions $TOPIC
```
3. «Зламай» застосунок — запиши в лог три помилки:
```bash
NOW=$(date +%s%3N)
aws logs put-log-events --log-group-name /khmarynka/app --log-stream-name web-1 --log-events \
  timestamp=$NOW,message="ERROR payment timeout" timestamp=$NOW,message="ERROR payment timeout" \
  timestamp=$NOW,message="ERROR db connection refused"
```
За 1–3 хвилини аларм перейде в **ALARM** (CloudWatch → Alarms), і прийде лист.
4. **CloudTrail → Event history** → фільтр Event name = `PutMetricAlarm`: ти бачиш, **хто** створив аларм, коли і з якої IP.
**Прибери за собою:**
```bash
aws cloudwatch delete-alarms --alarm-names khmarynka-errors
aws logs delete-log-group --log-group-name /khmarynka/app
aws sns delete-topic --topic-arn $TOPIC
```
:::

#### 💡 Запам'ятай

- **CloudWatch** — що відбувається (метрики, логи, аларми); **CloudTrail** — хто що зробив (API); **Config** — конфігурація, історія і правила.
- EC2: метрики кожні **5 хв** (detailed — 1 хв); **RAM і диск — лише через CloudWatch agent**; власні метрики — до 1 с.
- Аларм: SNS, Auto Scaling, **EC2 stop/terminate/reboot/recover**, Lambda; **composite alarms** проти шуму; **anomaly detection**.
- Логи: **retention** (за замовчуванням — назавжди), **metric filter → alarm**, **Logs Insights**, **subscription filters** у реальному часі, експорт у S3 — пакетно.
- **X-Ray** — траси й карта сервісів; інструментування — через **OpenTelemetry** (SDK X-Ray у maintenance з 2026).
- **CloudTrail:** 90 днів event history; trail у S3 (+ CloudWatch Logs); **organization trail**; data events — окремо й платно; **integrity validation**; ~5 хв затримки → для миттєвої реакції **EventBridge**.
- **Config:** правила, **remediation через SSM Automation**, conformance packs, aggregator; **виявляє, а не забороняє**.
- **Systems Manager:** **Session Manager** (без SSH), Run Command, **Patch Manager**, Automation, Parameter Store.
- **CloudFormation:** шаблони, change sets, drift, DeletionPolicy, **StackSets** (багато акаунтів і регіонів); CDK, SAM.
- **Service Catalog** — затверджені продукти; **Trusted Advisor** — поради й ліміти; **Health Dashboard + EventBridge** — події AWS; **License Manager** — BYOL.

#### 🎯 Як питають на іспиті

- Хто видалив ресурс чи змінив налаштування → **CloudTrail**
- Моніторити використання пам'яті EC2 → **CloudWatch agent**
- Сповіщення при появі певного тексту в логах → **metric filter + CloudWatch alarm + SNS**
- Автоматично перевіряти, що всі томи EBS зашифровані, і виправляти порушення → **Config rule + remediation**
- Доступ до інстансів у приватній підмережі без bastion і відкритого порту 22 → **Systems Manager Session Manager**
- Знайти вузьке місце в запитах між мікросервісами → **X-Ray**
- Однаковий набір ресурсів у кожному акаунті організації → **CloudFormation StackSets**
- Швидко відтворити інфраструктуру в DR-регіоні → **CloudFormation-шаблон**
- Централізований аудит API всіх акаунтів → **organization trail у S3 окремого акаунта**
- Перевірити, чи журнал CloudTrail не змінювали → **log file integrity validation**
- Автоматично відновлювати EC2 при збої хоста → **CloudWatch alarm з дією recover**
- Зменшити кількість хибних тривог → **composite alarms**
- Реагувати на планове обслуговування EC2 від AWS → **AWS Health + EventBridge**
- Команди запускають лише затверджені конфігурації → **Service Catalog**

#### ⚠️ Пастки

- CloudTrail **не показує** CPU чи помилки застосунку — це CloudWatch. CloudWatch **не каже**, хто видалив ресурс — це CloudTrail.
- **Config не забороняє** дії — лише виявляє і виправляє. Заборона — SCP та IAM.
- Логи CloudWatch за замовчуванням **зберігаються назавжди** — налаштовуй retention.
- **Data events** CloudTrail (читання об'єктів S3) **не записуються** за замовчуванням.
- Дія **recover** не зберігає дані **instance store**.

## ✅ Перевір себе

:::quiz
? Хтось видалив правило Security Group у production-акаунті минулої ночі. Як дізнатися, хто це зробив і з якої IP-адреси?
+ Переглянути події в AWS CloudTrail
- Переглянути метрики в Amazon CloudWatch
- Перевірити VPC Flow Logs
- Запустити перевірку AWS Trusted Advisor
= CloudTrail записує кожен виклик API: хто, що, коли і звідки. Метрики CloudWatch і Flow Logs не містять інформації про дії користувачів з налаштуваннями.

? Архітектору потрібно відстежувати використання оперативної пам'яті на інстансах EC2 і отримувати сповіщення, коли воно перевищить 90%. Що зробити?
+ Встановити CloudWatch agent, що надсилає метрику пам'яті, і створити аларм
- Увімкнути detailed monitoring для EC2
- Створити аларм на стандартну метрику MemoryUtilization в AWS/EC2
- Увімкнути AWS Config для інстансів
= Пам'ять — метрика всередині ОС, гіпервізор її не бачить. CloudWatch agent надсилає її як власну метрику. Detailed monitoring лише частішає стандартні метрики, а метрики пам'яті серед них немає.

? Компанія має гарантувати, що всі нові томи EBS зашифровані, а про порушення має знати служба безпеки й автоматично їх виправляти. Що обрати?
- AWS CloudTrail з organization trail
+ AWS Config з managed rule і автоматичним remediation
- Amazon CloudWatch з metric filter
- Amazon Inspector
= Config rules перевіряють відповідність налаштувань правилам при кожній зміні, а remediation через SSM Automation автоматично виправляє порушення.

? Адміністраторам потрібен доступ до командного рядка інстансів у приватних підмережах без bastion host і без відкритого порту 22, з журналом усіх сесій. Що використати?
+ AWS Systems Manager Session Manager
- EC2 Instance Connect з публічними IP
- Bastion host з обмеженою Security Group
- Site-to-Site VPN
= Session Manager дає доступ через SSM Agent без вхідних портів і ключів SSH, керується IAM і записує сесії в S3 і CloudWatch Logs.

? Застосунок пише логи в CloudWatch Logs. Команда хоче отримувати лист, коли за 5 хвилин з'являється понад 10 рядків з текстом «PaymentFailed». Яке рішення найпростіше?
+ Metric filter на групу логів, аларм на отриману метрику і тема SNS з підпискою email
- Щогодинний експорт логів у S3 і запит Athena
- Lambda, що щохвилини читає всі логи
- AWS Config rule для групи логів
= Metric filter перетворює збіги в логах на метрику, аларм стежить за порогом і надсилає сповіщення через SNS — без коду і серверів.

? Запит оформлення замовлення проходить через API Gateway, три функції Lambda і сервіс на ECS. Іноді він триває 8 секунд. Як знайти, який компонент гальмує?
- Переглянути CloudTrail
+ Увімкнути трасування AWS X-Ray (через OpenTelemetry) і переглянути service map і траси
- Увімкнути VPC Flow Logs
- Перевірити AWS Config timeline
= X-Ray показує трасу запиту крізь усі сервіси з часом у кожному сегменті, тож вузьке місце видно одразу.

? Компанія хоче розгорнути однаковий набір ролей IAM і правил Config у кожному з 60 акаунтів організації в трьох регіонах, а також автоматично в кожному новому акаунті. Що обрати?
+ AWS CloudFormation StackSets з інтеграцією AWS Organizations
- Окремий стек CloudFormation, запущений вручну в кожному акаунті
- AWS Service Catalog у кожному акаунті
- AWS Systems Manager Run Command
= StackSets розгортають стек у багатьох акаунтах і регіонах однією операцією, а з Organizations — автоматично в нові акаунти.

? Аудитор вимагає доказу, що файли журналу CloudTrail не змінювали й не видаляли після доставки в S3. Що увімкнути?
- Версіонування S3
+ Перевірку цілісності файлів журналу CloudTrail (log file integrity validation)
- CloudTrail Insights
- AWS Config rule для bucket
= Integrity validation створює дайджест-файли з хешами SHA-256, за якими можна довести, що журнал не змінено і не видалено.

? Які дії може виконати CloudWatch alarm напряму? (Оберіть 2)
+ Відновити (recover) інстанс EC2 на іншому хості
+ Надіслати сповіщення в тему SNS
- Змінити правило Security Group
- Зробити знімок бази RDS
- Відкотити стек CloudFormation
= Аларм може надіслати сповіщення в SNS, запустити політику Auto Scaling, виконати дії EC2 (stop, terminate, reboot, recover), викликати Lambda. Інші дії роблять через SNS/Lambda або EventBridge.
:::
