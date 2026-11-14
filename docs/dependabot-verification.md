# Dependabot設定例の動作検証

確認日: 2026年11月14日。**17パターンの設定検証と15種類の公式updaterテストがすべて成功しました。** [最終実行ログ](https://github.com/mergelog/dpb-test/actions/runs/43577956660)、[ケース別の実測結果JSON](dependabot-verification-results.json)から確認できます。検証したコードはコミット `cc4514f` です。

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

## 実サービスでの確認と区別する項目

| 項目 | 今回の確認範囲・残る前提 |
| --- | --- |
| 曜日・時刻・タイムゾーン | スキーマと公式仕様を照合。実際の曜日・時刻を待つ運用試験は行わない |
| PR上限・停止・再開 | スキーマ検証。GitHubのスケジューラによるPR作成制御はdry-run対象外 |
| ラベル・担当者 | スキーマ検証。実PRへの付与・通知はGitHubサービス側の確認が別途必要 |
| `rebase-strategy: disabled` | コメントを有効化した設定のスキーマ検証。既存PRの時間経過を伴う試験は行わない |
| `target-branch` | コメントを有効化した設定のスキーマ検証。実ブランチ・保護条件・ワークフロー条件は移行先で確認する |
| private registry | 一時的なHTTPSサーバーと仮トークンで認証・更新を検証。利用者の実registry、Secrets登録、証明書、権限の違いは未検証 |
| セキュリティ更新 | 仮の脆弱性情報でupdaterのグループ処理を検証。GitHubの実アラート生成・検出は未検証で、実リポジトリのsecurity updatesは有効化しない |
| 承認後の自動マージ | このテストでは人の承認や実マージを代行しない。設定例自体は承認ルールを作らない |

GitHub側の機能を有効化・変更する場合は、テスト用リポジトリなどで実PRの動作も確認してください。スキーマが通ることと、すべての運用条件で動くことは同義ではありません。

## 検証で修正・確認した点

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
