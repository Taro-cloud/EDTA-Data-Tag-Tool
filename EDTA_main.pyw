# -*- coding: utf-8 -*-

##########
# (c) 2025 T. Hayakawa
##########

import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTreeView, QListView, QSplitter, 
                               QFileSystemModel, QLabel, QToolBar, 
                               QStatusBar, QMenu, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, QDir, QModelIndex
from PySide6.QtGui import QIcon, QFont, QPixmap, QAction
from parameter_table import ParameterTable


class TagEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EDTA- Expeliment Data Tagging and Analysis")
        self.setGeometry(100, 100, 1200, 800)
        
        # ファイルシステムモデルの初期化
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.rootPath())
        
        # フォルダ履歴の管理
        self.history = []  # 履歴リスト
        self.history_index = -1  # 現在の履歴位置
        
        # UIの初期化
        self.init_ui()
        self.setup_connections()
        
        # 初期ディレクトリを設定
        self.set_initial_directory()
        
        # 戻る/進むボタンの初期状態を更新
        self.update_navigation_buttons()
            
    def init_ui(self):
        # メインウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        
        # ツールバーの作成
        self.toolbar = QToolBar()
        self.setup_toolbar()
        
        # スプリッターの作成
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # 左側のツリービュー（フォルダツリー）
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(QDir.rootPath()))
        self.tree_view.setAnimated(False)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        self.tree_view.setColumnWidth(0, 250)
        self.splitter.addWidget(self.tree_view)
        
        # 右側のツリービュー（ファイル一覧 - 詳細表示）
        self.rightPage=QWidget()
        self.RVlayout=QVBoxLayout(self.rightPage)
        self.RVlayout.addWidget(self.toolbar)

        self.list_view = QTreeView()
        self.list_view.setModel(self.file_model)
        self.list_view.setRootIsDecorated(False)  # フォルダの展開アイコンを非表示
        self.list_view.setSortingEnabled(True)
        self.list_view.sortByColumn(0, Qt.AscendingOrder)
        
        # 列の幅を設定
        self.list_view.setColumnWidth(0, 200)  # 名前
        self.list_view.setColumnWidth(1, 100)  # サイズ
        self.list_view.setColumnWidth(2, 100)  # 種類
        self.list_view.setColumnWidth(3, 150)  # 更新日時

        self.RVlayout.addWidget(self.list_view)
        
        self.splitter2 = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.splitter2)#self.list_view)
        
        # パラメータテーブルの初期化
        self.parameter_table =  ParameterTable(self)#(self.file_model, self)

        self.splitter2.addWidget(self.rightPage)
        self.splitter2.addWidget(self.parameter_table)
        # スプリッターの比率を設定
        self.splitter.setSizes([400, 800])
        
        # ステータスバーの作成
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # ファイル情報ラベル
        self.file_info_label = QLabel()
        self.status_bar.addPermanentWidget(self.file_info_label)
    
    def setup_toolbar(self):
        
        # 戻るボタン
        back_action = QAction("←", self)
        back_action.setToolTip("戻る")
        back_action.triggered.connect(self.go_back)
        self.toolbar.addAction(back_action)
        
        # 進むボタン
        forward_action = QAction("→", self)
        forward_action.setToolTip("進む")
        forward_action.triggered.connect(self.go_forward)
        self.toolbar.addAction(forward_action)
        
        # 上へボタン
        up_action = QAction("↑", self)
        up_action.setToolTip("上へ")
        up_action.triggered.connect(self.go_up)
        self.toolbar.addAction(up_action)
        
        self.toolbar.addSeparator()
                
        # 新規フォルダ作成
        new_folder_action = QAction("新規フォルダ", self)
        new_folder_action.setToolTip("新規フォルダを作成")
        new_folder_action.triggered.connect(self.create_new_folder)
        self.toolbar.addAction(new_folder_action)
        
        self.toolbar.addSeparator()
           
    def setup_connections(self):
        # ツリービューの選択変更
        self.tree_view.selectionModel().currentChanged.connect(self.on_tree_selection_changed)
        
        # リストビューのダブルクリック
        self.list_view.doubleClicked.connect(self.on_list_double_clicked)
        
        # コンテキストメニュー
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)
    
    def set_initial_directory(self):
        # 現在のディレクトリを初期ディレクトリとして設定
        current_path = QDir.currentPath()
        self.navigate_to_path(current_path)
    
    def navigate_to_path(self, path, add_to_history=True):
        """指定されたパスに移動"""
        # パスを正規化（絶対パスに変換）
        try:
            normalized_path = os.path.abspath(path)
        except:
            normalized_path = path
        
        index = self.file_model.index(normalized_path)
        if index.isValid():
            # 履歴に追加（同じパスへの移動は追加しない）
            if add_to_history:
                # 現在位置より後の履歴を削除（新しいパスに移動した場合）
                if self.history_index < len(self.history) - 1:
                    self.history = self.history[:self.history_index + 1]
                
                # 同じパスでない場合のみ履歴に追加
                if not self.history or self.history[-1] != normalized_path:
                    self.history.append(normalized_path)
                    self.history_index = len(self.history) - 1
            
            self.list_view.setRootIndex(index)
            self.tree_view.setCurrentIndex(index)
            self.update_file_info()
            
            # パラメータテーブルが開いている場合は更新
            if self.parameter_table and self.parameter_table.isVisible():
                self.parameter_table.update_path(normalized_path)
            
            # 戻る/進むボタンの有効/無効を更新
            self.update_navigation_buttons()
    
    def on_tree_selection_changed(self, current, previous):
        """ツリービューの選択が変更されたとき"""
        if current.isValid():
            path = self.file_model.filePath(current)
            if os.path.isdir(path):
                # 履歴に追加して移動
                self.navigate_to_path(path)
    
    def on_list_double_clicked(self, index):
        """リストビューでダブルクリックされたとき"""
        path = self.file_model.filePath(index)
        if os.path.isdir(path):
            self.navigate_to_path(path)
        else:
            # ファイルの場合はデフォルトアプリで開く
            self.open_file(path)
    
    def go_back(self):
        """戻る"""
        if self.history_index > 0:
            self.history_index -= 1
            previous_path = self.history[self.history_index]
            # 履歴に追加せずに移動（履歴の移動なので）
            self.navigate_to_path(previous_path, add_to_history=False)
    
    def go_forward(self):
        """進む"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            next_path = self.history[self.history_index]
            # 履歴に追加せずに移動（履歴の移動なので）
            self.navigate_to_path(next_path, add_to_history=False)
    
    def update_navigation_buttons(self):
        """戻る/進むボタンの有効/無効を更新"""
        # ツールバーからアクションを取得
        actions = self.toolbar.actions()
        back_action = None
        forward_action = None
        
        for action in actions:
            if action.toolTip() == "戻る":
                back_action = action
            elif action.toolTip() == "進む":
                forward_action = action
        
        # 戻るボタンの有効/無効
        if back_action:
            back_action.setEnabled(self.history_index > 0)
        
        # 進むボタンの有効/無効
        if forward_action:
            forward_action.setEnabled(self.history_index < len(self.history) - 1)
    
    def go_up(self):
        """上へ"""
        current_index = self.list_view.rootIndex()
        if current_index.isValid():
            parent_index = current_index.parent()
            if parent_index.isValid():
                path = self.file_model.filePath(parent_index)
                self.navigate_to_path(path)
    
    #つかわない
    def __change_view_mode(self, mode):
        """表示モードを変更"""
        current_index = self.list_view.rootIndex()
        #splitter = self.centralWidget().layout().itemAt(0).widget()
        
        if mode == "list":
            # 詳細表示（QTreeViewを使用）
            detail_tree_view = QTreeView()
            detail_tree_view.setModel(self.file_model)
            detail_tree_view.setRootIsDecorated(False)
            detail_tree_view.setSortingEnabled(True)
            detail_tree_view.sortByColumn(0, Qt.AscendingOrder)
            detail_tree_view.setColumnWidth(0, 200)
            detail_tree_view.setColumnWidth(1, 100)
            detail_tree_view.setRootIndex(current_index)
            
            # ダブルクリックとコンテキストメニューの接続を設定
            detail_tree_view.doubleClicked.connect(self.on_list_double_clicked)
            detail_tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
            detail_tree_view.customContextMenuRequested.connect(self.show_context_menu)
            
            # スプリッターの右側のウィジェットを置き換え
            self.splitter2.replaceWidget(0, detail_tree_view) #moto1
            self.list_view = detail_tree_view
            
        elif mode == "icon":
            # アイコン表示に切り替え（QListViewを使用）
            icon_list_view = QListView()
            icon_list_view.setModel(self.file_model)
            icon_list_view.setViewMode(QListView.IconMode)
            icon_list_view.setIconSize(QPixmap(48, 48).size())
            icon_list_view.setSpacing(10)
            icon_list_view.setResizeMode(QListView.Adjust)
            icon_list_view.setMovement(QListView.Static)
            icon_list_view.setRootIndex(current_index)
            
            # ダブルクリックとコンテキストメニューの接続を設定
            icon_list_view.doubleClicked.connect(self.on_list_double_clicked)
            icon_list_view.setContextMenuPolicy(Qt.CustomContextMenu)
            icon_list_view.customContextMenuRequested.connect(self.show_context_menu)
            
            # スプリッターの右側のウィジェットを置き換え
            self.splitter2.replaceWidget(0, icon_list_view) #moto1
            self.list_view = icon_list_view
    
    def create_new_folder(self):
        """新規フォルダを作成"""
        current_path = self.file_model.filePath(self.list_view.rootIndex())
        folder_name, ok = QInputDialog.getText(self, "新規フォルダ", "フォルダ名を入力してください:")
        
        if ok and folder_name:
            new_folder_path = os.path.join(current_path, folder_name)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                # モデルを更新
                self.file_model.setRootPath(self.file_model.rootPath())
            except Exception as e:
                QMessageBox.warning(self, "エラー", f"フォルダの作成に失敗しました: {str(e)}")
    
    def open_file(self, file_path):
        """ファイルを開く"""
        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"ファイルを開けませんでした: {str(e)}")
    
    def show_context_menu(self, position):
        """コンテキストメニューを表示"""
        index = self.list_view.indexAt(position)
        if index.isValid():
            menu = QMenu()
            
            # ファイル情報を取得
            file_path = self.file_model.filePath(index)
            file_info = self.file_model.fileInfo(index)
            
            if file_info.isDir():
                # フォルダの場合
                open_action = menu.addAction("開く")
                open_action.triggered.connect(lambda: self.navigate_to_path(file_path))
            else:
                # ファイルの場合
                open_action = menu.addAction("開く")
                open_action.triggered.connect(lambda: self.open_file(file_path))
            
            menu.addSeparator()
            
            # 削除アクション
            delete_action = menu.addAction("削除")
            delete_action.triggered.connect(lambda: self.delete_item(file_path))
            
            menu.exec_(self.list_view.mapToGlobal(position))
    
    def delete_item(self, path):
        """アイテムを削除"""
        reply = QMessageBox.question(self, "確認", 
                                   f"本当に削除しますか？\n{path}",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    os.rmdir(path)
                else:
                    os.remove(path)
                # モデルを更新
                self.file_model.setRootPath(self.file_model.rootPath())
            except Exception as e:
                QMessageBox.warning(self, "エラー", f"削除に失敗しました: {str(e)}")
    
    def update_file_info(self):
        """ファイル情報を更新"""
        current_index = self.list_view.rootIndex()
        if current_index.isValid():
            path = self.file_model.filePath(current_index)
            try:
                # ファイル数をカウント
                file_count = 0
                dir_count = 0
                total_size = 0
                
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        file_count += 1
                        total_size += os.path.getsize(item_path)
                    elif os.path.isdir(item_path):
                        dir_count += 1
                
                # サイズを読みやすい形式に変換
                size_str = self.format_size(total_size)
                self.file_info_label.setText(f"dirs: {dir_count}, files: {file_count}, size: {size_str}")
            except Exception:
                self.file_info_label.setText("")
    
    def format_size(self, size_bytes):
        """バイトサイズを読みやすい形式に変換"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def __show_parameter_table(self):
        """パラメータテーブルを表示・更新"""
        if not self.parameter_table:
            self.parameter_table = ParameterTable()#self.file_model, self)
            # ウィンドウを表示
            self.parameter_table.show()
        
        # 現在のパスを設定してデータを読み込み
        current_path = self.file_model.filePath(self.list_view.rootIndex())
        self.parameter_table.update_path(current_path)


def main():
    app = QApplication(sys.argv)
    
    # アプリケーションのスタイルを設定
    app.setStyle('Fusion')
    
    # フォントを設定
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # メインウィンドウを作成して表示
    mainwindow = TagEditor()
    mainwindow.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
