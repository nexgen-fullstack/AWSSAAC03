# Пробний іспит 2 (оригінальні питання у стилі SAA-C03)

Формат: `## Q<номер> | <домен>`, далі EN, UA, варіанти (зірочка після літери — правильна відповідь), WHY — пояснення. Розподіл за доменами як на справжньому іспиті: безпека 20, стійкість 17, продуктивність 15, вартість 13.

## Q1 | secure
EN: A company runs an AWS Lambda function in Account A. The function must write items to an Amazon DynamoDB table in Account B. The security team does not allow long-term credentials to be shared between accounts. What should a solutions architect do?
UA: Функція Lambda в акаунті A має записувати елементи в таблицю DynamoDB в акаунті B. Служба безпеки забороняє передавати довгострокові облікові дані між акаунтами. Що зробити?
A: Create an IAM user in Account B, generate access keys, and store them in the Lambda function's environment variables.
B*: Create an IAM role in Account B with write access to the table and a trust policy that allows the Lambda execution role in Account A to assume it. Call sts:AssumeRole from the function.
C: Add a resource-based policy to the Lambda function that grants access to the DynamoDB table in Account B.
D: Share the DynamoDB table with Account A by using AWS Resource Access Manager (AWS RAM).
WHY: Доступ між акаунтами — через роль у цільовому акаунті, якій довіряє роль виконання Lambda з першого акаунта; STS видає тимчасові облікові дані. Ключі IAM-користувача (A) — довгострокові. Політика на ресурсі Lambda (C) визначає, хто може викликати функцію, а не що може сама функція. RAM (D) не ділиться таблицями DynamoDB.

## Q2 | secure
EN: A company hosts a static website in an Amazon S3 bucket and serves it through Amazon CloudFront. The security team requires that users cannot access the objects directly through S3 URLs, and the bucket must not be public. What should the solutions architect do?
UA: Статичний сайт у S3 роздається через CloudFront. Користувачі не повинні мати доступу до об'єктів напряму через URL S3, а bucket не може бути публічним. Що зробити?
A: Enable S3 static website hosting, make the bucket public, and restrict access with a Referer header condition.
B*: Configure CloudFront origin access control (OAC) and update the bucket policy to allow access only from the CloudFront distribution. Keep S3 Block Public Access enabled.
C: Use S3 presigned URLs for every object and embed them in the HTML pages.
D: Place the bucket in a private subnet and allow access only from CloudFront IP ranges.
WHY: OAC дає CloudFront право читати приватний bucket, а bucket policy з умовою на ARN дистрибуції пускає лише його; Block Public Access лишається увімкненим. Заголовок Referer (A) легко підробити, і bucket при цьому публічний. Presigned URLs (C) мають термін дії й не підходять для статичного сайту. S3 не розміщується в підмережах (D).

## Q3 | secure
EN: A video streaming company stores premium videos in Amazon S3 and delivers them through Amazon CloudFront. Only paying subscribers may watch the videos. Each video consists of hundreds of small segment files. What is the MOST efficient way to restrict access?
UA: Преміум-відео зберігаються в S3 і роздаються через CloudFront. Дивитися можуть лише платні підписники. Кожне відео складається із сотень дрібних файлів-сегментів. Як найефективніше обмежити доступ?
A: Generate a CloudFront signed URL for each segment file.
B*: Use CloudFront signed cookies issued to authenticated subscribers.
C: Use AWS WAF geographic match rules on the distribution.
D: Make the origin bucket private and create an IAM user for each subscriber.
WHY: Signed cookies — одна «перепустка» на багато файлів, ідеально для відео із сотнями сегментів. Signed URL (A) підходить для окремих файлів — тут довелося б підписувати кожен сегмент. Geo match (C) обмежує країни, а не підписників. IAM-користувачі для клієнтів (D) — антипатерн.

## Q4 | secure
EN: Developers must be able to create IAM roles for their AWS Lambda functions. The security team wants to ensure that developers cannot create roles with more permissions than an approved maximum, which prevents privilege escalation. What should the solutions architect use?
UA: Розробники мають створювати ролі IAM для своїх функцій Lambda. Служба безпеки хоче гарантувати, що нові ролі не отримають прав понад затверджений максимум, — без ескалації привілеїв. Що використати?
A: A service control policy that denies iam:CreateRole in all accounts
B*: IAM permissions boundaries, with a developer policy that allows iam:CreateRole only when the approved boundary is attached to the new role
C: AWS Config rules that delete roles with administrator permissions
D: IAM Access Analyzer policy generation
WHY: Permissions boundary обмежує максимальні права ролі, а умова iam:PermissionsBoundary у політиці розробника дозволяє створювати ролі лише з цією межею. SCP (A) повністю заборонила б створення ролей. Config (C) реагує вже після факту. Access Analyzer (D) генерує політики, але не запобігає ескалації.

## Q5 | secure
EN: A company wants to require multi-factor authentication (MFA) for any IAM user who attempts to terminate Amazon EC2 instances or delete Amazon RDS DB instances in the production account. Other actions must not require MFA. What should the solutions architect do?
UA: Для завершення інстансів EC2 чи видалення баз RDS у production-акаунті IAM-користувачі мають обов'язково використовувати MFA. Для інших дій MFA не вимагати. Що зробити?
A: Enable MFA on the root user of the production account.
B*: Attach an IAM policy that denies ec2:TerminateInstances and rds:DeleteDBInstance when the aws:MultiFactorAuthPresent condition key is false or not present.
C: Enable AWS CloudTrail and send an alert when these actions occur without MFA.
D: Use AWS Config to require MFA for these API actions.
WHY: Deny з умовою на aws:MultiFactorAuthPresent (через BoolIfExists, щоб врахувати відсутній ключ) блокує саме ці дії без MFA. MFA на root (A) не впливає на IAM-користувачів. CloudTrail (C) лише фіксує дії, а Config (D) не керує доступом.

## Q6 | secure
EN: A company has an existing unencrypted Amazon RDS for MySQL DB instance. A new compliance requirement states that the database must be encrypted at rest with an AWS KMS key. What should the solutions architect do?
UA: Є незашифрований екземпляр RDS for MySQL. Нова вимога: база має бути зашифрована в стані спокою ключем KMS. Що зробити?
A: Modify the DB instance and enable encryption.
B*: Create a snapshot of the DB instance, copy the snapshot with encryption enabled, and restore a new DB instance from the encrypted snapshot.
C: Enable encryption on the underlying EBS volumes of the DB instance.
D: Create an encrypted read replica of the unencrypted DB instance and promote it.
WHY: Шифрування RDS вмикається лише під час створення. Стандартний шлях — знімок → копія знімка з шифруванням → відновлення нового екземпляра й перемикання застосунку. Змінити наявний екземпляр (A) не можна, доступу до його томів EBS (C) немає, а зашифровану репліку з незашифрованого екземпляра створити неможливо (D).

## Q7 | secure
EN: An application in us-east-1 encrypts data on the client side with an AWS KMS key before storing it in Amazon S3 and Amazon DynamoDB. For disaster recovery, the data is replicated to eu-west-1, where the application must decrypt it without calling AWS KMS in us-east-1. What should the solutions architect do?
UA: Застосунок у us-east-1 шифрує дані на боці клієнта ключем KMS перед записом у S3 і DynamoDB. Для DR дані реплікуються в eu-west-1, де їх треба розшифровувати без звернень до KMS у us-east-1. Що зробити?
A: Export the KMS key material from us-east-1 and import it into a new key in eu-west-1.
B*: Use an AWS KMS multi-Region key and create a replica key in eu-west-1.
C: Create a new KMS key in eu-west-1 and re-encrypt all data during replication with a Lambda function.
D: Store a copy of each plaintext data key in AWS Secrets Manager in eu-west-1.
WHY: Multi-Region keys мають однаковий ключовий матеріал і ID у різних регіонах, тож дані, зашифровані в us-east-1, розшифровуються реплікою ключа в eu-west-1. Експортувати матеріал ключа KMS (A) неможливо. C — складно й дорого. Зберігати відкриті ключі даних окремо (D) небезпечно.

## Q8 | secure
EN: A company exposes an internal REST API through Amazon API Gateway. The API must be reachable only from the company's VPC and must not be accessible from the internet. What should the solutions architect do?
UA: Внутрішній REST API в API Gateway має бути доступний лише з VPC компанії, а не з інтернету. Що зробити?
A: Create an edge-optimized API and restrict it with AWS WAF IP rules.
B*: Create a private API, create an interface VPC endpoint for execute-api, and add a resource policy that allows access only through that endpoint.
C: Create a Regional API and place it in a private subnet.
D: Create a Regional API and attach a security group that allows only the VPC CIDR range.
WHY: Private API доступний лише через interface endpoint (execute-api) у VPC, а resource policy обмежує доступ конкретним endpoint або VPC. Edge-optimized і Regional API (A, C, D) — публічні; API Gateway не розміщується в підмережах і не має Security Groups.

## Q9 | secure
EN: A mobile app calls a REST API in Amazon API Gateway. Users sign up and sign in through the app. The API must accept requests only from signed-in users, with the LEAST custom code. What should the solutions architect use?
UA: Мобільний застосунок викликає REST API в API Gateway. Користувачі реєструються й входять через застосунок. API має приймати запити лише від тих, хто увійшов, з мінімумом власного коду. Що обрати?
A: An IAM user for each app user with Signature Version 4 request signing
B*: An Amazon Cognito user pool and a Cognito user pool authorizer on the API
C: A Lambda authorizer that queries a user table in Amazon RDS
D: API keys and usage plans
WHY: Cognito user pool керує реєстрацією й входом і видає JWT, а вбудований авторизатор API Gateway перевіряє токени без коду. IAM-користувачі для клієнтів (A) не масштабуються. Lambda-авторизатор (C) — власний код. API keys (D) ідентифікують клієнта для лімітів, а не автентифікують користувачів.

## Q10 | secure
EN: A networking team manages a central VPC. Application teams work in separate AWS accounts in the same organization and must launch resources directly into subnets of the central VPC, while the networking team keeps control of routing, gateways, and network ACLs. Which solution meets these requirements?
UA: Мережева команда керує центральною VPC. Команди застосунків працюють в окремих акаунтах тієї ж організації й мають запускати ресурси прямо в підмережах центральної VPC, а маршрутизацію, шлюзи й NACL контролює мережева команда. Яке рішення?
A: Create VPC peering connections between each application account's VPC and the central VPC.
B*: Share the subnets with the application accounts by using VPC sharing through AWS Resource Access Manager (AWS RAM).
C: Create a transit gateway and attach all application VPCs to it.
D: Create IAM users for the application teams in the networking account.
WHY: VPC sharing через RAM дозволяє акаунтам-учасникам запускати ресурси в спільних підмережах, а власник VPC керує маршрутами, шлюзами й NACL. Peering і Transit Gateway (A, C) з'єднують окремі VPC, а не дають спільних підмереж. IAM-користувачі в чужому акаунті (D) ламають розділення відповідальності.

## Q11 | secure
EN: A security team must identify all S3 buckets, IAM roles, and KMS keys in the organization that grant access to principals outside the organization. The solution must continuously monitor for new cases. What should the solutions architect use?
UA: Треба знайти всі buckets S3, ролі IAM і ключі KMS в організації, що дають доступ суб'єктам поза організацією, і постійно стежити за новими випадками. Що використати?
A: Amazon GuardDuty
B*: IAM Access Analyzer with the organization as the zone of trust
C: AWS Trusted Advisor
D: Amazon Inspector
WHY: IAM Access Analyzer аналізує політики ресурсів і повідомляє про доступ ззовні зони довіри (організації), постійно оновлюючи знахідки. GuardDuty (A) шукає загрози в активності, Trusted Advisor (C) дає загальні перевірки, Inspector (D) шукає вразливості ПЗ.

## Q12 | secure
EN: A company wants to detect compromised Amazon EC2 instances, such as instances communicating with known cryptocurrency-mining IP addresses, and unusual API activity in its AWS accounts. The solution must require no agents and minimal setup. What should the solutions architect use?
UA: Потрібно виявляти скомпрометовані EC2 (наприклад, зв'язок з відомими адресами криптомайнінгу) і незвичну активність API в акаунтах — без агентів і з мінімальним налаштуванням. Що обрати?
A*: Amazon GuardDuty
B: Amazon Macie
C: AWS Config
D: Amazon Detective
WHY: GuardDuty аналізує CloudTrail, VPC Flow Logs і DNS-журнали за допомогою ML і розвідданих про загрози, без агентів. Macie (B) шукає чутливі дані в S3, Config (C) перевіряє налаштування, Detective (D) допомагає розслідувати вже знайдені інциденти.

## Q13 | secure
EN: A company needs continuous, automated scanning of its Amazon EC2 instances and container images in Amazon ECR for software vulnerabilities and unintended network exposure. What should the solutions architect use?
UA: Потрібне постійне автоматичне сканування EC2 і образів контейнерів в ECR на вразливості ПЗ і небажану мережеву доступність. Що обрати?
A: Amazon GuardDuty
B*: Amazon Inspector
C: AWS Shield Advanced
D: AWS Artifact
WHY: Inspector постійно сканує EC2, образи ECR і функції Lambda на відомі вразливості (CVE) і мережеву доступність. GuardDuty (A) шукає загрози в активності, Shield (C) захищає від DDoS, Artifact (D) видає звіти про відповідність AWS.

## Q14 | secure
EN: Workloads in private subnets across many VPCs send outbound traffic to the internet. The security team requires that outbound HTTPS traffic be allowed only to a list of approved domain names and that all traffic be inspected centrally. What should the solutions architect do?
UA: Навантаження в приватних підмережах багатьох VPC ходять в інтернет. Служба безпеки вимагає дозволяти вихідний HTTPS лише до затвердженого списку доменів і перевіряти весь трафік централізовано. Що зробити?
A: Use security groups with outbound rules for the approved domain names.
B*: Route the traffic through a central inspection VPC with AWS Network Firewall by using AWS Transit Gateway, and configure a stateful domain list rule group.
C: Use network ACLs with rules for the approved domains.
D: Attach AWS WAF to the NAT gateways.
WHY: Network Firewall підтримує stateful-правила зі списками доменів (за SNI і Host) і разом із Transit Gateway дає централізовану інспекцію. Security Groups і NACL (A, C) працюють з IP-адресами й портами, а не з доменами. WAF (D) не підключається до NAT Gateway.

## Q15 | secure
EN: A company's business-critical web application runs behind Amazon CloudFront and an Application Load Balancer. The company needs protection against large and sophisticated DDoS attacks, access to a 24/7 DDoS response team, and protection against scaling charges caused by attacks. What should the solutions architect recommend?
UA: Критичний вебзастосунок працює за CloudFront і ALB. Потрібен захист від великих і складних DDoS-атак, цілодобова команда реагування на DDoS і захист від витрат на масштабування під час атак. Що порадити?
A: AWS Shield Standard
B*: AWS Shield Advanced
C: AWS WAF with rate-based rules only
D: Amazon GuardDuty
WHY: Shield Advanced дає розширений захист від DDoS, доступ до Shield Response Team і компенсацію витрат на масштабування через атаку. Shield Standard (A) безкоштовний, але без команди й компенсацій. WAF (C) — фільтр рівня застосунку, GuardDuty (D) — виявлення загроз.

## Q16 | secure
EN: A security engineer needs to investigate which IP addresses are attempting connections to Amazon EC2 instances in a VPC and whether the connections were accepted or rejected by security groups and network ACLs. What should be enabled?
UA: Інженеру безпеки треба з'ясувати, з яких IP-адрес намагаються підключитися до EC2 у VPC і чи пропустили ці з'єднання Security Groups і NACL. Що увімкнути?
A: AWS CloudTrail data events
B*: VPC Flow Logs
C: Amazon CloudWatch detailed monitoring
D: AWS Config configuration recorder
WHY: VPC Flow Logs записують IP-трафік інтерфейсів: адреси, порти, дію ACCEPT чи REJECT; аналізувати можна в CloudWatch Logs або Athena. CloudTrail (A) записує виклики API, а не мережеві з'єднання. Detailed monitoring (C) дає частіші метрики, Config (D) — налаштування ресурсів.

## Q17 | secure
EN: An application runs as Amazon ECS tasks on AWS Fargate and needs a database password. The password must not be stored in the container image or in plaintext in the task definition. What should the solutions architect do?
UA: Застосунок у задачах ECS на Fargate потребує пароля до бази. Пароль не можна зберігати в образі контейнера чи відкритим текстом у task definition. Що зробити?
A: Store the password in an environment variable in the task definition.
B*: Store the password in AWS Secrets Manager, reference it in the secrets section of the container definition, and allow the task execution role to read it.
C: Store the password in a publicly readable S3 object and download it at container startup.
D: Bake the password into the container image and encrypt the image in Amazon ECR.
WHY: ECS вставляє секрети з Secrets Manager або Parameter Store у змінні середовища контейнера під час запуску, а доступ дає роль виконання задачі. Відкритий текст у task definition (A), публічний об'єкт S3 (C) і пароль в образі (D) — небезпечні.

## Q18 | secure
EN: A company wants to guarantee that no Amazon S3 bucket or object in its AWS account can be made public, even if a user misconfigures a bucket policy or an ACL. What is the simplest solution?
UA: Компанія хоче гарантувати, що жоден bucket чи об'єкт S3 в акаунті не стане публічним, навіть якщо хтось помилиться з bucket policy чи ACL. Яке рішення найпростіше?
A: Enable default encryption on all buckets.
B*: Enable S3 Block Public Access at the account level.
C: Enable S3 Versioning on all buckets.
D: Use AWS Config to detect public buckets every 24 hours.
WHY: Block Public Access на рівні акаунта перекриває будь-які публічні політики й ACL для всіх наявних і нових buckets (а SCP може заборонити його вимикати). Шифрування (A) і версіонування (C) не впливають на публічність, Config (D) лише виявляє порушення після факту.

## Q19 | secure
EN: A company must automatically detect any security group that allows inbound SSH (port 22) from 0.0.0.0/0 and must remove the offending rule without manual intervention. What should the solutions architect do?
UA: Потрібно автоматично виявляти будь-яку Security Group, що дозволяє вхідний SSH (порт 22) з 0.0.0.0/0, і прибирати таке правило без участі людини. Що зробити?
A: Enable VPC Flow Logs and create a CloudWatch alarm.
B*: Use the AWS Config managed rule restricted-ssh with automatic remediation through an AWS Systems Manager Automation runbook.
C: Use Amazon Inspector to scan the security groups weekly.
D: Use AWS Trusted Advisor and review the results monthly.
WHY: Config-правило restricted-ssh оцінює Security Groups при кожній зміні, а автоматичне виправлення через SSM Automation прибирає небезпечне правило. Flow Logs (A) показують трафік, а не налаштування. Inspector (C) і Trusted Advisor (D) не виправляють автоматично й не працюють у реальному часі.

## Q20 | secure
EN: A company stores confidential documents in an Amazon S3 bucket. All data must be encrypted at rest with a customer managed AWS KMS key, and all requests to the bucket must use encryption in transit. Which TWO actions should the solutions architect take? (Choose TWO.)
UA: Конфіденційні документи в S3 мають бути зашифровані KMS-ключем компанії, а всі запити до bucket — іти лише зашифрованим каналом. Які ДВІ дії потрібні?
A*: Configure default bucket encryption with SSE-KMS by using the customer managed key.
B*: Add a bucket policy that denies any request when aws:SecureTransport is false.
C: Enable S3 Transfer Acceleration.
D: Enable S3 Versioning.
E: Use SSE-C with keys stored in the application.
WHY: Шифрування за замовчуванням з SSE-KMS гарантує, що кожен новий об'єкт шифрується ключем компанії, а заборона aws:SecureTransport = false відкидає запити без HTTPS. Transfer Acceleration (C) пришвидшує передачу, версіонування (D) зберігає версії, SSE-C (E) не використовує KMS.

## Q21 | resilient
EN: A company needs a disaster recovery solution for a business-critical application with an RTO of a few minutes. A fully functional but scaled-down copy of the production environment must always be running in a second AWS Region, ready to scale up. Which DR strategy is this?
UA: Для критичного застосунку потрібне DR з RTO в кілька хвилин. У другому регіоні завжди працює повністю функціональна, але зменшена копія production, готова до масштабування. Яка це стратегія?
A: Backup and restore
B: Pilot light
C*: Warm standby
D: Multi-site active/active
WHY: Warm standby — зменшена, але робоча копія всього застосунку, яку при аварії масштабують. У pilot light (B) постійно живуть лише дані, а сервери запускають після аварії. Backup and restore (A) повільніший, active/active (D) обслуговує трафік в обох регіонах на повну потужність.

## Q22 | resilient
EN: An internal reporting application can tolerate up to 24 hours of downtime and the loss of up to 12 hours of data. The company wants protection against a Regional outage at the LOWEST cost. What should the solutions architect recommend?
UA: Внутрішній звітний застосунок може простоювати до 24 годин і втратити дані за 12 годин. Потрібен захист від збою регіону з найнижчою вартістю. Що порадити?
A: Amazon Aurora Global Database with a secondary cluster in another Region
B: A warm standby environment in another Region
C*: Scheduled backups copied to another Region with AWS Backup, and infrastructure defined in AWS CloudFormation for recovery
D: An active/active deployment with Amazon Route 53 latency-based routing
WHY: Великі допустимі RPO і RTO дозволяють найдешевшу стратегію backup and restore: копії в іншому регіоні й відтворення інфраструктури кодом. A, B і D дають кращі RPO і RTO, але коштують значно більше.

## Q23 | resilient
EN: Some messages in an Amazon SQS queue cause the consumer application to fail every time they are processed. These messages are received again and again and delay the processing of other messages. What should the solutions architect do?
UA: Деякі повідомлення в черзі SQS щоразу валять обробник. Вони отримуються знову і знову й затримують обробку інших. Що зробити?
A: Increase the message retention period to 14 days.
B*: Configure a dead-letter queue with a redrive policy and an appropriate maxReceiveCount.
C: Switch to an SQS FIFO queue.
D: Decrease the visibility timeout to 0 seconds.
WHY: Після maxReceiveCount невдалих спроб повідомлення переходить у DLQ, де його можна дослідити, і черга не блокується. Довше зберігання (A) лише продовжить проблему, FIFO (C) навіть блокує групу повідомлень, нульовий visibility timeout (D) спричинить дублікати.

## Q24 | resilient
EN: Worker instances in an Auto Scaling group process messages from an Amazon SQS queue. The number of messages varies greatly during the day. The company wants the number of instances to follow the workload so that each instance always has an acceptable number of messages to process. Which scaling approach is BEST?
UA: Інстанси-обробники в Auto Scaling group читають повідомлення з SQS; кількість повідомлень протягом дня сильно змінюється. Кількість інстансів має відповідати навантаженню, щоб на кожен припадала прийнятна кількість повідомлень. Який спосіб масштабування найкращий?
A: Scheduled scaling at fixed times of day
B: Target tracking on the average CPU utilization of the group
C*: Target tracking on a custom metric for backlog per instance (ApproximateNumberOfMessagesVisible divided by the number of running instances)
D: Simple scaling based on the NumberOfMessagesSent metric
WHY: Метрика «беклог на інстанс» прямо відображає навантаження: target tracking тримає її на цільовому рівні, додаючи чи прибираючи інстанси. Розклад (A) не реагує на реальні зміни, CPU (B) може не відповідати довжині черги, NumberOfMessagesSent (D) не показує накопичення.

## Q25 | resilient
EN: A company wants to react to events from its SaaS helpdesk provider (for example, new high-priority tickets) and route them to different AWS targets based on the event content, without any custom polling code. The provider is an Amazon EventBridge partner. What should the solutions architect do?
UA: Компанія хоче реагувати на події SaaS-сервісу підтримки (наприклад, нові термінові тікети) і направляти їх до різних цілей AWS залежно від вмісту, без власного коду опитування. Постачальник — партнер EventBridge. Що зробити?
A: Write a Lambda function that polls the provider's API every minute.
B*: Use an EventBridge partner event source with a partner event bus, and create rules with event patterns that route events to the targets.
C: Create an Amazon SNS topic and ask the provider to send emails to it.
D: Ingest the events with Amazon Kinesis Data Streams.
WHY: EventBridge приймає події від SaaS-партнерів напряму, а правила з шаблонами подій фільтрують і маршрутизують їх до цілей без коду. Опитування (A) — власний код і затримки. SNS (C) не інтегрується з партнерами і не маршрутизує так гнучко, Kinesis (D) тут зайвий.

## Q26 | resilient
EN: An application uses an Amazon Aurora MySQL DB cluster. Read traffic grows unpredictably during the day, and the company also wants fast automatic failover if the writer instance fails. What should the solutions architect do?
UA: Застосунок використовує кластер Aurora MySQL. Навантаження на читання непередбачувано зростає протягом дня, і потрібне швидке автоматичне перемикання при збої writer. Що зробити?
A: Create cross-Region read replicas and send all reads to them.
B*: Add Aurora Replicas in multiple Availability Zones with Aurora Auto Scaling, and send reads to the reader endpoint.
C: Increase the instance size of the writer.
D: Add a separate non-readable standby instance to the cluster.
WHY: Aurora Replicas масштабують читання через reader endpoint (з автомасштабуванням) і водночас є цілями для автоматичного failover. Міжрегіональні репліки (A) додають затримку й призначені для DR, більший writer (C) не дає відмовостійкості, окремого «нечитабельного standby» в Aurora немає — цю роль виконують репліки (D).

## Q27 | resilient
EN: A containerized application runs on Amazon ECS with AWS Fargate across three Availability Zones. The tasks need a shared file system that keeps data independently of the task lifecycle and remains available if one Availability Zone fails. What should the solutions architect use?
UA: Контейнерний застосунок на ECS з Fargate працює у трьох AZ. Задачам потрібна спільна файлова система, що зберігає дані незалежно від життя задач і лишається доступною при відмові однієї AZ. Що обрати?
A: Fargate ephemeral storage
B: An Amazon EBS volume attached to each task
C*: Amazon EFS with mount targets in each Availability Zone
D: Instance store volumes
WHY: EFS — регіональна спільна файлова система з точками монтування в кожній AZ, яку Fargate монтує нативно. Ефемерне сховище (A) зникає разом із задачею, том EBS (B) прив'язаний до однієї AZ і не спільний між задачами, instance store (D) у Fargate недоступний.

## Q28 | resilient
EN: An AWS Lambda function is invoked asynchronously by Amazon S3 event notifications. Occasionally the function fails, and after the retries are exhausted, the events are lost. The company must capture failed events for later reprocessing with minimal effort. What should the solutions architect do?
UA: Функцію Lambda асинхронно викликають події S3. Іноді вона падає, і після вичерпання повторів події губляться. Треба зберігати невдалі події для повторної обробки з мінімальними зусиллями. Що зробити?
A: Increase the function timeout to 15 minutes.
B*: Configure an on-failure destination, such as an Amazon SQS queue, for asynchronous invocations of the function.
C: Enable S3 Versioning on the bucket.
D: Invoke the function synchronously from an EC2 instance instead.
WHY: Для асинхронних викликів Lambda підтримує destinations: після всіх повторів невдала подія разом з деталями помилки йде в SQS, SNS, EventBridge або іншу функцію. Довший тайм-аут (A) не допоможе при помилках, версіонування (C) не стосується подій, D ускладнює архітектуру.

## Q29 | resilient
EN: A company deploys a new version of its web application to a new Auto Scaling group behind the existing Application Load Balancer. The company wants to send 10% of the traffic to the new version, increase the share gradually, and roll back instantly if errors occur. What should the solutions architect use?
UA: Нова версія вебзастосунку розгортається в новій Auto Scaling group за наявним ALB. Потрібно відправити на неї 10% трафіку, поступово збільшувати частку й миттєво відкотитися при помилках. Що використати?
A: Create a second ALB and use Amazon Route 53 simple routing.
B*: Use weighted target groups in the ALB listener rule to split traffic between the old and new target groups.
C: Enable sticky sessions on the ALB.
D: Place a Network Load Balancer in front of the ALB.
WHY: Правило listener ALB може пересилати трафік на кілька target groups з вагами (10/90, 50/50…), а відкат — просто зміна ваги. Simple routing (A) не розподіляє за вагами, sticky sessions (C) прив'язують користувача до цілі, NLB (D) нічого не додає.

## Q30 | resilient
EN: An application stores data in an Amazon DynamoDB table. Three hours ago, a bug in a new release overwrote thousands of items with incorrect values. The company must restore the table to its state just before the bug, with minimal data loss. Which feature should have been enabled in advance?
UA: Застосунок зберігає дані в DynamoDB. Три години тому помилка в новому релізі перезаписала тисячі елементів неправильними значеннями. Треба відновити таблицю до стану безпосередньо перед помилкою з мінімальною втратою даних. Яку функцію мали увімкнути заздалегідь?
A: DynamoDB Streams
B*: Point-in-time recovery (PITR)
C: Global tables
D: DynamoDB Accelerator (DAX)
WHY: PITR дозволяє відновити таблицю (у нову) на будь-яку секунду за останні 35 днів. Streams (A) зберігають зміни лише 24 години й не відновлюють таблицю, global tables (C) реплікують і помилкові записи, DAX (D) — кеш.

## Q31 | resilient
EN: Users accidentally delete and overwrite important objects in an Amazon S3 bucket. The company needs to recover previous versions of objects while keeping storage costs under control. What should the solutions architect do?
UA: Користувачі випадково видаляють і перезаписують важливі об'єкти в S3. Потрібна змога відновлювати попередні версії, але з контролем витрат на зберігання. Що зробити?
A*: Enable S3 Versioning and add a lifecycle rule that expires noncurrent versions after a defined number of days.
B: Enable S3 Transfer Acceleration.
C: Replicate the bucket to another Region without enabling versioning.
D: Create daily copies of the bucket with a scheduled Lambda function.
WHY: Версіонування зберігає попередні версії й маркери видалення, а lifecycle-правило прибирає застарілі версії через заданий час, стримуючи витрати. Transfer Acceleration (B) — про швидкість, реплікація без версіонування (C) неможлива, D — власний код і подвійне зберігання.

## Q32 | resilient
EN: A company has 150 on-premises physical and virtual servers that run critical applications. The company needs disaster recovery in AWS with an RPO of seconds and an RTO of minutes, and it wants to pay minimal costs while no disaster is occurring. What should the solutions architect use?
UA: У компанії 150 фізичних і віртуальних серверів on-premises з критичними застосунками. Потрібне DR в AWS з RPO в секунди і RTO в хвилини та мінімальними витратами, поки аварії немає. Що обрати?
A: AWS Backup with daily backups of the servers
B*: AWS Elastic Disaster Recovery (AWS DRS)
C: AWS Application Migration Service
D: AWS DataSync with hourly tasks
WHY: DRS постійно реплікує диски серверів у дешеву staging-зону і при аварії запускає повноцінні інстанси за хвилини. Щоденні бекапи (A) дають RPO в годинах, MGN (C) призначений для міграції, DataSync (D) копіює файли, а не сервери.

## Q33 | resilient
EN: A VPC has private subnets in three Availability Zones. All private subnets route internet-bound traffic to a single NAT gateway in Availability Zone A. During an outage of Availability Zone A, instances in the other zones lost internet access. How should the solutions architect improve resilience?
UA: У VPC є приватні підмережі у трьох AZ, і всі вони відправляють трафік в інтернет через один NAT Gateway в AZ A. Під час збою AZ A інстанси в інших зонах втратили інтернет. Як підвищити стійкість?
A: Replace the NAT gateway with a larger NAT instance in Availability Zone A.
B*: Create a NAT gateway in each Availability Zone and configure each private subnet's route table to use the NAT gateway in the same zone.
C: Associate a second Elastic IP address with the existing NAT gateway.
D: Add a route to the internet gateway in the private subnets' route tables.
WHY: NAT Gateway — зональний ресурс; для стійкості потрібен NAT у кожній AZ з маршрутом на «свій» (це ще й прибирає плату за трафік між AZ). NAT instance (A) — та сама єдина точка відмови, друга IP (C) не додає зони, маршрут на IGW (D) робить підмережі публічними.

## Q34 | resilient
EN: An order service publishes all order events to an Amazon SNS topic. An SMS notification service must receive only orders with the attribute priority set to "high", while an analytics queue must receive all orders. What is the simplest solution?
UA: Сервіс замовлень публікує всі події в тему SNS. Сервіс SMS має отримувати лише замовлення з атрибутом priority = «high», а черга аналітики — усі. Яке рішення найпростіше?
A: Create a separate SNS topic for high-priority orders and change the publisher to publish to both topics.
B*: Subscribe both consumers to the topic and apply a subscription filter policy on the SMS service's subscription that matches priority = high.
C: Let the SMS service receive all messages and discard the others in code.
D: Use an SQS FIFO queue for high-priority orders.
WHY: Filter policy на підписці SNS доставляє підписнику лише повідомлення з потрібними атрибутами чи вмістом, без змін у видавці. A ускладнює видавця, C витрачає ресурси й гроші на непотрібні повідомлення, FIFO (D) не фільтрує.

## Q35 | resilient
EN: A company must be able to recover its production Amazon RDS for PostgreSQL database in another AWS Region if the primary Region becomes unavailable. The RPO must be a few minutes at most. Which TWO actions are required? (Choose TWO.)
UA: Потрібно мати змогу відновити production-базу RDS for PostgreSQL в іншому регіоні, якщо основний регіон недоступний. RPO — щонайбільше кілька хвилин. Які ДВІ дії потрібні?
A*: Create a cross-Region read replica of the DB instance in the DR Region.
B*: During a disaster, promote the read replica to a standalone DB instance and point the application to it.
C: Enable Multi-AZ on the primary DB instance.
D: Enable S3 Cross-Region Replication for the database storage.
E: Take daily manual snapshots in the primary Region.
WHY: Міжрегіональна репліка асинхронно отримує зміни із затримкою в секунди чи хвилини, а під час аварії її підвищують (promote) до самостійної бази. Multi-AZ (C) захищає лише в межах регіону, сховище RDS не реплікується через S3 CRR (D), щоденні знімки (E) дають RPO до доби.

## Q36 | resilient
EN: A company is migrating an on-premises application that uses Apache ActiveMQ through the JMS API. The company wants a managed message broker in AWS, requires high availability across Availability Zones, and wants to avoid rewriting the messaging code. What should the solutions architect use?
UA: Компанія переносить застосунок, що працює з Apache ActiveMQ через JMS. Потрібен керований брокер в AWS з високою доступністю між AZ і без переписування коду обміну повідомленнями. Що обрати?
A: Amazon SQS standard queues
B: Amazon SNS topics
C*: Amazon MQ for ActiveMQ with an active/standby broker deployment across two Availability Zones
D: Amazon Kinesis Data Streams
WHY: Amazon MQ — керований ActiveMQ і RabbitMQ з підтримкою JMS, AMQP, MQTT, а розгортання active/standby забезпечує стійкість між AZ. SQS, SNS і Kinesis (A, B, D) вимагали б переписати код під інші API.

## Q37 | resilient
EN: A stateless web tier needs 6 Amazon EC2 instances to serve peak traffic. The tier runs in three Availability Zones. The company requires that the tier keep serving peak traffic without waiting for new instances to launch, even if one Availability Zone fails. What is the minimum number of instances that the Auto Scaling group should run?
UA: Вебшару без стану на піку потрібно 6 інстансів EC2; шар працює у трьох AZ. Він має витримувати піковий трафік без очікування запуску нових інстансів, навіть якщо одна AZ відмовить. Яка мінімальна кількість інстансів у групі?
A: 6 instances (2 per Availability Zone)
B: 7 instances
C*: 9 instances (3 per Availability Zone)
D: 12 instances (4 per Availability Zone)
WHY: Після втрати однієї AZ у двох інших має лишитися 6 інстансів, тобто по 3 у кожній; отже, по 3 у всіх трьох зонах — 9. Це статична стабільність. 6 (A) після втрати AZ дадуть лише 4, 7 (B) не розподіляються рівно, 12 (D) — більше, ніж потрібно.

## Q38 | performance
EN: Users around the world upload large files (1–5 GB) to an Amazon S3 bucket in eu-central-1. Uploads from distant continents are slow and sometimes fail. What should the solutions architect do to improve upload speed and reliability?
UA: Користувачі з усього світу завантажують великі файли (1–5 GB) у bucket S3 в eu-central-1. З далеких континентів завантаження повільні й інколи обриваються. Як пришвидшити їх і зробити надійнішими?
A: Create read replicas of the bucket in other Regions.
B*: Enable S3 Transfer Acceleration and use multipart upload.
C: Put Amazon CloudFront in front of the bucket with a cache behavior for GET requests only.
D: Request a higher bucket request rate limit through AWS Support.
WHY: Transfer Acceleration приймає дані в найближчій точці присутності й везе їх мережею AWS, а multipart upload завантажує частини паралельно й повторює лише невдалі. «Реплік для запису» в S3 немає (A), кешування GET (C) не прискорює завантаження, ліміт запитів (D) тут ні до чого.

## Q39 | performance
EN: An application writes and reads log objects under a single S3 prefix at about 15,000 requests per second and receives HTTP 503 Slow Down errors. What should the solutions architect recommend?
UA: Застосунок пише й читає об'єкти журналів в одному префіксі S3 зі швидкістю близько 15 000 запитів за секунду й отримує помилки 503 Slow Down. Що порадити?
A: Move the objects to S3 Glacier Instant Retrieval.
B*: Distribute the objects across multiple prefixes so that the requests are spread out.
C: Enable S3 Versioning.
D: Run the application on a larger EC2 instance.
WHY: S3 масштабується за префіксами: щонайменше 3 500 запитів PUT/DELETE і 5 500 GET за секунду на префікс. Розподіл об'єктів між кількома префіксами (наприклад, за хешем) збільшує загальну пропускну здатність. Glacier (A) і версіонування (C) не допоможуть, інстанс (D) — не вузьке місце.

## Q40 | performance
EN: A high performance computing (HPC) application runs on a group of Amazon EC2 instances that continuously exchange data. The application requires the lowest possible network latency and the highest throughput between the instances. What should the solutions architect do?
UA: HPC-застосунок працює на групі інстансів EC2, що безперервно обмінюються даними. Потрібна мінімальна мережева затримка й максимальна пропускна здатність між ними. Що зробити?
A: Launch the instances in a spread placement group across multiple Availability Zones.
B*: Launch the instances in a cluster placement group in a single Availability Zone by using instance types that support Elastic Fabric Adapter (EFA).
C: Launch the instances in different Regions and connect them with VPC peering.
D: Use a partition placement group with one instance per partition.
WHY: Cluster placement group розміщує інстанси фізично поруч в одній AZ, а EFA дає мережу з наднизькою затримкою для HPC. Spread (A) і partition (D) групи — для ізоляції збоїв, а не швидкості; різні регіони (C) лише збільшать затримку.

## Q41 | performance
EN: An Amazon DynamoDB table uses "country" as its partition key. Most of the traffic comes from a single country, and requests are throttled even though the table's total provisioned capacity is not exceeded. What should the solutions architect do?
UA: Таблиця DynamoDB має partition key «country». Більшість трафіку — з однієї країни, і запити тротляться, хоча загальна ємність таблиці не вичерпана. Що зробити?
A: Increase the table's provisioned read and write capacity.
B*: Choose a partition key with high cardinality, such as a customer ID, or add a random suffix (write sharding) to spread the load.
C: Add a global secondary index with country as the partition key.
D: Enable DynamoDB Streams.
WHY: Ключ з малою кількістю значень створює «гарячу» партицію, ліміт якої вичерпується раніше за ємність таблиці. Ключ з високою кардинальністю або write sharding розподіляють навантаження. Більша ємність (A) не усуне гарячу партицію, GSI з тим самим ключем (C) матиме ту саму проблему, Streams (D) ні до чого.

## Q42 | performance
EN: A social network must store user relationships and quickly answer queries such as "friends of friends who like the same brand", which require traversing many connections. Which database is the MOST suitable?
UA: Соцмережі потрібно зберігати зв'язки користувачів і швидко відповідати на запити на кшталт «друзі друзів, яким подобається той самий бренд», що вимагають обходу багатьох зв'язків. Яка база найкраще підходить?
A: Amazon RDS for MySQL
B: Amazon DynamoDB
C*: Amazon Neptune
D: Amazon Redshift
WHY: Neptune — графова база для швидкого обходу зв'язків (Gremlin, openCypher, SPARQL). Реляційні бази (A) і Redshift (D) потребують багатьох важких JOIN, DynamoDB (B) не призначена для обходу графів.

## Q43 | performance
EN: An e-commerce company wants customers to search its product catalog with full-text search, relevance ranking, typo tolerance, and faceted filtering. Which service should the solutions architect use?
UA: Інтернет-магазин хоче, щоб покупці шукали товари повнотекстовим пошуком з ранжуванням за релевантністю, толерантністю до помилок і фільтрами за характеристиками. Який сервіс обрати?
A: Amazon Athena
B*: Amazon OpenSearch Service
C: Amazon DynamoDB with a global secondary index
D: Amazon ElastiCache
WHY: OpenSearch — пошуковий рушій з повнотекстовим пошуком, релевантністю, нечітким пошуком і фасетами. Athena (A) — аналітичний SQL по S3, DynamoDB (C) шукає за ключами, ElastiCache (D) — кеш.

## Q44 | performance
EN: An AWS Lambda function performs CPU-intensive image processing and takes too long to finish. The function is configured with 512 MB of memory. What is the simplest way to make it run faster?
UA: Функція Lambda виконує важку для процесора обробку зображень і працює занадто довго. Їй виділено 512 MB пам'яті. Як найпростіше її пришвидшити?
A: Enable provisioned concurrency.
B*: Increase the memory setting, because Lambda allocates CPU power in proportion to the configured memory.
C: Increase the function timeout.
D: Connect the function to a VPC.
WHY: У Lambda потужність процесора пропорційна пам'яті (до 10 GB і 6 vCPU), тож більше пам'яті — швидше обчислення, часто за ту саму або меншу ціну. Provisioned concurrency (A) лише прибирає холодні старти, тайм-аут (C) не пришвидшує, VPC (D) нічого не дає.

## Q45 | performance
EN: A company needs to run compute-heavy jobs in Docker containers. Each job takes 2–6 hours, and the number of jobs varies daily. The company wants AWS to manage the job queues, scheduling, and scaling of compute resources. What should the solutions architect use?
UA: Потрібно запускати важкі обчислювальні задачі в Docker-контейнерах. Кожна триває 2–6 годин, кількість задач щодня різна, а AWS має керувати чергами, плануванням і масштабуванням обчислень. Що обрати?
A: AWS Lambda
B*: AWS Batch
C: Amazon EC2 instances with a cron schedule
D: AWS Step Functions Express Workflows
WHY: AWS Batch керує чергами задач, плануванням і масштабуванням обчислень (EC2, Spot, Fargate) для довгих пакетних задач у контейнерах. Lambda (A) обмежена 15 хвилинами, cron на EC2 (C) — ручне керування, Express Workflows (D) тривають до 5 хвилин.

## Q46 | performance
EN: An application runs complex SQL queries against an Amazon RDS for PostgreSQL database. The same query results are requested thousands of times per minute and change only every few minutes. The database CPU utilization is high. What should the solutions architect do to reduce latency and database load?
UA: Застосунок виконує складні SQL-запити до RDS for PostgreSQL. Однакові результати запитуються тисячі разів на хвилину й змінюються раз на кілька хвилин. CPU бази високий. Як зменшити затримку й навантаження?
A: Enable Multi-AZ on the DB instance.
B*: Cache the query results in Amazon ElastiCache by using a lazy-loading strategy with a short TTL.
C: Increase the allocated storage.
D: Move the database to an EC2 instance with instance store volumes.
WHY: Кеш у пам'яті (ElastiCache) віддає повторювані результати за мілісекунди, а TTL у кілька хвилин тримає дані досить свіжими. Multi-AZ (A) — для доступності, більше сховища (C) не зменшить CPU, база на instance store (D) — ризик втрати даних і зайва робота.

## Q47 | performance
EN: An application on Amazon EC2 uses a 100 GiB gp2 volume. The application now needs a consistent 6,000 IOPS. The company wants the MOST cost-effective solution without increasing the volume size. What should the solutions architect do?
UA: Застосунок на EC2 має том gp2 на 100 GiB і тепер потребує стабільних 6 000 IOPS. Потрібне найекономніше рішення без збільшення розміру тому. Що зробити?
A: Increase the gp2 volume size to 2,000 GiB.
B*: Modify the volume to gp3 and provision 6,000 IOPS.
C: Change the volume to io2 Block Express with 6,000 IOPS.
D: Change the volume to st1.
WHY: gp3 має 3 000 IOPS базово й дозволяє докупити IOPS незалежно від розміру, а зміна типу відбувається без простою (Elastic Volumes). gp2 (A) дає 3 IOPS на GiB, тож 6 000 IOPS — лише від 2 000 GiB. io2 (C) дорожчий, st1 (D) — HDD з низькими IOPS.

## Q48 | performance
EN: A company hosts a static website in Amazon S3 and wants to serve it worldwide with low latency through Amazon CloudFront by using the custom domain www.example.com over HTTPS. In which Region must the solutions architect request the certificate in AWS Certificate Manager (ACM)?
UA: Статичний сайт у S3 має роздаватися по світу з низькою затримкою через CloudFront за власним доменом www.example.com з HTTPS. У якому регіоні треба запросити сертифікат в ACM?
A: In the same Region as the S3 bucket
B*: In the US East (N. Virginia) Region (us-east-1)
C: In every Region where users are located
D: In any Region, because ACM certificates are global
WHY: CloudFront використовує сертифікати ACM лише з регіону us-east-1. Для регіональних ресурсів (ALB, регіональний API Gateway) сертифікат створюють у регіоні ресурсу, але для CloudFront — завжди us-east-1.

## Q49 | performance
EN: Several applications consume the same Amazon Kinesis data stream. As more consumers were added, each consumer began to experience higher read latency because all consumers share the read throughput of each shard. What should the solutions architect do?
UA: Кілька застосунків читають той самий потік Kinesis. З додаванням споживачів кожен почав отримувати дані з більшою затримкою, бо всі ділять пропускну здатність читання кожного shard. Що зробити?
A: Increase the data retention period of the stream.
B*: Register the consumers to use enhanced fan-out so that each consumer receives dedicated throughput per shard.
C: Replace the stream with an Amazon SQS standard queue.
D: Decrease the number of shards.
WHY: Enhanced fan-out дає кожному зареєстрованому споживачу власні 2 MB/с на shard з push-доставкою й низькою затримкою. Retention (A) не впливає на швидкість, SQS (C) не дозволяє кільком споживачам читати ті самі дані, менше shards (D) погіршить ситуацію.

## Q50 | performance
EN: A REST API built with Amazon API Gateway and AWS Lambda returns product details that change only a few times per day. The same GET requests are made very frequently. The company wants to reduce latency and the number of Lambda invocations. What should the solutions architect do?
UA: REST API на API Gateway і Lambda повертає деталі товарів, що змінюються кілька разів на день. Однакові GET-запити дуже часті; треба зменшити затримку й кількість викликів Lambda. Що зробити?
A*: Enable API caching on the API Gateway stage with an appropriate TTL.
B: Increase the memory of the Lambda function.
C: Enable provisioned concurrency for the Lambda function.
D: Add usage plans and API keys.
WHY: Кеш стадії API Gateway відповідає на повторні запити без виклику Lambda протягом TTL. Більше пам'яті (B) і provisioned concurrency (C) пришвидшують функцію, але не зменшують кількість викликів, usage plans (D) обмежують клієнтів.

## Q51 | performance
EN: A big data application on Amazon EC2 reads and writes large log files sequentially. It needs high throughput at the lowest cost, and the volume is not used as a boot volume. Which EBS volume type is the MOST appropriate?
UA: Застосунок великих даних на EC2 послідовно читає й пише великі файли журналів. Потрібна висока пропускна здатність за найнижчу ціну; том не завантажувальний. Який тип EBS найкращий?
A: io2 Block Express
B: gp3
C*: Throughput Optimized HDD (st1)
D: Cold HDD (sc1)
WHY: st1 — дешевий HDD для великих послідовних навантажень (до 500 MiB/s): журнали, big data, ETL. io2 (A) і gp3 (B) дорожчі й оптимізовані під IOPS, sc1 (D) дешевший, але для рідко використовуваних даних і з меншою пропускною здатністю.

## Q52 | performance
EN: A web application runs on Amazon EC2 instances behind an Application Load Balancer and has high CPU utilization. Analysis shows that much of the CPU time is spent on TLS encryption and on serving static images and scripts. Which TWO actions will MOST reduce the load on the instances? (Choose TWO.)
UA: Вебзастосунок на EC2 за ALB має високий CPU. Аналіз показує, що багато часу йде на шифрування TLS і роздачу статичних картинок і скриптів. Які ДВІ дії найбільше зменшать навантаження на інстанси?
A*: Serve the static content from Amazon S3 through Amazon CloudFront.
B*: Terminate TLS at the Application Load Balancer by using a certificate from ACM.
C: Increase the size of the EBS volumes.
D: Enable detailed monitoring on the instances.
E: Enable sticky sessions on the ALB.
WHY: CloudFront з S3 забирає роздачу статики із серверів і кешує її ближче до користувачів, а завершення TLS на ALB знімає з інстансів роботу шифрування. Розмір EBS (C), detailed monitoring (D) і sticky sessions (E) навантаження на CPU не зменшують.

## Q53 | cost
EN: A company must keep regulatory archives for 10 years. The data is almost never accessed, and when it is needed, a retrieval time of up to 48 hours is acceptable. What is the MOST cost-effective storage option?
UA: Регуляторні архіви треба зберігати 10 років. Дані майже ніколи не читають, а при потребі отримання до 48 годин прийнятне. Яке сховище найдешевше?
A: S3 Standard-Infrequent Access
B: S3 Glacier Instant Retrieval
C: S3 Glacier Flexible Retrieval
D*: S3 Glacier Deep Archive
WHY: Deep Archive — найдешевший клас S3 для даних, які рідко потрібні, з отриманням за 12–48 годин. Standard-IA (A) і Glacier Instant Retrieval (B) дорожчі й дають миттєвий доступ, Flexible Retrieval (C) дешевший за них, але дорожчий за Deep Archive.

## Q54 | cost
EN: A company runs containerized batch jobs on Amazon ECS with AWS Fargate. The jobs are fault tolerant and can be restarted if they are interrupted. The company wants to reduce compute costs as much as possible without managing servers. What should the solutions architect do?
UA: Пакетні задачі в контейнерах працюють на ECS з Fargate. Вони стійкі до збоїв і можуть перезапускатися після переривання. Треба максимально зменшити витрати на обчислення без керування серверами. Що зробити?
A: Move the tasks to Amazon EC2 On-Demand Instances.
B*: Run the tasks with the Fargate Spot capacity provider.
C: Purchase Dedicated Hosts.
D: Increase the task CPU and memory.
WHY: Fargate Spot запускає задачі на вільних потужностях зі знижкою до 70%, а переривання прийнятні для стійких пакетних задач. EC2 On-Demand (A) вимагає керування серверами й не дешевший, Dedicated Hosts (C) — найдорожчі, більші задачі (D) коштують більше.

## Q55 | cost
EN: A company runs hundreds of AWS Lambda functions written in Python that have no native x86 dependencies. The company wants to reduce Lambda costs without changing the function logic. What should the solutions architect recommend?
UA: Компанія має сотні функцій Lambda на Python без нативних залежностей під x86. Потрібно зменшити витрати на Lambda без зміни логіки коду. Що порадити?
A: Increase the memory of all functions to 10 GB.
B*: Change the function architecture to arm64 (AWS Graviton).
C: Enable provisioned concurrency for all functions.
D: Connect the functions to a VPC.
WHY: Функції на arm64 (Graviton) мають нижчу ціну за GB-секунду й часто кращу продуктивність; для коду на Python без нативних x86-залежностей перехід простий. Максимальна пам'ять (A) і provisioned concurrency (C) збільшать витрати, VPC (D) на ціну не впливає.

## Q56 | cost
EN: An Amazon DynamoDB table in on-demand capacity mode has had steady, predictable traffic 24 hours a day for many months. The company wants to reduce costs. What should the solutions architect do?
UA: Таблиця DynamoDB в режимі on-demand уже багато місяців має стабільний передбачуваний трафік цілодобово. Треба зменшити витрати. Що зробити?
A: Keep on-demand mode and add DynamoDB Accelerator (DAX).
B*: Switch to provisioned capacity mode with auto scaling, and consider reserved capacity for the baseline.
C: Enable global tables.
D: Change the table class to DynamoDB Standard-Infrequent Access.
WHY: Для стабільного передбачуваного трафіку provisioned-режим з автомасштабуванням дешевший за on-demand, а reserved capacity дає додаткову знижку на базове навантаження. DAX (A) і global tables (C) додають витрат, Standard-IA (D) економить на зберіганні рідко читаних даних, а не на запитах.

## Q57 | cost
EN: A company distributes popular software installers (several GB each) directly from an Amazon S3 bucket to millions of users worldwide. Data transfer out costs are high, and users far from the Region report slow downloads. What should the solutions architect do?
UA: Популярні інсталятори програм (по кілька GB) роздаються мільйонам користувачів напряму з bucket S3. Витрати на вихідний трафік високі, а далекі користувачі скаржаться на повільні завантаження. Що зробити?
A: Enable S3 Transfer Acceleration.
B*: Serve the files through Amazon CloudFront with the S3 bucket as the origin.
C: Replicate the bucket to every Region and use Amazon Route 53 geolocation routing.
D: Move the files to S3 Standard-Infrequent Access.
WHY: CloudFront кешує файли в точках присутності: передача з S3 до CloudFront безкоштовна, роздача через CloudFront дешевша й набагато швидша. Transfer Acceleration (A) — платне прискорення завантаження в S3, реплікація в усі регіони (C) дорога й складна, Standard-IA (D) дорожчий при частому читанні.

## Q58 | cost
EN: A company wants to be notified automatically when its AWS spending pattern changes unexpectedly, for example, when a misconfigured service suddenly doubles its daily cost. The company does not want to define thresholds for each service. What should the solutions architect use?
UA: Компанія хоче автоматично дізнаватися про неочікувані зміни витрат — наприклад, коли неправильно налаштований сервіс раптом подвоїв денні витрати, — без порогів для кожного сервісу. Що використати?
A: AWS Budgets with a fixed monthly budget
B*: AWS Cost Anomaly Detection
C: AWS Cost and Usage Report
D: Amazon CloudWatch billing alarms for each service
WHY: Cost Anomaly Detection за допомогою ML вивчає звичні витрати й повідомляє про аномалії без ручних порогів. Budgets (A) і billing alarms (D) потребують порогів, CUR (C) — лише дані для аналізу.

## Q59 | cost
EN: A company has hundreds of Amazon EC2 instances. Many of them seem to be over-provisioned, but the company does not know which instance types would be appropriate. The company wants data-driven recommendations based on actual utilization. What should the solutions architect use?
UA: У компанії сотні інстансів EC2, багато з яких, схоже, завеликі, але невідомо, які типи підійдуть. Потрібні рекомендації на основі фактичного використання. Що використати?
A*: AWS Compute Optimizer
B: AWS Pricing Calculator
C: AWS Budgets
D: Amazon Inspector
WHY: Compute Optimizer аналізує метрики використання й рекомендує оптимальні типи EC2, групи Auto Scaling, томи EBS, розміри Lambda тощо з оцінкою економії. Pricing Calculator (B) оцінює вартість нових рішень, Budgets (C) стежить за витратами, Inspector (D) шукає вразливості.

## Q60 | cost
EN: A research institute publishes large genomics datasets in an Amazon S3 bucket. Other organizations download the data frequently. The institute wants the downloading organizations to pay for the request and data transfer costs. What should the solutions architect configure?
UA: Інститут публікує великі геномні датасети в S3, і інші організації часто їх завантажують. Інститут хоче, щоб за запити й передачу даних платили ті, хто завантажує. Що налаштувати?
A: S3 Transfer Acceleration
B*: Requester Pays on the bucket
C: Presigned URLs with a short expiration time
D: S3 Intelligent-Tiering
WHY: У bucket з Requester Pays плату за запити й завантаження сплачує автентифікований запитувач, а власник — лише за зберігання. Transfer Acceleration (A) додає витрат, presigned URLs (C) не змінюють платника, Intelligent-Tiering (D) оптимізує зберігання.

## Q61 | cost
EN: A company takes daily Amazon EBS snapshots and must keep monthly snapshots for 7 years for compliance. The long-term snapshots are rarely restored, and a restore time of 24–72 hours is acceptable. What is the MOST cost-effective way to store them?
UA: Компанія щодня робить знімки EBS і мусить зберігати щомісячні знімки 7 років. Їх рідко відновлюють, і відновлення за 24–72 години прийнятне. Як зберігати їх найдешевше?
A: Keep all snapshots in the standard snapshot tier.
B*: Move the monthly long-term snapshots to the EBS Snapshots Archive tier.
C: Copy the snapshots to another Region.
D: Convert the snapshots to AMIs.
WHY: EBS Snapshots Archive зберігає повні знімки до 75% дешевше за стандартний рівень, а відновлення триває 24–72 години — саме для довгострокового рідкого зберігання. Стандартний рівень (A) дорожчий, копії в інший регіон (C) і AMI (D) лише додадуть витрат.

## Q62 | cost
EN: Analysts run ad hoc SQL queries on data stored in Amazon S3 a few times per month. The company currently keeps an Amazon Redshift provisioned cluster running 24/7 only for these queries. What is the MOST cost-effective alternative?
UA: Аналітики кілька разів на місяць виконують разові SQL-запити до даних у S3. Для цього цілодобово працює кластер Redshift. Яка альтернатива найекономніша?
A: Resize the Redshift cluster to add more nodes.
B*: Query the data in place with Amazon Athena and pay only for the data scanned.
C: Load the data into Amazon RDS for PostgreSQL.
D: Run an Amazon EMR cluster 24/7.
WHY: Athena не має постійної інфраструктури й бере гроші лише за прочитані дані — ідеально для рідких разових запитів. Більший кластер (A), RDS (C) і постійний EMR (D) коштують гроші навіть тоді, коли запитів немає.

## Q63 | cost
EN: A company runs a steady workload on Amazon EC2 M7g instances in a single Region 24/7. The company is confident that it will keep using this instance family in this Region for 3 years and wants the LARGEST discount. What should the solutions architect recommend?
UA: Стабільне навантаження працює цілодобово на інстансах M7g в одному регіоні, і компанія впевнена, що 3 роки використовуватиме саме це сімейство в цьому регіоні. Потрібна найбільша знижка. Що порадити?
A: A Compute Savings Plan with a 1-year term
B*: An EC2 Instance Savings Plan with a 3-year term for the M7g family in that Region
C: Spot Instances
D: On-Demand Capacity Reservations
WHY: EC2 Instance Savings Plan прив'язаний до сімейства й регіону і дає найбільшу знижку (до ~72%) за 3 роки. Compute Savings Plans (A) гнучкіші, але з меншою знижкою, Spot (C) може перериватися, Capacity Reservations (D) резервують ємність без знижки.

## Q64 | cost
EN: A company manually creates Amazon EBS snapshots for hundreds of volumes, and old snapshots are rarely deleted, so snapshot storage costs keep growing. The company wants to automate snapshot creation and retention with the LEAST operational overhead. What should the solutions architect use?
UA: Компанія вручну робить знімки сотень томів EBS, а старі знімки майже не видаляються, тож витрати на зберігання ростуть. Треба автоматизувати створення знімків і їх зберігання з мінімальними зусиллями. Що використати?
A: A cron job on an EC2 instance that calls the EC2 API
B*: Amazon Data Lifecycle Manager policies that target volumes by tag
C: S3 Lifecycle rules on the bucket that stores the snapshots
D: AWS Config rules
WHY: Data Lifecycle Manager створює знімки за розкладом для томів з певними тегами й автоматично видаляє старі за правилом зберігання (ще один варіант — AWS Backup). Cron на EC2 (A) — власний код і сервер, знімки EBS не лежать у твоєму bucket (C), Config (D) знімків не створює.

## Q65 | cost
EN: A company's Amazon CloudWatch Logs costs are growing quickly. Most log groups were created with default settings, and old logs are rarely queried. Which TWO actions will reduce costs? (Choose TWO.)
UA: Витрати на CloudWatch Logs швидко ростуть. Більшість груп журналів створено з налаштуваннями за замовчуванням, а старі журнали рідко переглядають. Які ДВІ дії зменшать витрати?
A*: Set retention policies on the log groups instead of the default setting of never expiring.
B*: Use the CloudWatch Logs Infrequent Access log class for logs that are rarely queried.
C: Enable detailed monitoring on the EC2 instances.
D: Increase the application logging level to DEBUG.
E: Create a separate log stream for every request.
WHY: За замовчуванням журнали зберігаються вічно — retention обмежує обсяг, а клас Infrequent Access дешевший для рідко переглянутих журналів. Detailed monitoring (C) додає платних метрик, DEBUG (D) збільшує обсяг журналів, окремі потоки (E) нічого не економлять.
