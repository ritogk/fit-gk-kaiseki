---
name: wt-done
description: /wt-start で作った worktree のタスク完了時に実行。動作確認 → commit → main へマージ（コンフリクトはここで解消）→ worktree/ブランチ削除まで一連で行う。実機必須の確認が残る場合はマージ前に停止してユーザーに委ねる。
---

# wt-done — worktree の回収（動作確認 → マージ → 削除）

worktree 内での実装が済んだら、以下を一連で実行する。worktree 内から実行する前提。

## 手順

1. **動作確認**: Mac 上で可能な範囲を worktree 内で行う。
   - Python 系: `../fit-gk-kaiseki-wt/<slug>/.venv` 経由の import / スクリプト実行（実車が要る操作は不可）
   - micro-control: `./build.sh compile <sketch>` が通ること（実書き込みはボード接続時のみ）
   - **実車・実機接続が必須の確認しか残っていない場合はここで停止**し、「マージしてよいか」をユーザーに確認する。
2. **worktree 内でコミット**:
   - `git status` / `git diff` で今回の変更ファイルを特定し、**必ずパス指定で** `git add`（`-A` / `.` 禁止）。
   - `git diff --cached --stat` で自分の変更だけであることを確認してからコミット。
   - コミットメッセージは既存 `git log` のスタイル（`feat(scope):`/`fix(scope):`/`docs(scope):` + 日本語要点）。
3. **main へマージ**:
   ```bash
   git -C ~/fit-gk-kaiseki merge <slug>
   ```
   - **コンフリクトしたら `~/fit-gk-kaiseki` 側で解消してマージコミットする**。解消時、自分のタスクと無関係なファイルは触らない。
   - git が「ローカル変更があるためマージできない」と拒否した場合、それは**他セッションの未コミット変更**。stash / reset / checkout で消さないこと。ユーザーに報告して停止する。
4. **worktree / ブランチ削除**:
   ```bash
   cd ~/fit-gk-kaiseki
   git branch --merged main | grep -q '<slug>' || { echo "未マージ"; exit 1; }
   # /wt-start で張った symlink を外す（共有実体は消えない）。追加で張ったものがあればそれも
   rm -f ~/fit-gk-kaiseki-wt/<slug>/.venv \
         ~/fit-gk-kaiseki-wt/<slug>/kline-app/web/node_modules \
         ~/fit-gk-kaiseki-wt/<slug>/can-live/web/node_modules
   git worktree remove ~/fit-gk-kaiseki-wt/<slug>
   git branch -d <slug>
   ```
   - `worktree remove` が未追跡ファイルで拒否された場合、残っているのがキャッシュ等の生成物だけなら `--force` でよい。成果物っぽいファイルが残っていたら消さずにユーザーに報告。

## 対象外

- push はしない（ユーザーの明示指示時のみ `git -C ~/fit-gk-kaiseki push`）。
- 動作確認 NG の場合はマージせず、同じ worktree で修正して再度この手順を実行する。
