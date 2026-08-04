#!/usr/bin/env python3
"""
git_auto_push.py — 自动化 Git 提交与推送工具
跨平台支持：macOS / Windows / Linux（只要装了 Python 3 和 Git 即可）

默认流程（对应你贴的 daily workflow）：
    1. git pull origin <branch>
    2. git status
    3. git add .
    4. git commit -m "<你输入的 message>"
    5. git push origin <branch>

用法：
    交互模式（会弹出输入框让你填 commit message）：
        python3 git_auto_push.py

    非交互模式（直接指定 message，适合写进脚本/定时任务）：
        python3 git_auto_push.py -m "Add user registration feature"

    其他可选参数：
        --no-pull        跳过 pull 步骤
        --branch <name>  指定分支（默认自动取当前分支）
        --remote <name>  指定远程名（默认 origin）
        --yes            跳过 push 前的二次确认
"""

import argparse
import subprocess
import sys


# Windows 下的 cmd/PowerShell 有时是 GBK 编码，强制切到 UTF-8，
# 避免打印中文时报 UnicodeEncodeError。
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python < 3.7 没有 reconfigure，忽略即可
        pass


def run(cmd, exit_on_error=True):
    """执行一条 git 命令，把输出实时打印出来"""
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode != 0 and exit_on_error:
        print(f"\n[错误] 命令执行失败: {' '.join(cmd)}")
        sys.exit(result.returncode)
    return result


def check_git_repo():
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                             capture_output=True, text=True)
    if result.returncode != 0:
        print("[错误] 当前目录不是一个 git 仓库。")
        sys.exit(1)


def get_current_branch():
    result = subprocess.run(["git", "branch", "--show-current"],
                             capture_output=True, text=True)
    return result.stdout.strip()


def has_changes():
    result = subprocess.run(["git", "status", "--porcelain"],
                             capture_output=True, text=True)
    return bool(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description="自动化 Git 提交与推送工具")
    parser.add_argument("-m", "--message", help="commit message，不填则会交互式输入")
    parser.add_argument("--branch", help="要操作的分支，默认自动检测当前分支")
    parser.add_argument("--remote", default="origin", help="远程名，默认 origin")
    parser.add_argument("--no-pull", action="store_true", help="跳过 git pull 步骤")
    parser.add_argument("--yes", action="store_true", help="跳过 push 前的二次确认")
    args = parser.parse_args()

    check_git_repo()

    branch = args.branch or get_current_branch()
    if not branch:
        print("[错误] 无法获取当前分支名，可能处于 detached HEAD 状态，请用 --branch 指定。")
        sys.exit(1)

    print(f"[信息] 当前分支: {branch}    远程: {args.remote}")

    # 1. Pull
    if not args.no_pull:
        print("\n=== 第一步: 拉取远程最新代码 (git pull) ===")
        run(["git", "pull", args.remote, branch], exit_on_error=False)
    else:
        print("\n=== 跳过 pull 步骤 (--no-pull) ===")

    # 2. Status
    print("\n=== 第二步: 检查改动 (git status) ===")
    run(["git", "status"], exit_on_error=False)

    if not has_changes():
        print("\n[完成] 没有需要提交的改动，工作区是干净的。")
        sys.exit(0)

    # 3. Add
    print("\n=== 第三步: 暂存改动 (git add .) ===")
    run(["git", "add", "."])

    # 4. Commit message —— 这里就是你要的“输入框”
    print("\n=== 第四步: 输入 commit message ===")
    message = args.message
    if not message:
        while True:
            message = input("请输入本次提交的 commit message: ").strip()
            if message:
                break
            print("[提示] commit message 不能为空，请重新输入。")

    run(["git", "commit", "-m", message])

    # 5. Push（带二次确认，防止误推）
    if not args.yes:
        confirm = input(f"\n是否推送到 {args.remote}/{branch}? (y/n): ").strip().lower()
        if confirm != "y":
            print("[已取消] 推送已取消，改动仍保留在本地 commit 中，可以随时手动 git push。")
            sys.exit(0)

    print(f"\n=== 第五步: 推送到远程 (git push {args.remote} {branch}) ===")
    run(["git", "push", args.remote, branch])

    print("\n[完成] 代码已成功推送到 GitHub。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[已中断] 用户手动中断操作。")
        sys.exit(1)