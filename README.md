# dpb-test

Angular 20で `hello depender bot` を表示する、Dependabot更新テスト用プロジェクトです。

## 起動

Node.js 20.19以降の20系、22.12以降の22系、または24系を使用してください。

```sh
npm ci
npm start
```

ブラウザーで http://localhost:4200 を開きます。

```sh
npm run build
```

本番ビルドは `dist/dpb-test/browser` に出力されます。

## Dependabotのテスト

`package.json` と `package-lock.json` は、更新候補が出るよう意図的に少し古いバージョンで固定しています。

| パッケージ | 固定バージョン |
| --- | --- |
| Angular本体 / compiler-cli | 20.3.34 |
| Angular CLI / build | 20.3.42 |
| RxJS | 7.8.1 |
| tslib | 2.8.1 |
| TypeScript | 5.9.2 |

`.github/dependabot.yml` で、ルートのnpm依存を毎日09:00（日本時間）に確認する設定です。Angular関連はまとめて更新し、Angular 20でのテストを続けられるようメジャー更新は全依存で除外しています。

push後はGitHubの **Insights → Dependency graph → Dependabot** から実行状況を確認できます。必要なら **Check for updates** で手動実行してください。

## 承認後の自動マージ

DependabotのPRは `.github/CODEOWNERS` に従ってmergelogにレビューを依頼し、`.github/workflows/dependabot-auto-merge.yml` で自動マージを予約します。GitHub側で `Allow auto-merge` を有効にし、`main` のブランチ保護で1名の承認を必須にしています（管理者にも適用）。承認が揃うとGitHubがマージし、更新コミットが追加された場合は再承認が必要です。

このワークフローはレビューを自動承認しません。レビュー権限のあるユーザーがPRの **Files changed → Review changes → Approve** から承認してください。

`Allow auto-merge` とブランチ保護はGitHubのリポジトリ設定なので、このリポジトリを別の場所へ複製した場合は設定し直してください。
