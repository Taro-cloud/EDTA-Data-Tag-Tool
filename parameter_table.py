from logging import root
import sys
import os #,pathlib
import json
from concurrent import futures #threading
import subprocess
from datetime import datetime
from tkinter import NO
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLabel, QFileDialog,
                               QMessageBox, QHeaderView, QMenu, QInputDialog,
                               QStyledItemDelegate, QComboBox)
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QAction, QFont


class ComboBoxDelegate(QStyledItemDelegate):
    """列1にComboBoxを表示するデリゲート"""
    def __init__(self, parent=None, master_data=None):
        super().__init__(parent)
        self.master_data = master_data
        self.table_widget = None  # テーブルへの参照
    
    def set_table_widget(self, table_widget):
        """テーブルウィジェットへの参照を設定"""
        self.table_widget = table_widget
    
    ## override
    def createEditor(self, parent, option, index):
        """エディタ（ComboBox）を作成"""
        combo = QComboBox(parent)
        combo.setEditable(True)  # 編集可能にする
        combo.lineEdit().setPlaceholderText("値を入力または選択")
        
        # 列2（value list）のデータを取得して候補として追加
        if self.table_widget:
            row = index.row()
            value_list_item = self.table_widget.item(row, 2)  # 列2
            if value_list_item:
                value_list_text = value_list_item.text()
                if value_list_text:
                    # カンマや改行で区切られた値を候補として追加
                    candidates = [v.strip() for v in value_list_text.replace('\n', ',').split(',') if v.strip()]
                    for candidate in candidates:
                        combo.addItem(candidate)
        
        return combo
    ## override
    def setEditorData(self, editor, index):
        """エディタにデータを設定"""
        value = index.data(Qt.DisplayRole)
        if value:
            editor.setCurrentText(str(value))
    ## override  
    def setModelData(self, editor, model, index):
        """モデルにデータを設定"""
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)


class ParameterTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.file_model = file_model
        self.current_path = ""
        self.root_path=""
        self.json_filename=""
        self.jdata=dict() #今のフォルダのjson
        self.sub_py_filename=""
        self.result_filename=""
        self.skip_row=0
        
        #self.enum_suffix="_enum" 
        #enumは、**.jsonのvalueを0:マスターなし、1...の値に変えたもの
        # **enum.jsonの中身は、

        self.json_master_filename=""
        self.master_jdata=dict()

        #self.file_list = []
        self.path_list=[]
        self.indexDict=dict()
       
        self.setWindowTitle("Tagデータ")
        self.setGeometry(200, 200, 800, 600)
        
        self.init_ui()
        self.setup_connections()
        
        # 初期状態では「リスト表示」ボタンを押してデータを読み込むことを案内
        self.status_label.setText("xml filename is not set.") #("ツールバーの「リスト表示」ボタンを押してデータを読み込んでください")
        self.root_label.setText("未設定")

    def init_ui(self):
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        
        # ヘッダー部分
        headerV_layout = QVBoxLayout()
        header_layout1 = QHBoxLayout()
        header_layout2 = QHBoxLayout()
        
        # パス表示ラベル
        self.path_label = QLabel("パス: 未選択")
        self.path_label.setFont(QFont("Segoe UI", 9))
        header_layout1.addWidget(self.path_label)
        
        self.root_label = QLabel("rootパス: 未選択")
        self.root_label.setFont(QFont("Segoe UI", 9))
        header_layout2.addWidget(self.root_label)

        header_layout1.addStretch()
        header_layout2.addStretch()
        
        # ボタン群
        self.set_root_btn = QPushButton("set root")
        self.set_root_btn.setToolTip("set root path of tag")
        header_layout1.addWidget(self.set_root_btn)

        self.new_json_btn = QPushButton("new json")
        self.new_json_btn.setToolTip("set root path of tag")
        header_layout1.addWidget(self.new_json_btn)

        self.load_btn = QPushButton("load root JSON")
        self.load_btn.setToolTip("JSONファイルからリストを読み込み")
        header_layout1.addWidget(self.load_btn)

        self.save_btn = QPushButton("save JSON")
        self.save_btn.setToolTip("リストをJSONファイルに保存")
        header_layout1.addWidget(self.save_btn)

        ##
        self.set_sub_py_btn = QPushButton("set sub *.py") #第一引数は、jsonのフォルダ。結果はstdoutから取得しまとめファイルに保存
        self.set_sub_py_btn.setToolTip("各フォルダで実行する*.pyを設定")
        header_layout2.addWidget(self.set_sub_py_btn)
     
        self.set_result_filename_btn = QPushButton("set result filename")
        self.set_result_filename_btn.setToolTip("各フォルダの実行結果ファイル名")
        header_layout2.addWidget(self.set_result_filename_btn)

        self.do_sup_py_btn = QPushButton("run sub *.py")
        self.do_sup_py_btn.setToolTip("各フォルダに+.py実行")
        header_layout2.addWidget(self.do_sup_py_btn)

        headerV_layout.addLayout(header_layout1)
        headerV_layout.addLayout(header_layout2)
        main_layout.addLayout(headerV_layout)
        
        # テーブルウィジェット
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["key","value","value list"])
        
        # 列1（value列）にComboBoxデリゲートを設定
        combo_delegate = ComboBoxDelegate(self, self.master_jdata)
        combo_delegate.set_table_widget(self.table)
        self.table.setItemDelegateForColumn(1, combo_delegate)
        
        # テーブルの設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) #Stretch)  # 名前列は伸縮
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch) 
        #header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        #header.setSectionResizeMode(4, QHeaderView.Stretch)  # パス列は伸縮
        
        self.table.setAlternatingRowColors(True)
        #self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        
        main_layout.addWidget(self.table)
        
        # ステータスラベル
        self.status_label = QLabel("xml name is not set.")
        self.status_label.setFont(QFont("Segoe UI", 8))
        main_layout.addWidget(self.status_label)
    
    def setup_connections(self):
        self.set_root_btn.clicked.connect(self.set_root_path)
        self.new_json_btn.clicked.connect(self.new_json)
        self.load_btn.clicked.connect(self.load_from_json)
        self.save_btn.clicked.connect(self.save_to_json)

        #
        self.set_sub_py_btn.clicked.connect(self.set_sub_pyfile)
        self.set_result_filename_btn.clicked.connect(self.set_result_filename)
        self.do_sup_py_btn.clicked.connect(self.do_sup_py)

        # コンテキストメニュー
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # セル編集終了時に新しい行を追加
        #self.table.cellChanged.connect(self.on_cell_changed)
        self.table.itemChanged.connect(self.on_cell_changed) #cellchangedは、loadしただけでも発生するのでつかわない。

    #########################################################
    # callback functions
    #########################################################

    def on_cell_changed(self, citem): #row, column):
        """セルの編集終了時に呼ばれる。最後の行を編集した場合は新しい行を追加"""
        row=citem.row()
        #マスターデータ更新
        #if column==2:
        print("master-update")
        print(row)
        if self.table.item(row,0)!=None:
            print( self.table.item(row,0).text() )
        if self.table.item(row,2)!=None:
            print( self.table.item(row,2).text() )

        # 現在の行数
        current_row_count = self.table.rowCount()
        
        # 編集された行が最後の行の場合、新しい行を追加
        if row == current_row_count - 1:
            # シグナルを一時的に切断（再帰的な変更を防ぐ）
            #self.table.cellChanged.disconnect(self.on_cell_changed)
            self.table.itemChanged.disconnect(self.on_cell_changed)
            try:
                # 新しい行を追加
                itemExist=False
                for col in range(self.table.columnCount()):
                    if self.table.item(row,col) !=None:
                        itemExist=True 
                if itemExist==True:

                    new_row = self.table.rowCount()
                    self.table.insertRow(new_row)
                    
                    # 新しい行のすべての列に空のセルを設定
                    for col in range(self.table.columnCount()):
                        self.table.setItem(new_row, col, QTableWidgetItem(""))

            finally:
                # シグナルを再接続
                #self.table.cellChanged.connect(self.on_cell_changed)
                self.table.itemChanged.connect(self.on_cell_changed)

    def set_root_path(self):
        self.root_label.setText("root path: "+self.current_path)
        try:
            self.root_path=self.current_path #os.path.realpath(self.current_path)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"絶対パスが生成できません:\n{str(e)}")
    
    def new_json(self):
        # rootにjsonをつくる
        if self.root_path=="":
            QMessageBox.warning(self, "警告", "root pathを設定して下さい")
            return           

        try:
            # rootPathに保存
            file_path, _ = QFileDialog.getSaveFileName(
                self, "JSONファイルを保存", self.root_path,
                #f"file_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "exp_condition.json",
                "JSON Files (*.json)"
            )
            if file_path=="": #cancel
                return
            if os.path.dirname(file_path)!= self.root_path:
                QMessageBox.warning(self, "警告", "root pathにJSONを保存してください")
                return

            self.json_filename= os.path.basename(file_path) ##解析用jsonの名前
            self.status_label.setText(self.json_filename) 
## master
            #mfile_path, __ = QFileDialog.getSaveFileName(
            #    self, "master JSONファイルを保存", self.root_path,
            #    #f"file_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            #    "master.json",
            #    "JSON Files (*.json)"
            #)
            #if not os.path.samefile(os.path.dirname(mfile_path), self.root_path):
            #    QMessageBox.warning(self, "警告", "root pathにmaster JSONを保存してください")
            #    return

            m_filename=QInputDialog().getText(self,"set JSON filename","input JSON file name.") #,"","")

            if  self.json_filename==m_filename: ##samefileはファイルが実在しないとエラーになる！
                QMessageBox.warning(self, "警告", "tagのJSONと違う名前にmaster JSONをしてください")
                return
            #print("----")

            self.json_master_filename= m_filename #os.path.basename(mfile_path) ##解析用jsonの名前
            #self.status_label.setText(self.json_filename) 
            ##
            #row = self.table.rowCount()
            self.table.setRowCount(0) #clear
            row=0
            self.table.insertRow(row)     #1行目
            self.table.setItem(row, 0, QTableWidgetItem(""))
            self.table.setItem(row, 1, QTableWidgetItem(""))
            self.table.setItem(row, 2, QTableWidgetItem(""))

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"JSONファイルの保存に失敗しました:\n{str(e)}")
    
    def load_from_json(self):
        """
        rootから、currentdirのjsonを読み,tableにセットする
        """
        if self.root_path=="":
            QMessageBox.warning(self, "警告", "root pathを設定して下さい")
            return      

        # 読み込みファイルを選択 root xml
        file_path, _ = QFileDialog.getOpenFileName(
            self, "JSONファイルを読み込み", 
            self.root_path, "JSON Files (*.json)"
        )
        if file_path=="": #cancel
            return
        if not os.path.samefile(os.path.dirname(file_path), self.root_path):
            QMessageBox.warning(self, "警告", "root pathのJSONを指定してください")
            return

        self.json_filename=os.path.basename(file_path) ##解析用jsonの名前
        ##
        mfile_path, _ = QFileDialog.getOpenFileName(
            self, "master JSONファイルを読み込み", 
            self.root_path, "JSON Files (*.json)"
        )
        if mfile_path=="": #cancel
            return
        if not os.path.samefile(os.path.dirname(file_path), self.root_path):
            QMessageBox.warning(self, "警告", "root pathのJSONを指定してください")
            return
        if  self.json_filename==os.path.basename(mfile_path): #path.samefileはエラーだから使うな！
            QMessageBox.warning(self, "警告", "tagのJSONと違う名前にmaster JSONをしてください")
            return

        self.json_master_filename=os.path.basename(mfile_path) ##解析用jsonの名前
        
        with open(os.path.join(self.root_path,self.json_master_filename), 'r', encoding='utf-8') as f2:
            self.master_jdata = json.load(f2)
        
        self.refresh_list() #jsonのloadもこれ
        

    def save_to_json(self):
        """リストをJSONファイルに保存.
        self.jdataをtableの内容にupdateもする
        """
        
        try:

            #if not os.path.samefile( self.root_path, self.current_path):
            ## root以外に保存するときは、rootにjsonがあるか確認する
            if not os.path.samefile(self.root_path,self.current_path) and not os.path.exists(os.path.join(self.root_path,self.json_filename) ):
                QMessageBox.information(self, "エラー", f"rootにJSONファイルが作成されていません。:\n{self.current_path}")
                return

            if os.path.exists(self.current_path):

                save_data=self.get_table_dict(1) #value=1
                self.jdata=save_data
                
                # JSONファイルに保存
                with open(os.path.join(self.current_path,self.json_filename), 'w', encoding='utf-8') as f:
                    json.dump(self.jdata, f, ensure_ascii=False, indent=2) #ensue_asciiがfalseでないと、日本語がでない
                
                self.status_label.setText(self.json_filename) #(f"JSONファイルを保存しました: {os.path.basename(file_path)}")
                QMessageBox.information(self, "成功", f"JSONファイルを保存しました:\n{os.path.join(self.current_path,self.json_filename)}")
            
            ##master save
                self.master_jdata=self.get_table_dict(2) #value=2
                with open(os.path.join(self.root_path,self.json_master_filename), 'w', encoding='utf-8') as f:
                    json.dump(self.master_jdata, f, ensure_ascii=False, indent=2)
                

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"JSONファイルの保存に失敗しました:\n{str(e)}")

    ##
    def set_sub_pyfile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "*.pyファイルを読み込み", 
            self.root_path, "Python Files (*.py)"
        )
        if file_path=="" or not os.path.exists(file_path): #cancel
            return
        self.sub_py_filename=file_path

        res,tf=QInputDialog().getInt(self,"header row number","input header row length.",1) #,"","")
        print(res)
        if tf:
            self.skip_row=res

    def set_result_filename(self):

        res,tf=QInputDialog().getText(self,"result file name","input result file name.") #,"","")
        print(res)
        if tf:
            self.result_filename=res

    def do_sup_py(self):

        threads = []
        # 4つのスレッドを作成
        #for i in range(4):
        #    thread = threading.Thread(target=self.sProc)
        #    threads.append(thread)
        #    thread.start()
        
        # 全てのスレッドの終了を待つ
        #for thread in threads:
        #    thread.join()
        if self.result_filename=="":
            QMessageBox.information(self, "失敗", f"resultのファイル名をセットしてください")
            return

            
        fp = open(os.path.join(self.root_path,self.result_filename),"w+" )
        future_list = []
        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            #for i in range(20):
                #future = executor.submit(self.sProc, tpath) #i
                #future_list.append(future) root_path,sub_py_filename,result_filename,tpath,json_filename):
            #recExeJson(executor,future_list, subProc, \
            #    self.root_path,self.sub_py_filename,self.result_filename, self.root_path,self.json_filename)

            startExeJson(executor,future_list,subProc,self.root_path,self.sub_py_filename,fp, self.json_filename,self.skip_row)

            #recExeJson(executor,future_list,subProc,root_path,sub_py_filename,result_filename,tpath,json_filename):

                #executor,future_list,lambda: subProc(root_path,sub_py_filename,result_filename,tpath), \
                #root_path,sub_py_filename,result_filename, os.path.join(tpath,ff),json_filename)

            _ = futures.as_completed(fs=future_list)

        # 全てのスレッド終了後、printFinを呼び出す
        print("thread finish")
        fp.close()



#  print("標準エラー出力:", result.stderr)



    #########################################################
    # utility for callback
    def over_root_path(self,rootpath,tpath):
        """
        rootを超えたときTrue
        """

        comm=os.path.commonpath([rootpath,tpath])
        return not os.path.samefile(comm,rootpath)
        

    def get_table_dict(self,col):
        """"
        空のときは空のdictになる
        """
        ret=dict()
        for ii in range( self.table.rowCount() ):

            if self.table.item(ii,0)!="" and self.table.item(ii,0)!=None: #itemAtはro,colを無視して0,0だけを返すらしい！
                key=self.table.item(ii,0).text()
                if key=="" or key==None:
                    continue
                value=self.table.item(ii,col).text()
                value= "" if value==None else value
                ret[key]=value
                #print(str(ii)+str(self.table.item(ii,0))+"  "+str(self.table.item(ii,1)) )
        #print("gettable-dict")
        #print(ret)
        return ret

    def get_diff_path_list(self):
        """
        rootPathとcurrentPathの中間のパスのリストを返す。[current_dir,...,rootdir]
        パスが無効なら[]
        currentとrootが同じでもrootが入る。
        """
        pathList=[]
        if os.path.exists(self.root_path) and os.path.exists(self.current_path):
            
            tpath= self.current_path #os.path.dirname(self.current_path)
            if self.over_root_path(self.root_path,self.current_path): #親を超えたpathが指定された。エラー
                return []

            while (not os.path.samefile(self.root_path,tpath) ): ## pathは==で比較しては行けない。同じパスでもtrueにならない
                if self.over_root_path(self.root_path,tpath):
                    break
                
                pathList.append(tpath)
                print(str(tpath))
                tpath=os.path.dirname(tpath)
                print("->"+str(tpath))

            pathList.append(self.root_path) #
            return pathList
        else:
            return []

    def get_overwrite_json_dict(self,pathlist,filename):
        """
        rootのfilenameのjsonをloadして、中間dir、currentdirのjsonを追記
        """

        pathList=self.get_diff_path_list()
        jdict=dict()
        for pp in pathlist:
            if os.path.exists(os.path.join(pp,self.json_filename)):
                with open(os.path.join(pp,self.json_filename), 'r', encoding='utf-8') as f:
                    jj = json.load(f)
                #print(jj)
                jdict=jj| jdict
        #print("overwite json")
        #print(jdict)
        return jdict
       
    ########
 
    def update_path(self, path):
        """パスを更新してリストを再構築"""
        #path=pathlib.Path(path)
        if path and os.path.exists(path):
            self.current_path = path #os.path.realpath(path) 
            self.path_label.setText(f"current path: {path}")
            self.refresh_list() ##
            print("refl"+str(path))
            print(self.jdata)
        #else:
            #self.status_label.setText("無効なパスです")
    
    def refresh_list(self):
        """リストを更新"""
        if  self.current_path=="" or not os.path.exists(self.current_path) \
            or self.root_path=="" or not os.path.exists(self.root_path):

            self.status_label.setText("root未設定か、無効なパスです")
            return
        
        try:

            pathlist=self.get_diff_path_list()
            self.jdata=self.get_overwrite_json_dict(pathlist,self.json_filename)

            self.table.setRowCount(0)
            self.add_json_to_table()
            
        except Exception as e:
            self.status_label.setText(f"エラー: {str(e)}")
    
    def add_json_to_table(self):
        """jsonをテーブルに追加"""
        try:

            if len(self.jdata)==0:
                return

            self.indexDict=dict()
            
            # テーブルに追加
            for key,value in self.jdata.items():
                #print(rr)
                #key,value =rr
                if key!=None and key!="":
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    print("add"+str(row))
                    
                    self.table.setItem(row, 0, QTableWidgetItem(key))
                    self.table.setItem(row, 1, QTableWidgetItem(value))
                    self.indexDict[key]=row
            
            for key,value in self.indexDict.items():
                ml=self.master_jdata.get(key)
                if ml!=None:
                    self.table.setItem(value, 2, QTableWidgetItem(str(ml)))         

        except Exception as e:
            print(f"アイテム追加エラー: {e}")
    


    #def update_master_value_list(self):
    #    """master valueリストを更新"""
    #    try:
    #        self.master_value_list = []
    #        #self.table.setRowCount(0)

    #    except Exception as e:
    #        QMessageBox.critical(self, "エラー", f"master valueリストの更新に失敗しました:\n{str(e)}")
    
    ##context menu callback
    def show_context_menu(self, position):
        """コンテキストメニューを表示"""
        row = self.table.rowAt(position.y())
        if row >= 0:
            menu = QMenu()
            
            # ファイルパスを取得
            path_item = self.table.item(row, 4)
            if path_item:
                file_path = path_item.text()
                
                # 開くアクション
                open_action = menu.addAction("開く")
                open_action.triggered.connect(lambda: self.open_file(file_path))
                
                # フォルダで開くアクション
                open_folder_action = menu.addAction("フォルダで開く")
                open_folder_action.triggered.connect(lambda: self.open_folder(file_path))
                
                menu.addSeparator()
                
                # パスをコピーアクション
                copy_path_action = menu.addAction("パスをコピー")
                copy_path_action.triggered.connect(lambda: self.copy_path(file_path))
            
            menu.exec_(self.table.mapToGlobal(position))
    
    def open_file(self, file_path):
        """ファイルを開く"""
        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"ファイルを開けませんでした: {str(e)}")
    
    def open_folder(self, file_path):
        """フォルダで開く"""
        try:
            if os.path.isdir(file_path):
                os.startfile(file_path)
            else:
                os.startfile(os.path.dirname(file_path))
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"フォルダを開けませんでした: {str(e)}")
    
    def copy_path(self, file_path):
        """パスをクリップボードにコピー"""
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(file_path)
            #self.status_label.setText("パスをクリップボードにコピーしました")
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"クリップボードへのコピーに失敗しました: {str(e)}")

############

def startExeJson(executor,future_list,subProc,root_path,sub_py_filename,fp,json_filename,skip_row):
    """
    *.pyの再帰実行のスタート。rootだけはファイルopen、ヘッダー出力がある。
    fp は開いた状態で引数で受けて、呼び出し側がcloseする。
    """
    with open(os.path.join(root_path, json_filename), 'r', encoding='utf-8') as f2:
        jdata = json.load(f2)

    retl=""
    for jd in jdata.keys():
        retl+=str(jd)+","
    
    fp.write(retl+"\n")

    tpath=root_path
    recExeJson(executor,future_list,subProc,root_path,sub_py_filename,fp,tpath,json_filename,skip_row)

def recExeJson(executor,future_list,subProc,root_path,sub_py_filename,fp,tpath,json_filename,skip_row):
    """
    skip_rowは*.pyが行ヘッダーあり出力のときに無視するヘッダ行数
    """

    #fp.write("recExe "+tpath+"\n")
    if os.path.exists(os.path.join(tpath,json_filename)):
        print("rec-ok")
        future = executor.submit(subProc, root_path,sub_py_filename,fp, tpath,json_filename,skip_row) #i ##lambda式がつかえない！
        future_list.append(future)

        for ff in os.listdir(tpath):
            if os.path.isdir(os.path.join(tpath, ff)):
                print("isdir"+ff)
                recExeJson(executor,future_list, subProc, \
                root_path,sub_py_filename,fp, os.path.join(tpath,ff), json_filename,skip_row)
    else:
        print("no-json" +os.path.join(tpath,json_filename))

def subProc(root_path,sub_py_filename,fp,tpath,json_filename,skip_row):
    """
    各フォルダで実行されるsubProc。指定した*.pyを呼び出す。
    結果の保存も行う。
    """
    with open(os.path.join(tpath, json_filename), 'r', encoding='utf-8') as f2:
        jdata = json.load(f2)

    if root_path==tpath: #rootのときはsubprocのheaderをsukipしない
        skip_row=0

#####
    command=["python",sub_py_filename,tpath] #, self.sub_py_filename] #, "arg1", "arg2"]
    print(command)
    #python　をsubprocessでよぶには、shell=tureがいる
    # subprocess.run()で実行
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    # 標準出力と標準エラー出力を確認
    #print("res-------\n"+str(result.stdout))
    relpath=os.path.relpath(tpath, start=root_path)
    #print("relpath------ "+relpath)

    #tpathではなくrootpathへ
    #with open(os.path.join(root_path,result_filename), 'a+', encoding='utf-8') as fp: #追記モード
    #print("stdout===============\n"+str(result)+"\n" )
    ol=str(result.stdout)#.splitlines()
    #print("ol===============\n"+str(ol)+"\n" )
    olines=ol.splitlines()
    #print("plines===============\n"+str(olines)+"\n" )
    #fp.write("plines"+str(olines) )
    #fp.flush()

    #fp.write(str(olines)+"\n") 
#    fp.write( str(olines[0])+"\n") 


    for li in range(skip_row,len(olines)):
        retl=""
        for jd in jdata.values():
            retl+=str(jd)+","

        retl+=relpath+","
        retl+=olines[li]
        #print(relpath+","+ll )
        #fp.write("wwww")
        fp.write(retl+"\n") #+","+ll )


if __name__ == "__main__":
    fp = open(r"C:\python_data\cursor_test\tag_exproler\main.csv","w+" )
    subProc( r"C:\python_data\cursor_test\tag_exproler\jsontest",r"C:\python_data\cursor_test\tag_exproler\threadTest\subpy.py" , \
        fp, r"C:\python_data\cursor_test\tag_exproler\jsontest", "dd.json",1)