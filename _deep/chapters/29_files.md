---
id: files
module: Сховища
title: Спільні файли — Amazon EFS і сімейство Amazon FSx
short: EFS і FSx
emoji: 📁
domains: resilient, performance, cost
svc: efs, fsx, fsxwin, fsxlustre, fsxontap, fileproto
---
> 🎬 **Історія Хмаринки.** Три «файлові» болі. Перша: старий модуль сайту зберігає завантажені продавцями файли в звичайну папку на диску — а тепер серверів шість, і кожен бачить лише свою папку. Друга: у бухгалтерії Windows-комп'ютери працюють зі спільним мережевим диском `\\buh\docs` з правами за обліковими записами Active Directory — і його треба перенести в хмару. Третя: аналітики хочуть навчати модель прогнозу попиту на терабайтах даних з S3, і їм потрібна дуже швидка файлова система. Три задачі — три різні файлові сервіси.

> 🖼️ **Образ.** **EFS** — спільна шафа з документами в коридорі офісу на кількох поверхах (зонах): кожен Linux-сервер відкриває її і бачить те саме, а шафа сама росте, коли документів більшає. **FSx** — набір спеціалізованих архівів: **Windows** — архів за правилами Windows з перепустками Active Directory; **Lustre** — гоночний конвеєр для суперкомп'ютерів; **NetApp ONTAP** — універсальний архів, що говорить усіма мовами; **OpenZFS** — знайомий архів для тих, хто вже звик до ZFS.

## Навіщо файлове сховище

Нагадування з [розділу 4](#ch/it-data/storage-types): **блочне** сховище (EBS) — диск одного сервера в одній AZ; **об'єктне** (S3) — необмежений склад через HTTP, без «монтування». **Файлове** — спільна файлова система, яку **одночасно** монтують багато серверів і працюють з нею як зі звичайною папкою: відкрити файл, дописати рядок, заблокувати файл від одночасного запису. Мова доступу — **протокол**: **NFS** для Linux, **SMB** для Windows.

## Amazon EFS {#efs}

**Amazon Elastic File System** — керована **NFS**-файлова система для **Linux**:

- **спільна**: тисячі клієнтів одночасно — сервери EC2, контейнери **ECS і EKS**, функції **Lambda**, навіть сервери в офісі через VPN/Direct Connect;
- **еластична**: росте й зменшується автоматично до петабайтів; платиш за **фактично збережені** гігабайти (без попереднього виділення);
- **регіональна** (Regional): дані зберігаються **в кількох AZ**, а в кожній AZ створюється **mount target** — мережевий інтерфейс у підмережі, через який клієнти монтують систему. Або **One Zone** — дешевше, дані в одній AZ.

<figure class="diagram" data-caption="EFS: одна файлова система для серверів у кількох AZ">
<div class="dg-box"><div class="dg-label">📁 EFS Regional · дані в кількох AZ</div>
<div class="dg-azs">
<div class="dg-box dg-az"><div class="dg-label">AZ a</div><div class="dg-nodes"><span class="dg-node net">mount target (ENI, SG: NFS 2049)</span><span class="dg-node cmp">EC2</span><span class="dg-node cmp">ECS task</span></div></div>
<div class="dg-box dg-az"><div class="dg-label">AZ b</div><div class="dg-nodes"><span class="dg-node net">mount target (ENI, SG: NFS 2049)</span><span class="dg-node cmp">EC2</span><span class="dg-node cmp">Lambda</span></div></div>
</div></div>
<figcaption>Усі бачать ті самі файли. Security Group mount target має дозволяти вхідний <b>TCP 2049 (NFS)</b> від Security Group клієнтів — найчастіша причина «EFS не монтується».</figcaption>
</figure>

### Продуктивність і вартість EFS

- **Throughput modes:** **Elastic** (рекомендовано: пропускна здатність автоматично під навантаження, оплата за використане), **Provisioned** (фіксована пропускна здатність незалежно від розміру), **Bursting** (залежить від обсягу даних, накопичує кредити).
- **Performance mode:** General Purpose — найнижча затримка, стандарт для більшості задач.
- **Класи зберігання:** **Standard**, **Infrequent Access (IA)** і **Archive** + **lifecycle management**: файли, яких не відкривали N днів, автоматично переходять у дешевші класи (і за бажанням повертаються в Standard при зверненні). EFS за гігабайт дорожча за EBS — lifecycle суттєво знижує рахунок.
- **Безпека:** шифрування at rest (KMS) і в дорозі (TLS через EFS mount helper), POSIX-права, **IAM-авторизація** клієнтів, **access points** — окремі «входи» для застосунків з фіксованим користувачем POSIX і кореневою папкою.
- **Надійність:** **EFS Replication** — копія файлової системи в іншому регіоні (RPO — хвилини); бекапи — AWS Backup.

## Amazon FSx: чотири спеціалізовані файлові системи {#fsx}

### FSx for Windows File Server {#fsx-windows}

Повноцінний **Windows-файловий сервер**, керований AWS:

- протокол **SMB**, файлова система **NTFS**, права **ACL Windows**;
- інтеграція з **Active Directory** — AWS Managed Microsoft AD або **власним** AD в офісі;
- **DFS Namespaces**, тіньові копії (Previous Versions), дедуплікація, квоти;
- **Multi-AZ** розгортання для високої доступності;
- доступ з офісу через VPN/Direct Connect.

Для чого: спільні диски Windows-користувачів, домашні папки, застосунки на .NET і SharePoint, спільне сховище для кластерів Microsoft SQL Server. **EFS для Windows не підходить** — це NFS і Linux.

### FSx for Lustre {#fsx-lustre}

Файлова система для **високопродуктивних обчислень**: **сотні ГБ/с**, мільйони IOPS, затримка менше мілісекунди.

- **Інтеграція з S3**: файлова система «підключається» до bucket — файли підтягуються з S3 при першому зверненні, а результати записуються назад у S3.
- **Scratch** — тимчасова, найдешевша, без реплікації (для короткочасних обчислень); **Persistent** — довготривала, з реплікацією в межах AZ.
- Лише **Linux**.

Для чого: **HPC, навчання ML-моделей, рендеринг, моделювання, геноміка, фінансові розрахунки**.

### FSx for NetApp ONTAP {#fsx-ontap}

Керований **NetApp ONTAP** — «швейцарський ніж»:

- **NFS, SMB і iSCSI одночасно** — Linux, Windows і macOS до тих самих даних;
- знімки, миттєві клони (FlexClone), реплікація SnapMirror, дедуплікація й стиснення, автоматичне перенесення холодних даних у дешевий рівень;
- **Multi-AZ**.

Для чого: **міграція з NetApp** в офісі, змішані Linux/Windows середовища, бази даних на iSCSI.

### FSx for OpenZFS {#fsx-openzfs}

Керована **OpenZFS** з доступом по **NFS**: знімки, клони, стиснення, низька затримка. Для чого: **міграція з ZFS** і Linux-файлових серверів без змін у застосунках.

## Що обрати {#choose}

| Вимога | Вибір |
|---|---|
| Спільна файлова система для **Linux** у кількох AZ, еластична, без керування | **Amazon EFS** |
| Спільна папка для **Windows** з **Active Directory**, SMB, NTFS | **FSx for Windows File Server** |
| **HPC / ML**, сотні ГБ/с, дані лежать у **S3** | **FSx for Lustre** |
| **NFS + SMB + iSCSI** одночасно, міграція з **NetApp** | **FSx for NetApp ONTAP** |
| Міграція з **ZFS**, NFS з низькою затримкою | **FSx for OpenZFS** |
| Диск для одного сервера (база, ОС) | **EBS** ([розділ 21](#ch/ec2-disks)) |
| Необмежений склад файлів через HTTP | **S3** ([розділ 27](#ch/s3)) |

:::mnemo 🧠 Протокол підказує сервіс
**NFS + Linux + кілька AZ → EFS. SMB + Windows + AD → FSx for Windows. «HPC» чи «Lustre» чи «сотні ГБ/с» → FSx for Lustre. «NetApp» або «NFS і SMB одночасно» → FSx for ONTAP. «ZFS» → FSx for OpenZFS.**
:::

## Рішення для Хмаринки {#design}

- Файли, які завантажують продавці через старий модуль сайту, → **EFS Regional** з **access point** для застосунку; усі шість серверів (і згодом контейнери) бачать одну папку; lifecycle → IA через 30 днів.
- Спільний диск бухгалтерії → **FSx for Windows File Server Multi-AZ**, інтегрований з корпоративним AD через AWS Managed Microsoft AD (з довірою до офісного AD); офіс підключається через VPN.
- Навчання моделі прогнозу попиту → **FSx for Lustre (Scratch)**, прив'язана до bucket з історією продажів, на час тренування.

:::lab 🧪 Спробуй у справжньому AWS: одна EFS для двох серверів
**Вартість:** кілька МБ в EFS і два маленькі сервери на 30 хвилин — центи. **Час:** 30 хвилин.
1. Запусти два сервери Amazon Linux 2023 у **різних AZ** твоєї VPC (як у [розділі 19](#ch/ec2)). Security Group серверів — `sg-efs-clients`.
2. Створи Security Group `sg-efs` з вхідним правилом **NFS (2049)**, джерело — `sg-efs-clients`.
3. **EFS → Create file system → Customize**: тип **Regional**, throughput **Elastic**, lifecycle — IA через 30 днів. На кроці Network для mount targets в обох AZ обери Security Group **`sg-efs`**.
4. На **кожному** сервері виконай (підстав ID своєї файлової системи `fs-…`):
```bash
sudo dnf install -y amazon-efs-utils
sudo mkdir -p /mnt/shared
sudo mount -t efs -o tls fs-0123456789abcdef0:/ /mnt/shared
df -h /mnt/shared
```
5. На першому сервері: `echo "Замовлення з AZ a" | sudo tee /mnt/shared/hello.txt`. На другому: `cat /mnt/shared/hello.txt` — файл той самий.
6. Навмисно прибери правило 2049 з `sg-efs` і спробуй змонтувати ще раз на новій папці — отримаєш таймаут. Поверни правило.
**Прибери за собою:** `sudo umount /mnt/shared` на обох серверах; видали файлову систему EFS, сервери, обидві Security Groups.
:::

#### 💡 Запам'ятай

- **EFS** — керована **NFS** для **Linux**; тисячі клієнтів (EC2, ECS, EKS, Lambda, on-prem); **Regional** (кілька AZ, mount target у кожній) або **One Zone**; росте сама; оплата за збережене.
- EFS: throughput **Elastic** (рекомендовано) / Provisioned / Bursting; класи **Standard, IA, Archive** + lifecycle; access points; replication в інший регіон; SG з **TCP 2049**.
- **FSx for Windows** — SMB, NTFS, **Active Directory**, DFS, Multi-AZ.
- **FSx for Lustre** — HPC/ML, сотні ГБ/с, **інтеграція з S3**; Scratch чи Persistent; Linux.
- **FSx for NetApp ONTAP** — **NFS + SMB + iSCSI**, міграція з NetApp, Multi-AZ.
- **FSx for OpenZFS** — міграція з ZFS, NFS.

#### 🎯 Як питають на іспиті

- Спільна файлова система для багатьох Linux-серверів у різних AZ → **Amazon EFS**
- Контейнерам ECS/EKS або функціям Lambda потрібне спільне постійне файлове сховище → **Amazon EFS**
- Спільна файлова система для Windows з інтеграцією з Active Directory → **FSx for Windows File Server**
- HPC або навчання ML з дуже високою продуктивністю, дані в S3 → **FSx for Lustre**
- Потрібні NFS і SMB одночасно або міграція з NetApp → **FSx for NetApp ONTAP**
- Файли в EFS майже не відкривають після 30 днів, рахунок росте → **EFS lifecycle management → IA / Archive**
- Сервери не можуть змонтувати EFS (таймаут) → **дозволити TCP 2049 у Security Group mount target**
- Найдешевша EFS для dev-середовища, висока доступність не потрібна → **EFS One Zone**
- Тимчасова швидка файлова система на час обчислень, найдешевше → **FSx for Lustre Scratch**
- Копія файлової системи EFS в іншому регіоні для DR → **EFS Replication**

#### ⚠️ Пастки

- EFS — **не** для Windows (NFS, Linux); для Windows — FSx for Windows File Server.
- EBS не можна одночасно підключити до багатьох серверів у різних AZ — для спільних файлів EFS.
- FSx for Lustre Scratch не реплікує дані — лише для тимчасових обчислень.
- EFS за гігабайт дорожча за EBS і S3 — без lifecycle рахунок швидко росте.

## ✅ Перевір себе

:::quiz
? Вебзастосунок на десяти Linux-серверах у трьох AZ має зберігати завантажені користувачами файли так, щоб усі сервери бачили їх одночасно. Обсяг непередбачуваний. Що обрати?
- Том EBS gp3, підключений до всіх серверів
+ Amazon EFS (Regional)
- Instance store на кожному сервері
- FSx for Windows File Server
= EFS — спільна NFS-файлова система для Linux, доступна з кількох AZ, що росте автоматично. EBS живе в одній AZ (Multi-Attach — лише io1/io2 і в межах AZ), instance store — локальний і тимчасовий.

? Компанія переносить Windows-застосунки, що використовують спільні папки SMB з правами користувачів Active Directory. Що обрати?
- Amazon EFS
+ Amazon FSx for Windows File Server
- Amazon FSx for Lustre
- Amazon S3 з bucket policy
= FSx for Windows File Server дає SMB, NTFS і інтеграцію з Active Directory. EFS працює з NFS і Linux, Lustre — для HPC.

? Дослідницька команда навчає модель на 200 ТБ даних, що лежать у S3. Потрібна файлова система з сотнями ГБ/с пропускної здатності лише на час навчання, якомога дешевше. Що обрати?
+ FSx for Lustre (Scratch), пов'язана з bucket S3
- EFS з Provisioned throughput
- FSx for NetApp ONTAP
- EBS io2 Block Express
= FSx for Lustre інтегрується з S3 і дає продуктивність HPC. Scratch-розгортання — найдешевше для тимчасових задач (без реплікації).

? Компанія переносить в AWS сховище NetApp, до якого одночасно звертаються Linux-сервери по NFS і Windows-сервери по SMB, а бази даних — по iSCSI. Що обрати?
- EFS і FSx for Windows окремо з синхронізацією
+ FSx for NetApp ONTAP
- FSx for OpenZFS
- S3 з кількома Access Points
= FSx for NetApp ONTAP підтримує NFS, SMB і iSCSI одночасно і має звичні можливості NetApp — ідеально для міграції.

? Сервери EC2 у приватній підмережі не можуть змонтувати EFS — команда mount завершується таймаутом. Що найімовірніше?
+ Security Group mount target не дозволяє вхідний TCP 2049 від серверів
- EFS не підтримує приватні підмережі
- Потрібна публічна IP-адреса для кожного сервера
- EFS треба спершу реплікувати в інший регіон
= Клієнти звертаються до mount target по NFS (TCP 2049). Якщо Security Group mount target не дозволяє цей порт від серверів, з'єднання не встановлюється.

? Файли в EFS активно використовують перший тиждень, а потім майже не відкривають, але мають лишатися доступними. Як знизити вартість з мінімальними зусиллями?
+ Увімкнути EFS lifecycle management з переходом у Infrequent Access (і Archive)
- Перейти на EFS One Zone з перенесенням даних вручну
- Щотижня копіювати файли в Glacier скриптом
- Перейти на FSx for Lustre
= Lifecycle management автоматично переносить файли, яких давно не відкривали, у дешевші класи EFS; файли лишаються доступними в тій самій файловій системі.

? Які твердження про Amazon EFS правильні? (Оберіть 2)
+ Файлову систему можуть одночасно монтувати тисячі клієнтів, зокрема ECS, EKS і Lambda
- EFS розрахована на Windows-клієнтів через SMB
+ Оплата йде за фактично збережені дані, розмір задавати наперед не потрібно
- EFS може бути кореневим диском сервера EC2
- Регіональна EFS зберігає дані лише в одній AZ
= EFS — спільна еластична NFS для Linux-клієнтів: платиш за збережене, розмір росте сам. Для Windows — FSx, кореневий диск — EBS, а Regional EFS зберігає дані в кількох AZ.
:::
