# Dependabot 運用ガイド

このリポジトリで依存パッケージの更新PRを確認・承認し、自動マージするための手順です。更新対象、制限事項、停止方法、問題が起きたときの確認先をまとめています。

## 更新からマージまでの流れ

1. Dependabotが新しい依存バージョンを探し、`main` 向けに更新PRを作成する。
2. CODEOWNERSに従ってmergelogへレビューを依頼する。
3. GitHub Actionsが、そのPRの自動マージを有効にする。
4. レビュー権限のある人が差分を確認し、**Approve** する。
5. マージ条件が揃うと、GitHubがSquash mergeで `main` に取り込む。

**現在の必須条件は承認1名です。ビルド・テストの成功は必須にしていないため、承認するとそのままマージされ得ます。** 自動マージは必要なレビューやステータスチェックが完了するまで待機する機能です。[GitHub公式：自動マージ](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/automatically-merging-a-pull-request)

## 現在の設定

| 項目 | 設定・動作 |
| --- | --- |
| 監視対象 | ルートのnpm依存。`dependencies` と `devDependencies` |
| 更新ファイル | `package.json` と `package-lock.json` のうち、変更が必要なファイル |
| 通常更新の確認 | `daily`、`09:00`、`Asia/Tokyo`。平日（月〜金）の日本時間9時が目安 |
| 通常更新のPR上限 | 同時に10件。既存PRのマージ・クローズで空きができるまで追加作成を待つ |
| Angular関連 | `@angular/*` の通常更新を `angular` グループにまとめる |
| その他の依存 | 原則としてパッケージごとに通常更新PRを作成する |
| 除外 | 全パッケージのメジャー更新。通常更新ではAngular 20系を維持する |
| レビュー依頼先 | `/package.json` と `/package-lock.json` の変更をmergelogに依頼する |
| 承認条件 | `main` に1名の承認が必要。管理者にも適用する |
| 追加コミット | 古い承認を無効にする。差分を確認して再承認が必要になる場合がある |
| 必須ステータスチェック | 未設定。自動マージ用ワークフローはビルド・テストを実行しない |
| セキュリティ更新 | GitHub側で無効。通常のバージョン更新とは別に有効化が必要 |

GitHub側の状態は2026年11月14日時点の確認内容です。運用を変えた場合は、実際のリポジトリ設定とこのガイドを揃えてください。

`daily` は土日を含む毎日ではありません。指定時刻ちょうどの実行・PR作成完了は保証されず、新規リリースもクールダウンの対象になる場合があります。現行の公式仕様では通常更新に既定3日のクールダウンがあり、この設定では期間を上書きしていません。[GitHub公式：更新オプション](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)

### 設定ファイルの役割

| ファイル・設定 | 管理する内容 |
| --- | --- |
| [.github/dependabot.yml](.github/dependabot.yml) | 更新対象、頻度、グループ、除外条件、通常更新PRの上限 |
| [.github/CODEOWNERS](.github/CODEOWNERS) | 対象ファイルが変わったときのレビュー依頼先 |
| [.github/workflows/dependabot-auto-merge.yml](.github/workflows/dependabot-auto-merge.yml) | DependabotのPRで自動マージを予約する処理 |
| GitHubのリポジトリ設定 | Allow auto-merge、ブランチ保護、必須承認・チェック、セキュリティ更新 |

## 通常の使い方

### 更新PR・実行履歴を確認する

[PR一覧](https://github.com/mergelog/dpb-test/pulls)から、作成者が `dependabot[bot]` のPRを開きます。PR本文に更新前後のバージョンやリリースノートが記載されます。

更新処理は **Insights → Dependency graph → Dependabot** で確認し、対象のnpm更新ジョブから実行履歴とログを開きます。すぐ確認したい場合は、更新ジョブの画面で **Check for updates** を実行してください。手動実行でも、除外条件・依存の解決・クールダウンなどは適用されるため、必ずPRが作成されるわけではありません。[GitHub公式：更新対象の確認](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/list-configured-dependencies)、[ジョブログと手動確認](https://docs.github.com/en/code-security/how-tos/view-and-interpret-data/view-dependabot-logs)

### 更新内容をレビューする

PRの **Files changed** とリリースノートで次を確認します。

- パッケージ名・更新バージョン・更新理由が妥当か。
- 破壊的変更、廃止機能、セキュリティ修正があるか。
- Angular・TypeScript・Node.jsの対応バージョンやpeer dependenciesに矛盾がないか。
- マニフェストとlockfileが整合し、意図しない依存や取得先が追加されていないか。
- グループPRに含まれるすべての更新を確認したか。

必要に応じて対象PRのブランチを取得し、依存更新を検証します。

```sh
npm ci
npm run build
```

これは手動の確認方法です。現在の自動マージ処理がこれらを実行するわけではありません。マイナー・パッチ更新でも互換性や安全性の確認は必要です。

### 承認して自動マージする

PRの **Files changed → Review changes → Approve → Submit review** から承認します。コメントやリアクションだけでは承認になりません。[GitHub公式：レビューの種類](https://docs.github.com/en/pull-requests/reference/pull-request-reviews)

自動マージが有効なPRでは、承認後に別途Mergeボタンを押す必要はありません。PRが **Merged** になったことを確認してください。競合などの条件が残っていれば承認済みでも待機します。

### 保留・中止する

調査中など、今は取り込みたくない場合はPRの **Disable auto-merge** で予約を解除し、必要に応じて **Request changes** を提出します。取り込まないことが確定したPRはクローズします。

追加コミットなどでワークフローが再実行されると、自動マージは再び有効になります。継続して止めたい場合は「設定変更・停止方法」も確認してください。

## PRコメントによる操作

以下は説明用の例です。対象のDependabot PRへコメントとして投稿すると実行されます。

| コメント | 用途・影響 |
| --- | --- |
| `@dependabot rebase` | ベースブランチに合わせて更新する |
| `@dependabot recreate` | PRを作り直す。PRブランチに加えた編集が上書きされる |
| `@dependabot show rxjs ignore conditions` | `rxjs` の保存済み除外条件を調べる |
| `@dependabot ignore this minor version` | 単独更新PRの対象マイナーバージョンを除外し、PRを閉じる |
| `@dependabot ignore this dependency` | 単独更新PRのパッケージを今後の候補から外し、PRを閉じる |

グループPRでは `@dependabot ignore @angular/core minor version` のようにパッケージを指定します。保存済み除外の解除例は `@dependabot unignore @angular/core` です。解除に伴い現在のPRが閉じられ、新しいPRが作成される場合があります。[GitHub公式：コメントコマンド](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-pull-request-comment-commands)

コメントで指定した除外条件はGitHub側に保存され、`dependabot.yml` へ直接書き込まれません。継続的な運用ルールは設定ファイルにも明示してください。利用可能な操作は、PR本文の **Dependabot commands and options** でも確認できます。[GitHub公式：Dependabot PRの管理](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/manage-dependabot-prs)

## 制限事項と注意事項

### 承認と権限

- 必須承認として数えられるレビューには、原則としてwrite権限以上が必要です。レビューを依頼できる人と、有効な承認者の範囲は同じとは限りません。
- PR作成者は自分のPRを承認できません。mergelog作成の文書・設定変更には別の有効な承認者が必要です。Dependabot作成のPRはmergelogが承認できます。[GitHub公式：レビュー手順](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request)
- `main` のルールはDependabot以外のPRにも適用され、管理者の直接pushも制限されます。
- 現在は **Require review from Code Owners** を必須にしていません。mergelogへ自動で依頼しますが、承認者をmergelogだけに限定する設定ではありません。
- CODEOWNERSはマージ先ブランチ上のものが使われ、指定ユーザーにはwrite権限が必要です。Draftの間は自動レビュー依頼を行いません。[GitHub公式：CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

Dependabot設定の旧 `reviewers` オプションは廃止されています。レビュー依頼先はCODEOWNERSで指定してください。[GitHub公式：reviewersの廃止](https://github.blog/changelog/2025-08-08-dependabot-reviewers-configuration-option-is-replaced-by-code-owners/)

### 自動マージ

- 自動予約の対象は、作成者が `dependabot[bot]`、作成元が同じリポジトリ、マージ先が `main`、DraftではないPRです。人が作成したPRには自動適用しません。
- 起動契機はPRの作成・再オープン・追加コミット・レビュー準備完了です。導入前からあるPRは、初回の手動有効化などが必要です。
- 承認後に差分が変わったら、古い承認が無効になっていないか確認し、最新の内容をレビューしてください。
- 他の更新PRのマージでlockfileが競合すると、再ベース・再確認が必要になる場合があります。
- **承認必須ルールを解除すると、承認前にマージされる可能性があります。** このワークフローはGitHub側の保護条件を前提にしています。
- 権限やベースブランチの変更などで自動マージが解除された場合は、PR画面で再設定を確認します。[GitHub公式：自動マージの条件](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/automatically-merging-a-pull-request)

### 更新対象と互換性

- 通常更新は主にマニフェストへ直接定義した依存が対象です。間接依存がすべて個別の更新PRになるわけではありません。
- メジャー除外はAngular以外にも適用されます。必要なメジャー更新や移行作業は別途計画してください。
- グループ化は更新をまとめる設定であり、互換性やアプリの正常動作を保証しません。
- 現在の監視設定はルートのnpmです。別ディレクトリの独立したプロジェクトや別エコシステムを追加した場合は、監視設定も追加します。
- Dependabotが必要なソースコード変更や移行作業をすべて代行するわけではありません。依存解決に失敗した場合はジョブログを確認します。

### ワークフローと資格情報

自動マージ用ワークフローは `pull_request_target` で動き、`contents: write` と `pull-requests: write` を持ちます。PRのコードをcheckout・実行せず、PR番号を使って自動マージを有効化する構成です。

この処理にPRブランチのcheckoutや任意スクリプト実行を追加すると、書き込み権限を持つトークンにPR側のコードが触れる危険があります。ビルド・テストは別の `pull_request` ワークフローなどで行い、必要なチェックをブランチ保護に設定してください。[GitHub公式：DependabotとActionsの自動化](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/automate-dependabot-with-actions)

## セキュリティ更新との違い

通常のバージョン更新は、新しいリリースを定期的に探す機能です。セキュリティ更新は、既知の脆弱性に対する修正PRを作る別機能です。**現在このリポジトリではDependabot security updatesが無効です。** 通常更新PRが動いていても、セキュリティ修正PRの作成まで有効とは限りません。

利用する場合は **Settings → Advanced Security** にある依存関係関連の設定で、Dependency graph・Dependabot alerts・Dependabot security updatesを確認します。メニュー名はGitHubのUI変更によって異なる場合があります。

- セキュリティ更新は脆弱性の検出と修正可能なバージョンが起点で、通常更新のスケジュールとは別に動きます。
- 通常更新PRとは別に、同時10件の固定上限があります。
- 現在の `angular` グループは通常更新用です。セキュリティ更新のグループ化は別設定です。
- 間接依存の修正に親パッケージの更新が必要な場合があります。解決可能な更新がなければ、アラートがあっても修正PRを作れません。
- 有効化後のセキュリティ更新PRも、現在のワークフロー条件に合えば承認後の自動マージ対象になります。

通常更新のメジャー除外を、あらゆるセキュリティ修正のバージョン上限として扱わないでください。アラート、設定、更新ログから対応可否を確認します。[GitHub公式：セキュリティ更新](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-security-updates)

## 設定変更・停止方法

`dependabot.yml` の変更はPRにし、承認を受けて `main` に取り込みます。作業ブランチで編集しただけでは、通常の運用設定に反映されません。

| 変更したい内容 | 変更箇所 |
| --- | --- |
| 週1回にする | `schedule.interval` を `weekly` にし、必要なら `day` を指定する |
| 時刻・タイムゾーンを変える | `schedule.time` と `schedule.timezone` |
| メジャー更新も候補にする | `ignore` のメジャー除外を削除・限定する。互換性と移行手順を確認する |
| 特定の依存・バージョンを除外する | `ignore` の `dependency-name`、`versions` など |
| 通常更新PRの新規作成を止める | `open-pull-requests-limit: 0` にする |
| レビュー依頼先を変える | CODEOWNERSのユーザー・チームとwrite権限 |

通常更新を停止しても、既存PRの自動マージ予約は解除されません。セキュリティ更新の停止も別操作です。[GitHub公式：更新オプション](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)

自動予約を継続して止める場合は、[Actions一覧](https://github.com/mergelog/dpb-test/actions)で **Dependabot auto-merge** ワークフローを無効化するか、ワークフロー変更をマージします。既存PRは個別に **Disable auto-merge** で解除します。リポジトリ全体で禁止する場合は **Allow auto-merge** も確認してください。承認必須ルールの解除は停止方法ではありません。

## テストを繰り返すとき

コメント付き設定例の検証方法・結果・未検証の範囲は、[設定例の動作検証記録](docs/dependabot-verification.md)を参照してください。17パターンの設定検証・15種類のupdaterテストに加え、実PRでのグループ化・PR上限・停止／再開・再ベース停止・セキュリティ更新・承認後の自動マージも確認しています。

1. 作業ブランチで、互換性のある少し古い依存バージョンを `package.json` に固定する。
2. `npm install` でlockfileも更新し、ビルドなどで依存の組み合わせを確認する。
3. 両ファイルをPRにし、別の有効な承認者のレビューを受けて `main` に取り込む。
4. Dependabotの更新ジョブを実行し、PR作成・レビュー依頼・自動マージ予約を確認する。
5. DependabotのPRをレビュー・承認し、マージ結果を確認する。

マニフェストとlockfileは整合させてください。既存PRや保存済みの除外条件があると、想定と異なる結果になる場合があります。実運用では古い依存を使い続けず、既知の脆弱性やサポート状況も確認してください。

## トラブルシューティング

| 症状 | 確認・対処 |
| --- | --- |
| PRが作成されない | 対象バージョン、メジャー除外、クールダウン、既存PR、上限10件、平日の実行予定、更新ログを確認する |
| 手動実行してもPRが出ない | 対象ディレクトリ、マニフェスト・lockfile、peer dependencies、保存済み除外、依存解決エラーを確認する |
| レビュー依頼が届かない | `main` のCODEOWNERS、対象パス、write権限、Draft状態、導入前からあるPRかを確認する |
| 承認しても進まない | 承認者の権限、追加コミットによる承認無効化、変更要求、競合、他の必須条件を確認する |
| 自動マージが有効にならない | Actionsログ、対象条件、Allow auto-merge、トークン権限、ブランチ保護を確認する |
| 承認後も競合で止まる | `@dependabot rebase` を使い、最新差分と再承認の要否を確認する |
| 再ベースされない | 30日を超えた未マージPRや人の追加コミットで自動再ベースが止まる場合がある。再作成は上書きに注意する |
| 脆弱性があるのに修正PRがない | セキュリティ更新の有効化、アラート、修正版の有無、依存解決の可否を確認する |
| private registryで認証エラー | `registries` とDependabot用Secretsを確認する。Actions用Secretsが自動共有される前提にしない |
| mainへ直接pushできない | 承認必須ルールの想定動作。作業ブランチとPRを使う |
| 長期間更新が動かない | 最終実行・ログ、非アクティブなリポジトリとしての停止、設定状態を確認する |

再ベースの条件は[GitHub公式：PRの管理](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/manage-dependabot-prs)、認証は[GitHub公式：private registry設定](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configure-access-to-private-registries)、非アクティブ時の停止は[GitHub公式：更新の自動停止](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-security-updates#about-automatic-deactivation-of-dependabot-updates)を参照してください。

## 別のリポジトリで使う場合

ファイルをコピーするだけではGitHub側の設定は引き継がれません。

1. `dependabot.yml` の対象ディレクトリ・エコシステムを移行先に合わせる。
2. CODEOWNERSを有効なユーザー・チームに変更する。
3. **Allow auto-merge** とSquash mergeを有効にする。
4. マージ先に承認1名以上を必須とするブランチ保護を設定する。管理者にも適用するなら、その設定も有効にする。
5. 必要なビルド・テストのワークフローと必須チェックを設定する。
6. Actionsの利用と、ワークフローに必要なトークン権限を許可する。
7. 必要ならセキュリティ更新・private registry認証を設定する。
8. 承認前は待機し、承認後にマージされることを検証する。

マージ先を `main` 以外に変える場合は、Dependabotの対象ブランチ、ワークフローの `branches`、マージ先のCODEOWNERS、ブランチ保護を揃えます。forkでは通常更新を明示的に有効化する追加操作が必要です。[GitHub公式：通常更新の有効化とfork](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/configure-version-updates)

privateリポジトリではブランチ保護や自動マージの利用条件がGitHubのプランによって異なります。[GitHub公式：自動マージの利用条件](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/automatically-merging-a-pull-request)
