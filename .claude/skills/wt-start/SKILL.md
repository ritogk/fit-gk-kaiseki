---
name: wt-start
description: 実装タスク開始時に専用の git worktree を作成して作業場所を分離する（並行セッション運用の衝突防止）。引数はタスクの内容（日本語可）。完了時は /wt-done で回収する。
---

# wt-start — タスク専用 worktree の作成

並行して複数セッションが作業しても衝突しないよう、実装タスクごとに専用の worktree + ブランチを作る。

## 手順

1. **main を最新化**: `git -C ~/fit-gk-kaiseki pull --ff-only` を試す。remote 不通や fast-forward 不可なら現状の main のまま進めてよい（報告だけする）。
2. **ブランチ名を決める**: 引数のタスク内容から短い英語ケバブケースのスラッグを作る（例: 「統合ファームの入力層実装」→ `mc-input-layer`）。既存ブランチと重複しないこと（`git branch --list`）。
3. **worktree 作成**:
   ```bash
   git -C ~/fit-gk-kaiseki worktree add -b <slug> ~/fit-gk-kaiseki-wt/<slug> main
   ```
4. **gitignore されている共有物を symlink**（worktree には git 管理外ファイルが来ないため）:
   ```bash
   # Python venv（ルート共有。kline-app / can-live の実行に必要）
   ln -s ~/fit-gk-kaiseki/.venv ~/fit-gk-kaiseki-wt/<slug>/.venv
   # node_modules は存在する場合のみ（無ければ張らない。web/dist はコミット済みなので不要）
   [ -d ~/fit-gk-kaiseki/kline-app/web/node_modules ] && ln -s ~/fit-gk-kaiseki/kline-app/web/node_modules ~/fit-gk-kaiseki-wt/<slug>/kline-app/web/node_modules
   [ -d ~/fit-gk-kaiseki/can-live/web/node_modules ] && ln -s ~/fit-gk-kaiseki/can-live/web/node_modules ~/fit-gk-kaiseki-wt/<slug>/can-live/web/node_modules
   ```
   - micro-control は arduino-cli のツールチェーンが `~/Library/Arduino15` 共有なので symlink 不要
   - 張り先が追跡済みディレクトリとして既に存在する場合は、ディレクトリごとではなく中身を個別に symlink する（`<dir>/<dir>` 入れ子防止）
5. **以後の作業はすべて `~/fit-gk-kaiseki-wt/<slug>/` 配下で行う**。ファイルの読み書き・コマンド実行のパスを worktree 側に切り替えること。`~/fit-gk-kaiseki`（main）のファイルは以後触らない。

## ルール

- 動作確認も worktree 内で完結させる（venv は symlink で使える。micro-control は `./build.sh compile <sketch>`）。
- 同じファイルを触るタスクを別 worktree に分けない（マージで必ず衝突する）。その場合は1つのタスクにまとめる。
- 完了したら `/wt-done` でマージ・後片付けまで行う。
