# 補足資料 — 「CloudFrontとS3だけ」の中身は、9個ある（Part 2）

このドキュメントは `design-share-infra-lt-part2.html`（LT資料 Part 2）の内容を、発表を離れて読んでも理解できるレベルまで掘り下げた補足資料です。スライドの番号・見出しに対応させて章立てしています。参照している実ファイルは `.waffle/skills/design-share/infra/cloudformation.yaml`・`infra/cloudfront-function/edge-gate.js`・`scripts/ds.py` です。

前提として、Part 1（`design-share-infra-lt.md`）で説明した「design-shareとは何か」「なぜLambdaを使わない構成にしたか」を踏まえた上で、この文書ではその構成を実現している9つのAWSリソースそれぞれの内部を掘り下げます。

---

## 01. 今日見る9個

`.waffle/skills/design-share/infra/cloudformation.yaml` という1つのYAMLファイルを開くと、次の9種のリソースが定義されています。

1. S3 Bucket（コンテンツ保管）
2. Origin Access Control（CloudFrontだけがS3を読める鍵）
3. CloudFront Distribution（全リクエストの入口）
4. Cache Policy（キャッシュしないという設定）
5. Origin Request Policy（コメントPUT専用）
6. Response Headers Policy（AWSマネージドのセキュリティヘッダー）
7. CloudFront Function（`edge-gate.js` の実行環境）
8. CloudFront KeyValueStore（状態の保存先）
9. CloudFormation Stack（これら全部を束ねる仕組みそのもの）

以降の章で、リクエストが実際に流れる順番でこれらを見ていきます。

---

## 02. S3 — 完全に非公開の倉庫

S3バケットの定義には、次の設定が入っています。

```yaml
PublicAccessBlockConfiguration:
  BlockPublicAcls: true
  BlockPublicPolicy: true
  IgnorePublicAcls: true
  RestrictPublicBuckets: true
```

この4項目は、S3バケットが持ちうる「公開のための抜け道」を1つずつ塞ぐものです。

- `BlockPublicAcls`: バケットやオブジェクトに「誰でも読める」ようなACL（アクセス制御リスト）を新たに設定することを禁止する
- `BlockPublicPolicy`: バケットポリシーで公開設定をすることを禁止する
- `IgnorePublicAcls`: 仮に既存のACLで公開設定がされていても、それを無視する
- `RestrictPublicBuckets`: バケットポリシーが公開アクセスを許可していても、それを無視する

4つとも`true`にすることで、「うっかり公開設定をしてしまう」というヒューマンエラーの余地そのものを断っています。加えて、静的Webサイトホスティング機能（`http://バケット名.s3-website-...`のような、S3を直接Webサーバーとして公開する機能)も設定していません。つまりこのバケットには、CloudFrontを経由しない限り、どこからも直接アクセスする経路が存在しません。

CORS設定もしていません。理由は次章以降で説明する構成——コメントの読み書きは常に「configファイルを配信しているのと同じドメイン（CloudFrontのドメイン）」からの`fetch`だけで完結するため、他のドメインのJavaScriptからこのバケットの中身にアクセスされる必要が最初から無いからです。

保存されているデータの実体は次の通りです。

| パス | 内容 |
|---|---|
| `p/{slug}/index.html` | 生成されたUIパターンのHTML本体 |
| `comments/{slug}/{id}.json` | コメント。1件が1つの独立したS3オブジェクト |
| `design/{slug}.md` | デプロイ元となったDesign.md |
| `gallery/` , `galleries/{gslug}.json` | 共有ギャラリー・名前付きギャラリーの実体データ |

データベースを持たず、すべてが「ファイルとして置かれたJSON/HTML」である、という点が後々の章（特にKeyValueStoreとコメント機能）を理解する鍵になります。

---

## 03. Origin Access Control（OAC） — CloudFrontだけが持つ、S3への鍵

S3バケットは前章の通り完全に非公開です。しかし当然、design-shareの利用者は最終的にHTMLやコメントデータを読めなければなりません。その「非公開のバケットを、CloudFront経由でだけ読めるようにする」仕組みが **Origin Access Control（OAC）** です。

```yaml
OriginAccessControlConfig:
  OriginAccessControlOriginType: s3
  SigningBehavior: always
  SigningProtocol: sigv4
```

`SigningBehavior: always` は、「CloudFrontがS3へリクエストを転送するときは、必ずSigV4（AWSの標準的な署名方式）で署名する」という設定です。この署名によって、S3側は「このリクエストは本当にAWSの正規の仕組み経由で来たものだ」と検証できます。

ここでバケットポリシー側の記述を見てみます。

```yaml
Principal:
  Service: cloudfront.amazonaws.com
Action: s3:GetObject
Resource: !Sub "${ContentBucket.Arn}/*"
Condition:
  StringEquals:
    AWS:SourceArn: !Sub "arn:aws:cloudfront::${AWS::AccountId}:distribution/${Distribution}"
```

### なぜ「confused deputy攻撃」が問題になるのか

ここで、もし`Condition`の部分が無かったら何が起きるかを考えてみます。`Principal: Service: cloudfront.amazonaws.com` だけを見るバケットポリシーは、「CloudFrontというAWSのサービスから、正しく署名されたリクエストであれば許可する」という意味にしかなりません。**「どのCloudFront Distributionからのリクエストか」までは指定していません。**

ここで、悪意のある第三者が次のようなことをするとどうなるでしょうか。

1. 攻撃者は自分自身のAWSアカウントで、新しいCloudFront Distributionを1つ作成する
2. そのDistributionのOriginとして、design-shareのS3バケット名を指定する（バケット名はグローバルに一意で、公開されているURLなどから推測・確認できる場合がある）
3. 攻撃者自身のOACを使い、攻撃者のDistributionからそのバケットへのリクエストにSigV4署名をさせる

この場合、S3側から見ると、リクエストは確かに「`cloudfront.amazonaws.com` というサービスからの、正しくSigV4署名されたリクエスト」です。`Condition`が無ければ、この条件だけを見るポリシーはこれを許可してしまいます。しかも、design-shareの認可ロジックである`edge-gate.js`は攻撃者自身が作った別のDistributionには当然ひも付いていないので、**トークンチェックを丸ごとバイパスして、「非公開のはず」のS3オブジェクトを直接読まれてしまう**ことになります。

これが**confused deputy（惑わされた代理人）攻撃**と呼ばれるパターンです。「deputy（代理人）」とは、ここではAWSの正規サービスであるCloudFrontのことを指します。CloudFrontという信頼された代理人が、正規の持ち主（design-shareのDistribution）のためではなく、攻撃者のリソース（攻撃者のDistribution）のために、意図せずその権限（S3の読み取り許可）を行使してしまう——という構図です。「Principalだけを見て、どのリソースから来たかを見ない」認可設計に共通する落とし穴で、AWSに限らずクラウド全般で繰り返し議論されてきた問題です。

### Conditionがどう塞いでいるか

```yaml
Condition:
  StringEquals:
    AWS:SourceArn: !Sub "arn:aws:cloudfront::${AWS::AccountId}:distribution/${Distribution}"
```

この一文は、「Principalがcloudfront.amazonaws.comであること」に加えて、「**そのリクエストの送信元が、このCloudFormationスタックが作った、この特定のDistribution（`${Distribution}`が展開する具体的なDistribution ID）であること**」までを要求します。攻撃者が自分のDistributionを使ってどれだけ正しくSigV4署名をしても、そのDistributionのARNはdesign-share自身のものとは一致しないため、`Condition`の時点で拒否され、403になります。

design-shareのバケットポリシーには3つのStatement（`CloudFrontRead`・`CloudFrontListComments`・`CloudFrontPutCommentOnly`）がありますが、**すべてに同じ`Condition`が付いています**。これにより、読み取り・一覧取得・コメント書き込みのどの操作についても、「自分自身のDistribution経由でなければ一切許可しない」という一貫した防御になっています。

| Sid | 許可アクション | 範囲 |
|---|---|---|
| CloudFrontRead | `s3:GetObject` | バケット全体 |
| CloudFrontListComments | `s3:ListBucket` | `comments/*` のprefix一覧のみ |
| CloudFrontPutCommentOnly | `s3:PutObject` | `comments/*` 配下のみ（`DeleteObject`は付与していない） |

「削除権限を持たせない」という点も意図的です。誰かが不正にコメントを投稿できたとしても、既存のコメントを消すことはできません。

---

## 04. CloudFront Distribution — 全リクエストの入口

1つのDistributionの中で、URLのパスパターンによって挙動が変わる3つの経路が定義されています。

| Path Pattern | 許可メソッド | 役割 |
|---|---|---|
| デフォルト（`/*`） | `GET`, `HEAD` | パターンHTML・DESIGN.mdスペックシートの閲覧。必ず`edge-gate`を通過する |
| `comments/*` | `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE` | コメント投稿。専用のOrigin Request Policyを付与（05章参照） |
| `comments-list/*` | `GET`, `HEAD` | コメント一覧。`edge-gate`がS3の`ListObjectsV2`呼び出しへ書き換える |

`comments/*` の経路だけ、書き込み系メソッド（`PUT`など）を許可しています。これはCloudFrontの仕様上、パスパターンごとに許可メソッドを制限できるためで、「コメント投稿以外の経路からは、そもそも書き込み系メソッドのリクエスト自体を受け付けない」という制約を、`edge-gate.js`のロジックを待たずにCloudFrontの設定レベルで先に掛けています（Part 1で説明した「多層防御」の一部です）。

その他の設定値:

- **PriceClass_200**: CloudFrontの配信拠点（エッジロケーション）をどの地域まで使うかの価格クラス。北米・欧州に加えてアジアなど主要拠点まで含む中間グレード（全世界の全拠点を使う`PriceClass_All`より安価）
- **HttpVersion: http2and3**: HTTP/2とHTTP/3の両方に対応
- **DefaultRootObject: ""**（空文字）: 通常CloudFrontは「`/`へのアクセスに対して自動的に`index.html`を補完する」設定を持てますが、design-shareではこれを空にしています。理由は、`/p/{slug}/` のような「slugごとのフォルダ」に対する`index.html`補完を、CloudFront標準機能ではなく`edge-gate.js`側で個別に行っているためです（Part 1・06章を参照）。

---

## 05. 3枚のポリシー — Cache / Origin Request / Response Headers

### Cache Policy（キャッシュしないという設計判断）

```yaml
DefaultTTL: 0
MaxTTL: 1
MinTTL: 0
```

CloudFrontの本来の得意技は「一度取得したコンテンツをエッジにキャッシュし、次回以降は高速に返す」ことです。しかしdesign-shareは、このキャッシュ機能を実質的に無効化しています。理由は明快で、トークンが無効化された直後やコメントが新しく投稿された直後に、古いキャッシュ内容が返り続けてしまうと困るからです。「セキュリティに関わる状態（トークンの有効性）を扱うページを、キャッシュで古いまま出し続けるわけにはいかない」という判断です。

この設定により、design-shareにおけるCloudFrontの役割は「コンテンツを高速化するキャッシュ」ではなく、**「世界中からのアクセスを一箇所（正確にはエッジ）に集約し、TLS終端（HTTPSの復号）を行い、`edge-gate.js`という認可ロジックを必ず通す、グローバルなリクエストルーター」**という位置づけに変わっています。CDNをキャッシュ目的ではなく、エッジでの認可・ルーティング基盤として使う、という発想の転換がここでの面白さです。

### Origin Request Policy（コメントPUT専用の自作ポリシー）

```yaml
HeadersConfig:
  HeaderBehavior: whitelist
  Headers: [content-type]
```

CloudFrontがS3のようなオリジンへリクエストを転送する際、「どのヘッダーをオリジンまで転送するか」を指定するのがOrigin Request Policyです。design-shareではAWSがあらかじめ用意している汎用の管理ポリシー（`AllViewer`など、多くのヘッダーを丸ごと転送するもの）が使えませんでした。理由は、S3オリジンがそうした汎用ポリシーに含まれる一部のヘッダーを許可しないためです。そこで、コメント投稿（`PUT`）に本当に必要な `content-type` ヘッダーだけを転送する専用ポリシーを1枚作りました。

ここで重要な実装上の注意点があります。SigV4署名に本来必要な`x-amz-content-sha256`（リクエストボディのハッシュ値を示すヘッダー）は、あえてこのポリシーに含めていません。OAC（`SigningBehavior: always`）が署名処理の中でこのヘッダーをネイティブに扱ってくれるため、Origin Request Policyでこれを転送しようとすると、逆にCloudFrontから「許可されないヘッダー」として拒否されてしまうという落とし穴があるからです。「署名に関わるヘッダーは自分で転送しようとしない」というのが、OACと組み合わせるときの実践的な注意点です。

### Response Headers Policy（AWSマネージドの活用）

CloudFrontの`DefaultCacheBehavior`と`comments/*`・`comments-list/*`の両方に、`ResponseHeadersPolicyId: 67f7725c-6f97-4210-82d7-5512b31e9d03` というIDが指定されています。これはAWSがあらかじめ用意している管理ポリシー「SecurityHeadersPolicy」で、これをアタッチするだけで、`X-Content-Type-Options: nosniff`（ブラウザにMIMEタイプの誤判定をさせない）や `X-Frame-Options: DENY`（他サイトの`<iframe>`に埋め込まれるクリックジャッキング対策）といった、Webセキュリティの定番ヘッダー群を、コードを1行も書かずに全レスポンスへ自動付与できます。「よくあるセキュリティ設定は自作せず、AWSが用意しているものにそのまま乗る」という判断です。

---

## 06. CloudFront Functions — edge-gate.js、10KBの中身

Part 1では`edge-gate.js`が担う役割（トークン照合・無効化判定・PUTの検査・コメント一覧の書き換え）を説明しました。ここでは、その実行環境である**CloudFront Functions（通称cf2）**そのものの制約と、その中に収まっている理由を数字で見ます。

- **291行**（コメント込みのソースコード全体の行数）
- **8.6KB**（`ds.py update-function` がデプロイ時に行コメントと空行を取り除いた後の実際の配置サイズ。実測値）
- **10KB**（CloudFront Functionsのランタイムが許容するコードサイズの上限。余白は約1.4KB）
- **最大約6回**（1回のアクセスあたりのKeyValueStore読み取り回数の上限。通常のアクセスは1回で完結する）

CloudFront Functionsは、Lambda@Edgeよりもさらに軽量な実行環境として設計されており、次のような制約があります。

- 実行できるコードはJavaScript（ES5.1相当のサブセット）に限られる
- 外部ネットワークへのI/Oは基本的にできない（唯一の例外がKeyValueStoreへの読み取りアクセス）
- 実行時間・メモリの予算が非常に小さい（マイクロ秒オーダーでの実行が前提）
- イベントタイプは`viewer-request`（クライアントからのリクエストがCloudFrontに届いた直後）と`viewer-response`（レスポンスをクライアントへ返す直前）の2種類のみで、オリジンとの通信を伴う`origin-request`/`origin-response`には対応していない（そちらはLambda@Edgeの領分）

`edge-gate.js`は`viewer-request`のタイミングで動作し、「オリジン（S3）に問い合わせる前に、認可されていないリクエストをその場で弾く」という役割に徹しています。この制約の中に収めるため、KeyValueStoreへの問い合わせ回数を切り詰め、複雑な処理（HTMLのテンプレート展開など）は最小限に留める設計になっています。

デプロイの実際の流れとしては、`scripts/ds.py`の`update-function`コマンドが、リポジトリ上の可読性重視の`edge-gate.js`（コメント・空行あり）を読み込み、行コメントと空行を削ってから、実際にCloudFront Functionへ反映します。「開発者が読むためのソース」と「実際にエッジで実行されるコード」を分けることで、10KBという厳しい制約の中でも可読性を犠牲にしないようにしています。

---

## 07. CloudFront KeyValueStore — 書き込みを守るETag

Part 1で、design-shareが保持しているキーの一覧（`token:{slug}`など）を説明しました。ここでは「書き込みがどう安全に行われているか」を掘り下げます。

`scripts/ds.py`の実装（`kvs_etag`・`kvs_put`関数）を見ると、KeyValueStoreへの書き込みは次の2段階で行われています。

```python
def kvs_etag(ctx):
    return ctx.kvs.describe_key_value_store(KvsARN=ctx.kvs_arn)["ETag"]

def kvs_put(ctx, key, value):
    ctx.kvs.put_key(KvsARN=ctx.kvs_arn, Key=key, Value=value, IfMatch=kvs_etag(ctx))
```

1. `describe_key_value_store`を呼び、その時点のKeyValueStore全体のETag（版数を示す文字列）を取得する
2. `put_key`を呼ぶ際、そのETagを`IfMatch`パラメータとして渡す。KeyValueStore側は、渡されたETagが「現在の実際のETagと一致する場合にのみ」書き込みを実行し、一致しなければ（＝自分がETagを取得した後に、誰か他のプロセスが別の書き込みを行っていた場合）エラーを返す

これは**楽観的並行性制御（optimistic concurrency control）**と呼ばれる仕組みで、DynamoDBの条件付き書き込み（`ConditionExpression`を使ったUpdateItemなど）と全く同じ発想です。「書き込む前に必ずロックを取る」のではなく、「書き込む瞬間に、想定通りの状態のままだったかを確認し、想定と違っていれば失敗させて呼び出し側にリトライを促す」という設計です。

ここに、Part 1で触れた面白い符合があります。design-shareは「DynamoDBを使わない」という選択をしましたが、複数の管理操作（例えば同時に別々の端末からトークンをローテーションしようとするようなケース）が競合したときに正しく振る舞うためには、結局DynamoDBが得意とする「条件付き書き込み」という考え方が必要になり、それをKeyValueStoreのETag機能を使って自前で再現しています。**「サービスとしてのDynamoDBは消えたが、DynamoDB的な設計思想は生き残っている」**というのが、このインフラ最大の発見の一つです。

もう一つの重要な特性は、**結果整合性（eventual consistency）**です。KeyValueStoreに書き込んだ内容は、世界中のCloudFrontエッジロケーションへ非同期に複製されます。この複製が完了するまでには数秒から数十秒かかることがあり、design-shareではこれを踏まえて「トークンを無効化・再発行した直後は、少し待ってから再読み込みしてほしい」と利用者に案内する設計になっています(SKILL.mdのガードレール項目にも明記)。「即座に反映される」という誤った期待を持たせないことも、設計の一部です。

---

## 08. CloudFormation — 1枚のYAMLがすべてを知っている

ここまで説明してきた8つの部品（S3・OAC・CloudFront Distribution・3枚のポリシー・CloudFront Function・KeyValueStore）は、すべて`infra/cloudformation.yaml`という1つのテンプレートファイルの中で、`Resources`セクションに定義されています。CloudFormationはAWSの「インフラをコードとして記述し、まとめてデプロイ・削除できる」仕組み（Infrastructure as Code）です。

このテンプレートの`Outputs`セクションでは、構築後に必要となる値が定義されています。

| Output名 | 内容 |
|---|---|
| `DistributionDomain` | 共有URLのベースとなるドメイン名 |
| `BucketNameOut` | コンテンツを保管しているバケット名 |
| `TokenStoreArn` | KeyValueStoreのARN（他のAWS API呼び出しで必要になる識別子） |
| `EdgeGateFunctionName` | `edge-gate.js`の反映先となるCloudFront Function名 |

`scripts/ds.py`の`init`コマンドは、このテンプレートを使って実際にCloudFormationスタックを作成し（すでに環境がある場合は既存スタックを再利用し)、`Outputs`から得られた値を`design-share.env`というテキストファイルに書き出します。以降、`deploy`・`rotate`・`disable`など、design-shareのすべてのコマンドはこの`design-share.env`を読み込んで、対象のバケット・Distribution・KeyValueStoreを特定します。

つまり全体としては、**「テンプレート（CloudFormation）→ 出力値（Outputs）→ 環境ファイル（design-share.env）→ CLIコマンド」**という一本道になっており、「ARNをコンソールからコピーしてスクリプトに手で貼り付ける」といった、ヒューマンエラーの入り込む工程が存在しません。環境を壊したい場合も、`destroy`コマンドが同じスタックを対話式に削除します(CloudFront Distributionの無効化待ちのため15〜20分程度かかることがあります)。

---

## 09. まとめ図 — 1本のGETリクエストの一生

最後に、ここまでバラバラに説明してきた9つの部品が、実際に1本のリクエストの中でどう連携しているかを、`GET /p/{slug}/` へのアクセスを例に時系列で追います。

1. **Browser → CloudFront**: 利用者のブラウザが `GET /p/{slug}/` をリクエストする
2. **CloudFront Function → KeyValueStore**: `edge-gate.js`が起動し、`token:{slug}`をKeyValueStoreへ問い合わせる
3. **KeyValueStore → CloudFront Function**: 現在の有効トークン（ETagで保護された値）が返る
4. **CloudFront Function内での判定**: ブラウザが持つCookieと突き合わせ、一致すれば許可する。**Cache Policyのキャッシュ時間が実質0**なので、この判定は毎回必ず実行される（古い許可判定がキャッシュされて使い回されることがない）
5. **CloudFront → S3**: 許可されたリクエストを、OACによるSigV4署名付きでS3へ転送する
6. **S3 → CloudFront**: 非公開のオブジェクトが返される。もしOACの署名（および正しいバケットポリシーのCondition）が無ければ、S3は`AccessDenied`を返してここで失敗する
7. **CloudFront内での加工**: Response Headers Policyが、返却する直前のレスポンスにセキュリティヘッダーを付与する。なお、コメントの投稿（`PUT`）の場合はこの手前でOrigin Request Policyが`content-type`ヘッダーだけをS3へ転送する処理が挟まる
8. **CloudFront → Browser**: 完成したレスポンスが利用者のブラウザへ届く

そして、この一連の流れを成立させている土台——各リソースの定義そのもの、リソース間の参照関係（DistributionのARNをバケットポリシーのConditionに埋め込む、といった配線）——を担っているのが**9番目の部品、CloudFormation**です。

9つの部品はどれも単体では地味な機能ですが、組み合わさることで「認証つき・コメント可・即時失効可能なWebアプリケーション」が、常時稼働するコンピュートを1つも使わずに実現されています。
