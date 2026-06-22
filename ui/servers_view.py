"""
The "My Servers" view: a list of installed servers and their detail pages.

This widget is an internal stack — page 0 lists the servers, page 1 shows the
selected server's detail/management surface. Selecting a server opens its
detail; the back button returns to the list.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.server_registry import ServerRecord, ServerRegistry
from core.server_runtime import RuntimeManager
from translations import Translator
from ui.common import title_label
from ui.server_detail import ServerDetail


class ServersView(QStackedWidget):
    """Lists installed servers and routes to their detail pages."""

    became_empty = pyqtSignal()        # no servers remain
    create_requested = pyqtSignal()    # user clicked "create" from the empty state

    def __init__(self, registry: ServerRegistry, runtimes: RuntimeManager,
                 translator: Translator, parent=None) -> None:
        super().__init__(parent)
        self.registry = registry
        self.runtimes = runtimes
        self.tr_ = translator
        self._detail: ServerDetail | None = None
        self._list_page = self._build_list_page()
        self.addWidget(self._list_page)
        self.refresh()

    def t(self, key: str, **kwargs) -> str:
        return self.tr_.t(key, **kwargs)

    # ------------------------------------------------------------------ list
    def _build_list_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(title_label(self.t("servers_title")))
        header.addStretch(1)
        create = QPushButton("＋ " + self.t("nav_create"))
        create.setObjectName("Primary")
        create.clicked.connect(self.create_requested.emit)
        header.addWidget(create)
        layout.addLayout(header)

        self._empty_label = QLabel(self.t("servers_empty"))
        self._empty_label.setObjectName("Secondary")
        layout.addWidget(self._empty_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(12)
        self._cards_layout.addStretch(1)
        scroll.setWidget(self._cards_container)
        layout.addWidget(scroll, 1)
        return page

    def refresh(self) -> None:
        """Reload the server cards from the registry."""
        # Remove existing cards (keep the trailing stretch).
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        records = self.registry.all()
        self._empty_label.setVisible(not records)
        for record in records:
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, self._make_card(record))

    def _make_card(self, record: ServerRecord) -> QFrame:
        card = QFrame()
        card.setObjectName("ServerCard")
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 14, 16, 14)

        text_col = QVBoxLayout()
        name = QLabel(record.name)
        name.setStyleSheet("font-size: 17px; font-weight: 600;")
        meta = QLabel(f"{record.platform.title()}  •  {record.mc_version}  •  Port {record.port}")
        meta.setObjectName("Secondary")
        text_col.addWidget(name)
        text_col.addWidget(meta)
        row.addLayout(text_col)
        row.addStretch(1)

        running = self.runtimes.get(record).is_running()
        badge = QLabel(self.t("server_status_running") if running else self.t("server_status_stopped"))
        badge.setObjectName("BadgeRunning" if running else "BadgeStopped")
        row.addWidget(badge)

        manage = QPushButton(self.t("btn_manage"))
        manage.setObjectName("Primary")
        manage.clicked.connect(lambda _c=False, r=record: self.open_detail(r))
        row.addWidget(manage)
        return card

    # ---------------------------------------------------------------- detail
    def open_detail(self, record: ServerRecord, auto_start: bool = False) -> None:
        """
        Open the management surface for ``record``.

        When ``auto_start`` is set (used right after installation) the server is
        started automatically; the user can then stop it or keep it running.
        """
        if self._detail is not None:
            self._detail.stop_timers()
            self.removeWidget(self._detail)
            self._detail.deleteLater()
            self._detail = None

        runtime = self.runtimes.get(record)
        self._detail = ServerDetail(record, runtime, self.registry, self.tr_)
        self._detail.back_requested.connect(self._close_detail)
        self._detail.deleted.connect(self._on_deleted)
        self.addWidget(self._detail)
        self.setCurrentWidget(self._detail)
        if auto_start:
            self._detail.start_server()

    def _close_detail(self) -> None:
        self.refresh()
        self.setCurrentWidget(self._list_page)

    def _on_deleted(self, path: str) -> None:
        self.runtimes.discard(path)
        self._close_detail()
        if self.registry.count() == 0:
            self.became_empty.emit()
