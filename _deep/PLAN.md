# AWS SAA-C03 з нуля — глибоке навчання: план і правила

Окремий сайт-підручник: `docs/deep/` → https://nexgen-fullstack.github.io/AWSSAAC03/deep/
(окремий застосунок на телефоні, свій офлайн-режим, свій PDF). Коротка версія курсу і шпаргалка — `docs/` (версія 2).

## Збірка

```bash
python _deep/build.py            # сайт + іконки + PDF-підручник
python _deep/build.py --no-pdf   # лише HTML
```

Джерела:

- `_deep/chapters/NN_id.md` — розділи (порядок = номер файлу).
- `_deep/glossary.md` — основи IT для підказок (формат як у `_source/services.md`, категорія `it`).
- `_source/services.md` — довідник сервісів AWS (спільний з версією 2).
- `_source/questions.md` + `_deep/exam2.md` (якщо є) — пробний іспит англійською з перекладом.

## Формат розділу

```
---
id: vpc
module: Мережа
title: VPC з нуля: адреси, підмережі, маршрути, NAT
emoji: 🏘️
minutes: 35
domains: secure, resilient, performance, cost
svc: vpc, subnet, cidr, igw, natgw
---
> 🎬 **Історія Хмаринки.** …        — сюжетна проблема (callout story)
> 🖼️ **Образ.** …                     — образ для запам'ятовування
## Заголовок {#slug}                  — підрозділ (потрапляє в зміст розділу)
:::lab 🧪 Спробуй у справжньому AWS: …  — практика в консолі, з вартістю і прибиранням
:::deep 🔬 Глибше: …                  — розгортний блок для допитливих
:::note / :::calc / :::mnemo / :::example — інші рамки
#### 💡 Запам'ятай | 🎯 Як питають на іспиті (ситуація → **відповідь**) | ⚠️ Пастки
:::quiz                                — питання «Перевір себе»:
? питання
- неправильний варіант
+ правильний варіант (кілька «+» = кілька правильних)
= пояснення
:::
```

Схеми — HTML-блоки `<figure class="diagram" data-caption="…">` без порожніх рядків усередині
(класи `flow`, `tiers`, `dg-box`, `dg-node`, SVG з класом `svg-dg`, viewBox ~400 завширшки).

## Стиль

- Звертання на «ти», теперішній або майбутній час: без «ти зробив/зробила» (рід читача невідомий).
- Від простого до складного: історія → образ → як працює → як обирати → практика → підсумок → питання.
- Терміни AWS — англійською (як на іспиті), пояснення — українською.
- Цифри — за документацією AWS станом на вересень 2026 (див. `_source/sheet/09_numbers.md`, розділ 28 шпаргалки).
- Практика «Спробуй у справжньому AWS»: вартість, час і обов'язкове прибирання наприкінці.

## Наскрізний приклад — «Хмаринка»

Український інтернет-магазин подарунків і товарів для дому зі Львова. Олена — засновниця,
Тарас — розробник, бухгалтерія і склад. Сайт і база жили на одному сервері в підсобці офісу;
у «чорну п'ятницю» все впало. Читач — новий архітектор рішень, який переносить Хмаринку в AWS.
Основний регіон — eu-central-1 (Франкфурт), резервний — eu-west-1 (Ірландія). Домен — khmarynka.ua.

## Розділи (46)

| № | id | Модуль | Тема |
|---|---|---|---|
| 1 | start | Старт з нуля | Як пройти курс і стати архітектором |
| 2 | it-computers | Старт з нуля | Основи IT (1): комп'ютер, сервер, ОС, віртуалізація |
| 3 | it-networks | Старт з нуля | Основи IT (2): мережі, IP, порти, DNS, HTTPS |
| 4 | it-data | Старт з нуля | Основи IT (3): дані, бази, API, шифрування |
| 5 | cloud | Старт з нуля | Що таке хмара |
| 6 | global | Старт з нуля | Глобальна інфраструктура AWS |
| 7 | account | Старт з нуля | Акаунт, безкоштовний план, бюджет, Well-Architected |
| 8 | iam | Безпека і доступ | IAM: користувачі, групи, політики |
| 9 | roles | Безпека і доступ | Ролі, STS, федерація, Identity Center, Cognito |
| 10 | organizations | Безпека і доступ | Organizations, SCP, Control Tower |
| 11 | encryption | Безпека і доступ | KMS, CloudHSM, ACM, секрети |
| 12 | protection | Безпека і доступ | WAF, Shield, GuardDuty та інші |
| 13 | vpc | Мережа | VPC: CIDR, підмережі, маршрути, NAT |
| 14 | vpc-security | Мережа | Security Groups, NACL, доступ до серверів |
| 15 | vpc-connect | Мережа | Endpoints, PrivateLink, Peering, Transit Gateway |
| 16 | hybrid-network | Мережа | VPN, Direct Connect, гібридний DNS |
| 17 | route53 | Мережа | Route 53 |
| 18 | edge | Мережа | CloudFront і Global Accelerator |
| 19 | ec2 | Обчислення | EC2 |
| 20 | ec2-pricing | Обчислення | Тарифи EC2 |
| 21 | ec2-disks | Обчислення | EBS, instance store, снапшоти (3 схеми) |
| 22 | elb | Обчислення | ALB, NLB, GWLB |
| 23 | autoscaling | Обчислення | Auto Scaling |
| 24 | containers | Обчислення | Docker, ECS, EKS, Fargate |
| 25 | lambda | Обчислення | Lambda |
| 26 | api-platforms | Обчислення | API Gateway, Beanstalk, Batch, Amplify |
| 27 | s3 | Сховища | S3: основи |
| 28 | s3-deep | Сховища | S3 глибше |
| 29 | files | Сховища | EFS і FSx |
| 30 | hybrid-storage | Сховища | Storage Gateway, DataSync, Transfer Family, Snow |
| 31 | sqs-sns | Інтеграція | SQS і SNS |
| 32 | events | Інтеграція | EventBridge, Step Functions, MQ, AppFlow |
| 33 | migration | Переїзд у хмару | 7R, MGN, DMS, SCT, план міграції |
| 34 | rds | Бази даних | Amazon RDS |
| 35 | aurora | Бази даних | Amazon Aurora |
| 36 | dynamodb | Бази даних | DynamoDB |
| 37 | cache-special | Бази даних | ElastiCache і спеціалізовані бази |
| 38 | streaming | Дані, аналітика й AI | Kinesis, Firehose, MSK, Flink |
| 39 | analytics | Дані, аналітика й AI | Data lake, Glue, Athena, Redshift, EMR |
| 40 | ai | Дані, аналітика й AI | AI і машинне навчання |
| 41 | monitoring | Моніторинг, надійність і гроші | CloudWatch, CloudTrail, Config, SSM, IaC |
| 42 | resilience | Моніторинг, надійність і гроші | HA і Disaster Recovery |
| 43 | cost | Моніторинг, надійність і гроші | Оптимізація витрат |
| 44 | final-architecture | Фінал | Велика архітектура «Хмаринки» |
| 45 | exam | Фінал | Розбір іспиту |
| 46 | next | Фінал | Що далі |
