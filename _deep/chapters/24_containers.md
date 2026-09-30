---
id: containers
module: Обчислення
title: Контейнери — Docker, Amazon ECS, Amazon EKS, AWS Fargate і ECR
short: ECS, EKS, Fargate
emoji: 📦
domains: resilient, performance, cost
svc: ecs, eks, fargate, ecr
---
> 🎬 **Історія Хмаринки.** У Тараса з'явилися двоє колег, і сайт почав ламатися по-новому: «у мене на ноутбуці працює, а на сервері — ні». Різні версії бібліотек, різні налаштування, золотий AMI перебудовується годину. А ще сайт поступово ділиться на частини: каталог, кошик, оплата, пошук — кожну хочеться оновлювати окремо, не зупиняючи решту. Тарас пропонує **контейнери**: упакувати кожну частину разом з усіма залежностями в образ, що працює однаково всюди, і доручити AWS запускати їх — бажано взагалі без серверів.

> 🖼️ **Образ.** Контейнер — стандартний морський контейнер. Що б у ньому не везли — іграшки чи холодильники, — кран, судно і вантажівка працюють з ним однаково. **Образ** — креслення і вміст контейнера. **ECR** — склад контейнерів у порту. **ECS** і **EKS** — диспетчери порту, що вирішують, на яке судно і скільки контейнерів вантажити (оркестрація). **Fargate** — ти навіть не бачиш суден: здаєш контейнер, а перевезення — повністю турбота порту.

## Контейнер за 3 хвилини {#basics}

Нагадування з [розділу 2](#ch/it-computers/virtualization): контейнер пакує **застосунок і його залежності**, але використовує спільне ядро ОС хоста — легкий, стартує за секунди, працює **однаково** всюди.

- **Dockerfile** — рецепт: «візьми базовий образ з Node.js, скопіюй код, встанови бібліотеки, запускай командою…».
- **Образ (image)** — результат збирання: незмінний, складається з шарів, має версію-тег (`shop-api:1.4.2`).
- **Реєстр (registry)** — сховище образів.
- **Контейнер** — запущений екземпляр образу.

```dockerfile
FROM public.ecr.aws/docker/library/node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .
EXPOSE 8080
CMD ["node", "server.js"]
```

Коли контейнерів десятки й сотні, потрібен **оркестратор**: запускати потрібну кількість копій, розкладати їх по серверах, перезапускати впалі, оновлювати версії без простою, підключати до балансувальника. В AWS таких два: **ECS** і **EKS**.

## Amazon ECR: реєстр образів {#ecr}

**Amazon Elastic Container Registry (ECR)** — приватний керований реєстр Docker/OCI-образів:

- доступ через **IAM** (і resource-based політики репозиторію);
- **сканування вразливостей** образів (розширене — через **Amazon Inspector**, постійне);
- **lifecycle policies** — автоматично видаляти старі образи («тримати останні 30»);
- **реплікація** між регіонами й акаунтами (для DR і мультирегіональних розгортань);
- **immutable tags** — заборонити перезапис тегу (`1.4.2` завжди означає той самий образ);
- **pull through cache** — кешувати образи з публічних реєстрів.

Публічні образи є в **ECR Public Gallery**.

## Amazon ECS {#ecs}

**Amazon Elastic Container Service (ECS)** — «рідний» оркестратор AWS: простіший за Kubernetes і глибоко інтегрований з сервісами AWS. Поняття:

- **Cluster** — логічна група, де працюють задачі.
- **Task definition** — опис застосунку (як docker-compose): образи, CPU і пам'ять, порти, змінні середовища, **секрети** (з Secrets Manager чи Parameter Store), журнали (у CloudWatch Logs), **IAM-ролі**.
- **Task** — запущений екземпляр task definition (один чи кілька контейнерів разом).
- **Service** — тримає **потрібну кількість** задач (desired count), перезапускає впалі, реєструє їх у **target group ALB/NLB**, робить **поступові оновлення** (rolling) або blue/green, масштабується (**Service Auto Scaling** за CPU, пам'яттю чи запитами на ціль).

Дві IAM-ролі, які плутають на іспиті:

- **Task role** — права **самого застосунку** в контейнері: читати S3, писати в DynamoDB.
- **Task execution role** — права **агента ECS**: завантажити образ з ECR, прочитати секрети для змінних середовища, писати логи в CloudWatch.

Мережа: у режимі **awsvpc** кожна задача отримує **власний мережевий інтерфейс** з приватною IP і **власну Security Group** — як окремий маленький сервер.

<figure class="diagram" data-caption="ECS: кластер, сервіси, задачі, контейнери">
<div class="dg-box"><div class="dg-label">📦 ECS cluster «khmarynka-prod»</div>
<div class="grid2">
<div class="dg-box dg-az"><div class="dg-label">Service «web» · desired 4</div><div class="dg-nodes"><span class="dg-node cmp">Task</span><span class="dg-node cmp">Task</span><span class="dg-node cmp">Task</span><span class="dg-node cmp">Task</span></div><small class="muted">за ALB, масштабування за запитами</small></div>
<div class="dg-box dg-az"><div class="dg-label">Service «api» · desired 3</div><div class="dg-nodes"><span class="dg-node cmp">Task</span><span class="dg-node cmp">Task</span><span class="dg-node cmp">Task</span></div><small class="muted">task role: DynamoDB, SQS</small></div>
<div class="dg-box dg-az"><div class="dg-label">Service «image-worker» · 0–20</div><div class="dg-nodes"><span class="dg-node cmp">Task (Fargate Spot)</span><span class="dg-node cmp">Task (Fargate Spot)</span></div><small class="muted">масштабування за чергою SQS</small></div>
<div class="dg-box dg-az"><div class="dg-label">Task definition «api:17»</div><small class="muted">образ ECR shop-api:1.4.2 · 0,5 vCPU · 1 GiB · порт 8080 · секрет DB_PASSWORD з Secrets Manager · логи → CloudWatch</small></div>
</div></div>
<figcaption>Service — «диспетчер», що стежить за кількістю задач. Task definition — «паспорт» застосунку з версією.</figcaption>
</figure>

### Де фізично працюють контейнери ECS: EC2 чи Fargate

| | **ECS на EC2** | **ECS на Fargate** |
|---|---|---|
| Сервери | Твої інстанси EC2 з агентом ECS (зазвичай в Auto Scaling group) | **Серверів не видно** — AWS виділяє ресурси під кожну задачу |
| Що ти керуєш | Тип серверів, їх кількість, патчі ОС, щільність розміщення | Лише CPU і пам'ять задачі |
| Оплата | За сервери EC2 (можна Savings Plans, Spot) | За vCPU і пам'ять задачі посекундно (Savings Plans, **Fargate Spot** до −70%) |
| Коли обирати | Велике стабільне навантаження, щільне «пакування» заради економії, GPU, особливі вимоги до хоста | **Мінімум операційної роботи**, змінне навантаження, швидкий старт, ізоляція задач |

**Capacity providers** дозволяють кластеру поєднувати джерела: наприклад, частина задач на Fargate, частина — на Fargate Spot чи EC2.

**ECS Anywhere** — запуск задач ECS на **власних серверах** у дата-центрі, з керуванням з AWS.

## Amazon EKS {#eks}

**Amazon Elastic Kubernetes Service (EKS)** — керований **Kubernetes**: AWS запускає і підтримує **control plane** (API-сервер, etcd) у кількох AZ, оновлює і латає його. Ти працюєш стандартними інструментами Kubernetes (`kubectl`, Helm).

Де працюють поди (data plane):

- **Managed node groups** — EC2-вузли, якими AWS допомагає керувати (оновлення, заміна);
- **Self-managed nodes** — повністю свої EC2;
- **Fargate** — поди без вузлів;
- **EKS Auto Mode** — AWS сам обирає, запускає, масштабує й оновлює вузли; популярний автоскейлер вузлів **Karpenter**.

Права AWS для окремих подів — через **EKS Pod Identity** або IAM-ролі для service accounts. Для власних дата-центрів — **EKS Anywhere** і **EKS Distro**.

**Коли EKS, а не ECS?** Компанія **вже** використовує Kubernetes, потрібна **переносимість** між хмарами й on-prem, потрібна екосистема Kubernetes (оператори, Helm-чарти, open-source інструменти). Якщо цього немає — ECS простіший і дешевший в обслуговуванні.

## AWS Fargate {#fargate}

**Fargate** — serverless-двигун для контейнерів, працює і з **ECS**, і з **EKS**:

- ніяких серверів: не треба обирати тип, латати ОС, масштабувати кластер;
- кожна задача ізольована в окремому мікро-VM;
- платиш за **запитані vCPU і пам'ять** посекундно, поки задача працює;
- **Fargate Spot** — для переривних задач зі знижкою.

## Що обрати для обчислень {#choose}

| Вимога | Вибір |
|---|---|
| Повний контроль над ОС, особливе ПЗ, ліцензії, GPU | **EC2** |
| Контейнери з мінімумом операційних зусиль | **ECS на Fargate** |
| Уже є Kubernetes, потрібна переносимість | **EKS** (з Fargate або Auto Mode для мінімуму зусиль) |
| Велике стабільне контейнерне навантаження, максимальна економія | **ECS/EKS на EC2** з Savings Plans і Spot |
| Короткі подієві задачі до 15 хвилин | **Lambda** ([розділ 25](#ch/lambda)) |
| Довгі пакетні задачі з чергами | **AWS Batch** ([розділ 26](#ch/api-platforms)) |
| Перенести застосунок у контейнери **без переписування** | Образ у **ECR** + **ECS/EKS на Fargate** |

## Рішення для Хмаринки {#design}

- Сайт розділено на сервіси `web`, `api`, `image-worker`; образи — в **ECR** з постійним скануванням і lifecycle policy.
- **ECS на Fargate** за ALB — Тарасу більше не треба латати сервери; ASG з [розділу 23](#ch/autoscaling) замінює **Service Auto Scaling**.
- Секрети — з **Secrets Manager** через task definition; права — через **task role**.
- `image-worker` — на **Fargate Spot**, масштабується за довжиною черги.
- Розгортання нових версій — поступове (rolling), з автоматичним відкатом при провалі health checks.
- Kubernetes не потрібен: немає ні досвіду, ні вимог до переносимості.

:::lab 🧪 Спробуй у справжньому AWS: контейнер на Fargate за 10 хвилин
**Вартість:** задача 0,25 vCPU / 0,5 GB на 15 хвилин — менше цента. **Час:** 20 хвилин.
1. **ECS → Clusters → Create cluster**: назва `khmarynka-lab`, інфраструктура — **AWS Fargate (serverless)**. Create.
2. **Task definitions → Create new**: назва `hello-web`, launch type **Fargate**, CPU `.25 vCPU`, Memory `.5 GB`. Контейнер: ім'я `web`, image URI `public.ecr.aws/nginx/nginx:latest`, port mapping **80**. Create.
3. Кластер → **Tasks → Run new task**: launch type Fargate, task definition `hello-web`. Networking: твоя VPC, **публічна** підмережа, **Public IP — Turned on**, Security Group з HTTP 80 з My IP. Create.
4. Коли задача в статусі **Running**, відкрий її → Configuration → **Public IP** — відкрий у браузері: вітальна сторінка nginx. Жодного сервера EC2 ти не створював.
5. Вкладка **Logs** задачі — журнали контейнера (якщо ввімкнено CloudWatch Logs у task definition).
6. Подумай: що додати, щоб таких задач завжди було 3 за балансувальником? (Відповідь: **ECS service** з desired count 3 і ALB.)
**Прибери за собою:** зупини задачу (**Stop**), видали кластер, деактивуй і видали task definition, видали Security Group і журнали в CloudWatch Logs.
:::

#### 💡 Запам'ятай

- Контейнер = застосунок + залежності в образі; однаково всюди, старт за секунди.
- **ECR** — приватний реєстр: IAM, сканування (Inspector), lifecycle, реплікація, immutable tags.
- **ECS:** cluster → **service** (кількість, ALB, оновлення, автомасштабування) → **task** → контейнери; **task definition** — опис.
- **Task role** — права застосунку; **task execution role** — права агента (ECR, секрети, логи).
- **ECS на EC2** — контроль і економія на великому стабільному навантаженні; **ECS на Fargate** — без серверів, мінімум роботи.
- **EKS** — керований Kubernetes: коли вже є K8s чи потрібна переносимість; вузли — managed node groups, Fargate, **Auto Mode**.
- **Fargate** — serverless-двигун для ECS і EKS; **Fargate Spot** — дешево для переривних задач.
- On-prem: **ECS Anywhere**, **EKS Anywhere**.

#### 🎯 Як питають на іспиті

- Запускати контейнери без керування серверами → **AWS Fargate (ECS або EKS)**
- Компанія вже використовує Kubernetes і хоче керований сервіс → **Amazon EKS**
- Контейнерам потрібен доступ до S3 з найменшими правами → **ECS task role**
- ECS не може завантажити образ з ECR або прочитати секрет для змінної середовища → **перевір task execution role**
- Перенести застосунок у контейнери без переписування коду → **образ у ECR + ECS/EKS на Fargate**
- Сканувати образи контейнерів на вразливості → **ECR scanning (Amazon Inspector)**
- Автоматично видаляти старі образи в реєстрі → **ECR lifecycle policy**
- Кілька контейнерів на одному сервері за ALB з різними портами → **ECS з динамічним мапінгом портів**
- Переривні контейнерні задачі найдешевше → **Fargate Spot** (або ECS на EC2 Spot)
- Запускати контейнери ECS на власних серверах у дата-центрі → **ECS Anywhere**

#### ⚠️ Пастки

- Task role ≠ task execution role: права застосунку проти прав агента ECS.
- Fargate — не окремий оркестратор, а двигун **для** ECS та EKS.
- EKS не «простіший ECS»: без потреби в Kubernetes ECS зазвичай дає менше операційної роботи.
- Контейнер теж має бути **stateless**: дані — у S3, базах, EFS, а не у файловій системі контейнера.

## ✅ Перевір себе

:::quiz
? Команда пакує застосунок у Docker-образи і хоче запускати їх з мінімальними операційними зусиллями: без керування серверами, патчів ОС і масштабування кластера. Досвіду Kubernetes немає. Що обрати?
+ Amazon ECS на AWS Fargate
- Amazon EKS з self-managed вузлами
- Amazon ECS на EC2 з власною Auto Scaling group
- Docker на окремому інстансі EC2
= ECS на Fargate не потребує керування серверами: AWS виділяє ресурси під кожну задачу. EKS має сенс, коли вже є Kubernetes, а варіанти з EC2 додають керування серверами.

? Застосунок у контейнері ECS має записувати дані в таблицю DynamoDB. Як правильно надати права?
- Покласти access keys у змінні середовища контейнера
- Надати права task execution role
+ Надати права IAM task role в task definition
- Відкрити таблицю через Security Group
= Task role — права застосунку всередині контейнера. Task execution role використовує агент ECS для завантаження образів, секретів і запису журналів.

? Компанія має 40 мікросервісів у Kubernetes у власному дата-центрі і хоче перенести їх в AWS, зберігши наявні маніфести й Helm-чарти. Що обрати?
- Amazon ECS на Fargate
+ Amazon EKS
- AWS Lambda
- AWS Elastic Beanstalk
= EKS — керований Kubernetes, сумісний з наявними інструментами. Перехід на ECS вимагав би переписати опис розгортань.

? Щоночі тисячі короткочасних контейнерних задач обробляють зображення; задачі можна переривати й перезапускати. Як знизити вартість при запуску на ECS без серверів?
+ Використовувати Fargate Spot
- Використовувати Dedicated Hosts
- Збільшити CPU задач
- Перейти на EKS
= Fargate Spot дає значну знижку для переривних задач. Dedicated Hosts — навпаки, дорожчі, а зміна оркестратора не впливає на ціну обчислень.

? Служба безпеки вимагає постійно перевіряти образи контейнерів у реєстрі на відомі вразливості. Що використати?
- Amazon Macie
+ Amazon ECR з розширеним скануванням (Amazon Inspector)
- AWS WAF
- Amazon GuardDuty для S3
= ECR інтегрований з Inspector для постійного сканування образів на CVE. Macie шукає чутливі дані в S3, WAF фільтрує HTTP, GuardDuty виявляє загрози в акаунті.

? Задачі ECS не запускаються з помилкою «CannotPullContainerError: access denied» при завантаженні образу з ECR. Що перевірити насамперед?
+ Права task execution role на читання з ECR
- Права task role на DynamoDB
- Налаштування cross-zone load balancing
- Security Group бази даних
= Образ завантажує агент ECS від імені task execution role (для Fargate). Якщо в неї немає прав ECR (або немає мережевого шляху до ECR), образ не завантажиться.

? Які твердження про AWS Fargate правильні? (Оберіть 2)
+ Працює як двигун і для Amazon ECS, і для Amazon EKS
- Вимагає керувати вузлами кластера Kubernetes
+ Тарифікується за запитані vCPU і пам'ять задачі
- Дозволяє встановлювати патчі на хост-ОС задачі
- Підходить лише для задач тривалістю до 15 хвилин
= Fargate — serverless-двигун для ECS і EKS, оплата за ресурси задачі. Хостами керує AWS, а обмеження 15 хвилин стосується Lambda, а не Fargate.
:::
