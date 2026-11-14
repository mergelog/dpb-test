# Dependabot設定例の動作検証

確認日: 2026年11月14日。**17パターンの設定検証と15種類の公式updaterテストがすべて成功しました。** [最終実行ログ](https://github.com/mergelog/dpb-test/actions/runs/43577956660)、[ケース別の実測結果JSON](dependabot-verification-results.json)から確認できます。検証したコードはコミット `cc4514f` です。

追加検証後のコミット`994fea6`でも[全16ジョブの再実行](https://github.com/mergelog/dpb-test/actions/runs/43580394195)が成功しました。以下にはGitHub実サービスでの追加確認も記録しています。

対象は [.github/dependabot.examples.yml.disabled](../.github/dependabot.examples.yml.disabled) の9ケースと、設定ファイル内のコメントアウトした代替設定です。有効なDependabot設定値、ブランチ保護、セキュリティ更新の有効・無効は変更していません。

## 検証方法

1. コメント内のYAMLを実際に取り出し、独立した設定として読み込む。キー重複も拒否する。
2. 元の9ケース、コメントから作る7パターン、有効な設定の計17パターンを、固定したSchemaStoreスキーマで検証する。
3. 公式Dependabot CLI v1.97.0と公式updater/proxyをGitHub Actionsで実行する。
4. npm、GitHub Actions、複数ディレクトリ、HTTPS registryのテスト用ファイルを入力し、提案される依存・バージョン・PR単位・変更ファイルを検証する。

CLIは更新処理を実行し、PR作成要求をテスト用APIへ記録します。実リポジトリへテスト用更新PRを作成・マージしません。GitHubのスケジュールや通知処理まで再現する機能ではありません。[公式CLIの説明](https://github.com/dependabot/cli#dependabot-update)

CLIへ渡すのは `dependabot.yml` そのものではなく、検証スクリプトで対象オプションを変換したジョブ定義です。グループ化・除外・更新戦略などのupdater動作を検証し、GitHubサービスが管理する項目は下表で区別しています。[公式CLI：ジョブ定義](https://github.com/dependabot/cli#job-description-file)

スキーマはSchemaStoreのコミット `e2606e03284e60792672dc9e7e930f3c496c5c3d` を使用します。これはGitHubサービスそのものの検証APIではありません。[使用するスキーマ](https://github.com/SchemaStore/schemastore/blob/e2606e03284e60792672dc9e7e930f3c496c5c3d/src/schemas/json/dependabot-2.0.json)

## updaterテストの実測結果（全15ケース成功）

| テスト | 確認できた結果（PR件数はdry-runの作成提案） |
| --- | --- |
| `all` | 5依存を1件のPRへまとめ、`chore(deps):` のタイトルを生成する |
| `split` | Angular、本番依存、開発依存の3件に分かれる |
| `patch` | パッチ更新の4依存だけを提案し、tslibのマイナー更新を除外する |
| `ignored-version` | RxJS 7.8.2も除外し、3依存だけを提案する |
| `production` | 開発依存を除外し、本番依存の3依存だけを提案する |
| `lockfile-pinned` | 完全固定の範囲を超える更新を提案しない（0件） |
| `lockfile-range` | 5件の提案はいずれもlockfileだけを更新し、package.jsonを変えない |
| `increase-if-necessary` | 5件の提案で、既存範囲が新バージョンを許容するpackage.jsonを変えない |
| `cooldown-excluded` | コメント内の`exclude: ["*"]`を有効化すると5依存をまとめて更新する |
| `actions` | 2つのActions更新を1件にまとめ、メジャー更新を除外する |
| `security` | 仮の脆弱性情報に対する2依存の修正を1件にまとめる |
| `directories` | `/apps/web`・`/packages/shared`で各5件、計10件を提案し、除外したfixturesを変更しない |
| `registry` | 認証付きHTTPS registryから1.0.0→1.0.1の更新を提案する |
| `cooldown-withheld` | 公開直後の仮パッケージをクールダウンにより更新しない（0件） |
| `cooldown-excluded-fresh` | 同じ公開直後の仮パッケージを除外指定によって即時候補にする（1件） |

npmの基本fixtureにはAngular compiler/core 20.3.34、RxJS 7.8.1、tslib 2.8.1、TypeScript 5.9.2を使用します。更新後はそれぞれ20.3.35、7.8.2、2.9.1、5.9.3になることを確認します。

将来のリリースによる変動を抑えるため、現在のメジャー内の後続バージョンをテスト側で除外します。新しいメジャーはこの上限では除外せず、サンプルのメジャー除外ルールで防げるかを確認します。

## GitHub実サービスで追加確認した結果

以下はCLIのdry-runとは別に、実際のPRとGitHub Actionsで確認しました。[実測結果JSON](dependabot-live-verification-results.json)に確認時刻・対象コミット・レビュー・マージ結果を記録しています。

### 承認後の自動マージ

- 対象: [tslib更新PR #4](https://github.com/mergelog/dpb-test/pull/4)、`2.8.1 → 2.9.1`。変更は`package.json`と`package-lock.json`のみ。
- コミット`b5a01f3bd642d263dd1e201343021a547fb6e1b8`を別worktreeで取得し、`npm ci --ignore-scripts --no-audit --no-fund`と`npm run build`が成功。
- 承認前は`open`・`blocked`・レビューなしで、自動マージの予約だけが有効。
- `mergelog`でAPIからApproveを提出した時刻は`2026-11-14 09:15:24 UTC`。GitHubが`09:15:39 UTC`に自動Squash mergeしたことを確認。手動マージ・マージAPIの呼び出しは行っていません。
- マージコミットは`1510a62a1bd075edded10570c0875fe1c8703f8d`。承認1件必須・管理者にも適用するブランチ保護は維持しています。

### ワークフローによる自動マージ予約

[RxJS更新PR #2](https://github.com/mergelog/dpb-test/pull/2)を閉じた時点で予約が解除されたことを確認し、再オープンしました。`reopened`イベントで[自動マージのワークフロー](https://github.com/mergelog/dpb-test/actions/runs/43579846705)が成功し、`github-actions`がSquash mergeの予約を有効にしました。その後も`OPEN`・`REVIEW_REQUIRED`・`BLOCKED`であり、承認なしではマージされていません。

この確認はアカウント`mergelog`のAPI操作によるレビューです。ブラウザ上での手作業による承認操作を試したという意味ではありません。新規作成イベントによる起動は、再オープンイベントとは区別して扱います。

### 設定例を有効化した実PRの確認

[検証専用リポジトリ](https://github.com/mergelog/dpb-test-live-verification-20261114)に、意図的に古い依存を入れたfixtureを配置しました。設定はデフォルトの`control`ブランチで管理し、通常の確認先は承認1件必須の`main`です。元リポジトリの設定例をコピーし、ディレクトリ・対象ブランチ・検証用スケジュールを変更しています。

| 項目 | 実測結果・証跡 |
| --- | --- |
| 全依存のグループ化 | [PR #8](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/8)でRxJS・tslib・TypeScriptを1件に集約 |
| 接頭辞・ラベル・担当者 | 同PRのタイトルが`chore(deps):`、ラベルが`dependencies`、担当者が`mergelog` |
| 新規PRでの自動マージ予約 | `main`向けの新規Dependabot PRでワークフローが実行され、承認前は予約して待機 |
| PR上限の変更 | 上限1では[PR #3](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/3)の1件。2へ増やすと[PR #9](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/9)が追加され、2件になる |
| 停止・再開 | 上限0ではPRなし。1へ戻すと[PR #10](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/10)を作成。再度0にしても既存PRは残る |
| `lockfile-only` | [PR #5](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/5)は`package-lock.json`だけを変更 |
| `target-branch` | [PR #7](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/7)は`dependency-testing`向けに作成。`main`専用の自動マージ予約は適用されない |
| セキュリティ更新 | 通常更新の上限0でも実アラートから修正PRを作成。[PR #11](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/11)で2依存をグループ化し、先行の個別PR #1・#2をDependabot自身がクローズ |
| 再ベース停止 | 同じ競合を作ると通常設定の[PR #3](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/3)はhead更新・競合解消。最初から`disabled`の[PR #6](https://github.com/mergelog/dpb-test-live-verification-20261114/pull/6)はhead不変・競合ありのまま |

セキュリティ更新には、実アドバイザリに該当する`lodash 4.17.20`と`minimist 1.2.5`を検証用入力として使いました。[lodashのアドバイザリ](https://github.com/advisories/GHSA-35jh-r3h4-6jhm)、[minimistのアドバイザリ](https://github.com/advisories/GHSA-xvch-5gv4-984h)。本体アプリの依存に追加したものではありません。設定が無効だった時点では個別PRが作成され、設定修正後のグループ化で置き換わることも観測しました。

再ベースの比較では、PR #8に検証用コミットを追加し、2ケースのRxJS指定を`7.8.1`から同じ固定版を表す`=7.8.1`へ変更して、既存更新PRと同じ行に競合を作りました。承認後の自動マージで取り込み、通常設定と停止設定を比較しています。初期のグループ化・ラベル・担当者の観測は、この追加コミットより前です。

終了時は専用リポジトリの通常更新上限を全件0にし、security updatesと未マージPRの自動マージ予約を無効化しました。設定検証の成功と実行中ジョブがないことを確認してアーカイブしています。コード・PR・ログを証跡として参照できます。再利用にはアーカイブ解除と設定の復元が必要です。

## 実サービスでの確認範囲と残る前提

| 項目 | 今回の確認範囲・残る前提 |
| --- | --- |
| 曜日・時刻・タイムゾーン | スキーマと公式仕様を照合。実際の曜日・時刻を待つ運用試験は行わない |
| PR上限・停止・再開 | 上記の実PRで確認済み。上限0は既存PRを閉じる機能ではない |
| ラベル・担当者 | 実PRへの付与を確認済み。メール通知の受信までは確認しない |
| `rebase-strategy: disabled` | 最初から停止設定で作った実PRの競合時動作を確認済み。設定変更前からあるPRへの30日間の例外は、時間経過を伴うため未検証 |
| `target-branch` | 実PRの対象ブランチを確認済み。移行先でも実ブランチ・保護条件・ワークフロー条件の設定が必要 |
| private registry | 一時的なHTTPSサーバーと仮トークンで認証・更新を検証。利用者の実registry、Secrets登録、証明書、権限の違いは未検証 |
| セキュリティ更新 | 仮情報でのupdaterテストに加え、専用リポジトリで実アラートとグループ修正PRを確認済み。本体リポジトリのsecurity updatesは無効のまま |
| 承認後の自動マージ | 上記の実PRで確認済み。設定例自体は承認ルールを作らないため、移行先でもブランチ保護が必要 |

移行先でGitHub側の機能を有効化・変更する場合も、実PRの動作を確認してください。スキーマが通ることと、すべての運用条件で動くことは同義ではありません。

## 検証で修正・確認した点

- 検証用に生成したYAMLの`09:00`で引用符が外れ、GitHub側で整数として解釈されました。配布する設定例は`"09:00"`のように引用符を付けています。YAML生成時にも文字列が維持されることを確認してください。
- 実サービスでは5分間隔のcronが拒否され、最小間隔は24時間というエラーを確認しました。公開JSONスキーマに適合しても、この制約は検出されません。検証用設定は日次cronへ修正して、[GitHub側の設定検証成功](https://github.com/mergelog/dpb-test-live-verification-20261114/runs/132403032796)を確認しています。
- 設定不備はActionsの実行一覧に出るとは限りません。設定変更コミットのChecksにある`.github/dependabot.yml`の結果も確認してください。
- `cooldown.default-days: 0` は公開スキーマで拒否されました。待機を外す例は、スキーマに適合する `exclude: ["*"]` に変更しました。CLI実装と設定スキーマの受け付け範囲は一致しない場合があります。
- 認証付きregistryのテストで、公式proxyがHTTP接続へ認証情報を付けず401になることを確認しました。検証サーバーをHTTPSにし、検証用証明書を明示的に信頼させることで、認証・更新が成功しました。[公式proxyの実装](https://github.com/dependabot/proxy/blob/main/internal/handlers/npm_registry.go)
- 完全固定バージョンに `lockfile-only` を使っても、その範囲外への更新PRは出ません。範囲指定のfixtureを別に用意し、lockfileだけが更新される場合も確認しました。
- セキュリティ更新のテストは説明用の仮アドバイザリを入力します。テストに使うバージョンに実在する脆弱性があるという意味ではありません。

## 再実行と証跡

ワークフロー: [.github/workflows/verify-dependabot-examples.yml](../.github/workflows/verify-dependabot-examples.yml)

検証スクリプト: [scripts/verify-dependabot-examples.py](../scripts/verify-dependabot-examples.py)

現在は `docs/dependabot-guide` への対象ファイルのpushで実行します。ワークフローがデフォルトブランチへ反映された後は、Actionsの **Verify Dependabot examples → Run workflow** からも実行できます。

ローカルでの構文・スキーマ検証例:

```sh
python3 -m venv /tmp/dependabot-verification-venv
/tmp/dependabot-verification-venv/bin/pip install PyYAML==6.0.3 jsonschema==4.25.1
/tmp/dependabot-verification-venv/bin/python scripts/verify-dependabot-examples.py --validate
```

updaterテストには稼働中のDockerと公式CLIが必要です。registry系のテストはLinuxのDocker `host-gateway` を前提にしています。

```sh
/tmp/dependabot-verification-venv/bin/python scripts/verify-dependabot-examples.py --case all
```

出力は `out/dependabot-verification/` です。GitHub Actionsのartifactには、入力ジョブ、結果、ログ、検証成功時の `passed.json`、使用イメージ情報を14日間保存します。GitHubの一時APIトークンは保存前に除去します。実行失敗時は `passed.json` がないため、artifactが存在することだけを成功判定にしないでください。
