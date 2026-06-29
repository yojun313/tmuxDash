import subprocess
from dataclasses import dataclass, field, asdict


@dataclass
class TmuxPane:
    index: str
    title: str
    content: str


@dataclass
class TmuxWindow:
    index: str
    name: str
    active: bool
    panes: list[TmuxPane] = field(default_factory=list)


@dataclass
class TmuxSession:
    name: str
    windows: list[TmuxWindow] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except Exception:
        return ""


def get_sessions() -> list[TmuxSession]:
    raw = _run(["tmux", "list-sessions", "-F", "#{session_name}"])
    if not raw:
        return []

    sessions = []
    for session_name in raw.splitlines():
        session = TmuxSession(name=session_name)

        # 윈도우 목록
        win_raw = _run(
            [
                "tmux",
                "list-windows",
                "-t",
                session_name,
                "-F",
                "#{window_index}|#{window_name}|#{window_active}",
            ]
        )
        for win_line in win_raw.splitlines():
            parts = win_line.split("|")
            if len(parts) < 3:
                continue
            win_index, win_name, win_active = parts
            window = TmuxWindow(
                index=win_index,
                name=win_name,
                active=win_active == "1",
            )

            # 팬 목록
            pane_raw = _run(
                [
                    "tmux",
                    "list-panes",
                    "-t",
                    f"{session_name}:{win_index}",
                    "-F",
                    "#{pane_index}|#{pane_title}",
                ]
            )
            for pane_line in pane_raw.splitlines():
                pparts = pane_line.split("|")
                if len(pparts) < 2:
                    continue
                pane_index, pane_title = pparts[0], pparts[1]

                # 팬 내용 캡처 (최근 200줄)
                content = _run(
                    [
                        "tmux",
                        "capture-pane",
                        "-p",
                        "-t",
                        f"{session_name}:{win_index}.{pane_index}",
                        "-S",
                        "-200",
                    ]
                )
                window.panes.append(
                    TmuxPane(
                        index=pane_index,
                        title=pane_title,
                        content=content,
                    )
                )

            session.windows.append(window)
        sessions.append(session)

    return sessions


def get_pane_content(session: str, window: str, pane: str, lines: int = 200) -> str:
    return _run(
        [
            "tmux",
            "capture-pane",
            "-p",
            "-t",
            f"{session}:{window}.{pane}",
            "-S",
            f"-{lines}",
        ]
    )
