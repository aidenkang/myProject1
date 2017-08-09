"""
QtDesigner로 만든 UI와 해당 UI의 위젯에서 발생하는 이벤트를 컨트롤하는 클래스

author: 서경동
last edit: 2017. 01. 18
"""

import sys, time, datetime
import sqlite3
import pandas as pd
from pandas import Series, DataFrame
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem, QDialog, QListWidgetItem
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5 import uic
from Kiwoom import Kiwoom, ParameterTypeError, ParameterValueError, KiwoomProcessingError, KiwoomConnectError

ui = uic.loadUiType("pytrader.ui")[0]
jongmokInputPopupUI = uic.loadUiType("ItemSelectPopup.ui")[0]

class InputInterestItem(QDialog, jongmokInputPopupUI):
    def __init__(self, kw):
        super().__init__()
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.kiwoom = kw

        self.buttonBoxAddJongmok.accepted.connect (self.saveSelectedJonkmok)
        self.buttonBoxAddJongmok.rejected.connect (self.close)
        self.llineEditAddJongmokCode.textChanged.connect(self.processAddJongmokTextChanged)

    def saveSelectedJonkmok(self):
        self.jongmokCode = self.llineEditAddJongmokCode.text()
        self.jongmokName = self.lineEditDisplayAddJonkmokName.text()

        print ("Save button pushed!")

    def processAddJongmokTextChanged(self):
        code = self.llineEditAddJongmokCode.text()
        codeName = self.kiwoom.getCodeNameFromCode(code)
        if (codeName == ""):
            return

        self.lineEditDisplayAddJonkmokName.setText(codeName)

# SQLDB_TABLE_LIST = ['Targetjongmok',]

class  MySql():
    DB_PATH = "./kiwoom.db"
    DB_TABLE_DICT = {
                        'TARGET_JONGMOK' : ['종목코드', '종목명'],
#                        'OHLCV' : ['data', 'open', 'high', 'low', 'close', 'volume']
                    }

    def __init__(self):
        self.initializeDB()

    def initializeDB(self):
        try:
            for tablename in self.DB_TABLE_DICT.keys():
                self.createTables(tablename)
        except Exception as e:
            print("\nExxception occurred. {0}".format(e))

    def readJongmokToDF(self):
        sqldb = sqlite3.connect (self.DB_PATH)

        with sqldb:
            try:
                index_name = self.DB_TABLE_DICT['TARGET_JONGMOK'][0]
                df = pd.read_sql("SELECT * FROM '{0}'".format('TARGET_JONGMOK'), sqldb, index_col=index_name)
                df.index.name = index_name
            except Exception as e:
                print("\nExxception occurred. {0}".format(e))

        return df

    def commitJongmokFromDF (self, df):
        sqldb = sqlite3.connect(self.DB_PATH)

        with sqldb:
            try:
                df.to_sql('TARGET_JONGMOK', sqldb, if_exists='replace')

            except Exception as e:
                print("\nExxception occurred. {0}".format(e))

    def commitOHLCVforJongmok (self, code, df):
        sqldb = sqlite3.connect(self.DB_PATH)

        with sqldb:
            try:
                df.to_sql(code, sqldb, if_exists='replace')

            except Exception as e:
                print("\nExxception occurred. {0}".format(e))

    def createTables(self, tablename):
        dbcon = sqlite3.connect (self.DB_PATH)
        with dbcon:
            dbcur = dbcon.cursor()
            if tablename == 'TARGET_JONGMOK':
                try:
                    sqlcmd = """CREATE TABLE IF NOT EXISTS '{0}' ('{1}' text PRIMARY KEY, '{2}' text NOT NULL)
                                """.format(tablename, self.DB_TABLE_DICT[tablename][0], self.DB_TABLE_DICT[tablename][1])
                    dbcur.execute(sqlcmd)
                except Exception as e:
                    print("\nExxception occurred. {0}".format(e))
            dbcur.close()

    def checkTableExists(self, tablename):
        dbcon = sqlite3.connect (self.DB_PATH)

        with dbcon:
            dbcur = dbcon.cursor()
            dbcur.execute("""
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type = 'table' and name = '{0}'
                """.format(tablename.replace('\'', '\'\'')))
            if dbcur.fetchone()[0] == 1:
                dbcur.close()
                return True

        dbcur.close()
        return False

    def insertJongmok(self, code, name):
        sqldb = sqlite3.connect(self.DB_PATH)
        with sqldb:
            dbcur = sqldb.cursor()
            cols = ', '.join('"{}"'.format(col) for col in self.DB_TABLE_DICT['TARGET_JONGMOK'])
            vals = '"{0}","{1}"'.format(code, name)
            try:
                sqlcmd = """INSERT INTO '{0}' ({1}) VALUES ({2})""".format('TARGET_JONGMOK', cols, vals)
                dbcur.execute(sqlcmd)

                self.DB_TABLE_DICT['OHLCV_' + code] = ['data', 'open', 'high', 'low', 'close', 'volume']
                self.createTables('OHLCV_' + code)

                sqldb.commit()
            except Exception as e:
                print("\nExxception occurred. {0}".format(e))

            dbcur.close()

    def loadJongmok(self):
        sqldb = sqlite3.connect(self.DB_PATH)
        with sqldb:
            try:
                df = pd.read_sql("SELECT * FROM '{0}'".format('TARGET_JONGMOK'), sqldb)
                print(df)
            # except sqlite3.OperationalError as e:
            # except sqlite3.DatabaseError as e:

            except Exception as e:
                print("\nExxception occurred. {0}".format(e))

#            df = pd.read_sql_table('Targetjongmok', sqldb, index_col='code')
#            df.to_sql('Targetjongmok', sqldb, if_exists='replace')

from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.scheduler import Scheduler

class ScheduledJobs():
    def __init__(self):
        sched = BackgroundScheduler()
#        sched = Scheduler()
        sched.add_job(self.test, 'cron', hour='9', minute='44', second='0,5,10,15,20,25,30,35,40,45,50,55')

        sched.start()

    def test(self):
        print ('Cron function at {0}'.format(time.strftime('%H:%M:%S')))

class MyWindow(QMainWindow, ui):
    def __init__(self):
        super().__init__()

        self.kiwoom = Kiwoom()
        self.kiwoom.commConnect()

        self.setupUi(self)
        self.show()

        self.kiwoom.r.realSignal.connect(self.onRealData)

        self.db = MySql()

        self.server = self.kiwoom.getLoginInfo("GetServerGubun")

        if len(self.server) == 0 or self.server != "1":
            self.serverGubun = "실제운영"
        else:
            self.serverGubun = "모의투자"

        # 메인 타이머
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        # 잔고 및 보유종목 조회 타이머
        self.inquiryTimer = QTimer(self)
        self.inquiryTimer.start(1000*10)
        self.inquiryTimer.timeout.connect(self.timeout)

        self.setAccountComboBox()
        self.codeLineEdit.textChanged.connect(self.setCodeName)
        self.lineEditSilsiganJongmok.textChanged.connect(self.processSilsiganJongMokTextChanged)
        self.orderBtn.clicked.connect(self.sendOrder)
        self.inquiryBtn.clicked.connect(self.inquiryBalance)

        self.checkBoxSilsiganJongmok.stateChanged.connect(self.changeSilsiganJonkmok)

        self.toolButtonAddJongmok.clicked.connect(self.inputAutoJongmok)
        self.toolButtonRemoveJongkmok.clicked.connect(self.removeAutoJongmok)

        displayItems = ["종목코드"] +  self.kiwoom.rtJusikChaekulLists
        self.realTimeTable.setHorizontalHeaderLabels(displayItems)
        self.realTimeTable.resizeColumnsToContents()

        # 자동 주문
        # 자동 주문을 활성화 하려면 True로 설정
        self.isAutomaticOrder = False

        # 자동 선정 종목 리스트 테이블 설정
        self.setAutomatedStocks()

        ScheduledJobs()

    realDispLists = []

    def inputAutoJongmok(self):
        inputdialog = InputInterestItem(self.kiwoom)
        inputdialog.show()
        inputdialog.exec_()

        self.db.insertJongmok(inputdialog.jongmokCode, inputdialog.jongmokName)
        self.createJongmokOHLCV_DB(inputdialog.jongmokCode)

        self.listWidgetAutoJongmok.addItem('{0:15}{1:15}'.format(inputdialog.jongmokCode, inputdialog.jongmokName))
#        self.listWidgetAutoJongmok.show()

    def updateListWidgetJongmok(self, jongmokdf):
        for index, row in jongmokdf.iterrows():
            self.listWidgetAutoJongmok.addItem('{0:15}{1:15}'.format(index, row['종목명']))    #index is series of '종목코드'

    def createJongmokOHLCV_DB(self, code):
        self.kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

        self.kiwoom.setInputValue("종목코드", code)
        today = datetime.datetime.today().strftime("%Y%m%d")
        self.kiwoom.setInputValue("기준일자", today)
        self.kiwoom.setInputValue("수정주가구분", '1')
        self.kiwoom.commRqData("주식일봉차트조회요청", "opt10081", 0, "0101")

        df = DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=self.kiwoom.ohlcv['date'])

        self.db.commitOHLCVforJongmok(code, df)

    def checkOHLCVTable(self, jongmokdf):
        for code in jongmokdf.index:        # index is '종목코드'
            if not self.db.checkTableExists('OHLCV_'+ code):
                self.db.DB_TABLE_DICT['OHLCV_'+ code] = ['data', 'open', 'high', 'low', 'close', 'volume']
                self.db.createTables('OHLCV_'+ code)

            self.createJongmokOHLCV_DB(code)

    def setAutomatedStocks(self):
        jongmokdf = self.db.readJongmokToDF ()
        self.updateListWidgetJongmok(jongmokdf)
        self.checkOHLCVTable(jongmokdf)
        """
        fileList = ["buy_list.txt", "sell_list.txt"]
        automatedStocks = []

        try:
            for file in fileList:
                # utf-8로 작성된 파일을
                # cp949 환경에서 읽기위해서 encoding 지정
                with open(file, 'rt', encoding='utf-8') as f:
                    stocksList = f.readlines()
                    automatedStocks += stocksList
        except Exception as e:
            e.msg = "setAutomatedStocks() 에러"
            self.showDialog('Critical', e)
            return

        # 테이블 행수 설정
        cnt = len(automatedStocks)
        self.automatedStocksTable.setRowCount(cnt)

        # 테이블에 출력
        for i in range(cnt):
            stocks = automatedStocks[i].split(';')

            for j in range(len(stocks)):
                if j == 1:
                    name = self.kiwoom.getMasterCodeName(stocks[j].rstrip())
                    item = QTableWidgetItem(name)
                else:
                    item = QTableWidgetItem(stocks[j].rstrip())

                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.automatedStocksTable.setItem(i, j, item)

        self.automatedStocksTable.resizeRowsToContents()
        """

    def msgbox (self, text, info, title, dtext):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText(text)
        msg.setInformativeText(info)
        msg.setWindowTitle(title)
        msg.setDetailedText(dtext)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
#        msg.buttonClicked.connect(self.msgbtn)

        retval = msg.exec_()

        return retval

    def msgbtn(btn):
        print(btn)

    def removeAutoJongmok(self):
        retval = self.msgbox("종목을 삭제합니다", "", "Warning", "")

        if retval == QMessageBox.Ok:
            for item in self.listWidgetAutoJongmok.selectedItems():
                print (item)
            print([x.row() for x in self.listWidgetAutoJongmok.selectedIndexes()])
#            print([item.text() for item in self.listWidgetAutoJongmok.selectedItems()])
            print ("removing")
            df = self.db.readJongmokToDF ()
            df = df.drop(df.index[[x.row() for x in self.listWidgetAutoJongmok.selectedIndexes()]])
            print (df)
            self.db.commitJongmokFromDF(df)

            model = self.listWidgetAutoJongmok.model()
            for selectedItem in self.listWidgetAutoJongmok.selectedItems():
                qIndex = self.listWidgetAutoJongmok.indexFromItem(selectedItem)
                print ('removing : %s' % model.data(qIndex))
                model.removeRow(qIndex.row())

        else:
            print ("Ignored")

    def onRealData(self, data):
        """
        searchOnRealDataList(data[])
        cnt = self.getRepeatCnt(trCode, requestName)
        keyList = ["종목명", "보유수량", "매입가", "현재가", "평가손익", "수익률(%)"]
#        "10;27;28;13;14;15;16;17;18"
        for i in range(cnt):
            stock = []

            for key in keyList:
                value = self.commGetData(trCode, "", requestName, i, key)

                if key.startswith("수익률"):
                    value = self.changeFormat(value, 2)
                elif key != "종목명":
                    value = self.changeFormat(value)

                stock.append(value)

            self.opw00018Data['stocks'].append(stock)
         """

        dic = {}
        dataFounded = False

        if (data['RealType'] == '주식체결'):
            for i, realDispList in enumerate(self.realDispLists):
                if (realDispList['종목코드'] == data['Data']['종목코드']):
                    self.realDispLists[i]['Data'] = data['Data']
                    dataFounded = True
                    dispItems = self.realDispLists[i]
                    break;

            if (not dataFounded):
                dic['종목코드'] = data['Data']['종목코드']
                dic['Data'] = data['Data']
                dic["Row"] = len(self.realDispLists)
                self.realDispLists.append(dic)
                self.realTimeTable.setRowCount(dic['Row']+1)
                dispItems = self.realDispLists[dic["Row"]]

            item = QTableWidgetItem(dispItems['Data']['종목코드'])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.realTimeTable.setItem(dispItems['Row'], 0, item)

            col = 1
            for i in range(len(self.kiwoom.rtJusikChaekulLists)):
                item = QTableWidgetItem(dispItems['Data'][self.kiwoom.rtJusikChaekulLists[i]])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.realTimeTable.setItem(dispItems['Row'], col, item)
                col += 1

            self.realTimeTable.resizeRowsToContents()

            """
            for j in range(len(row)):
                item = QTableWidgetItem(row[j])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.stocksTable.setItem(i, j, item)
        
            self.stocksTable.resizeRowsToContents()
            """
            print ('RT_DATA:', self.realDispLists)
        else:
            print ('RT_DATA:', data)


    def timeout(self):
        """ 타임아웃 이벤트가 발생하면 호출되는 메서드 """

        # 어떤 타이머에 의해서 호출되었는지 확인
        sender = self.sender()

        # 메인 타이머
        if id(sender) == id(self.timer):
            currentTime = QTime.currentTime().toString("hh:mm:ss")
            automaticOrderTime = QTime.currentTime().toString("hhmm")

            # 상태바 설정
            state = ""

            if self.kiwoom.getConnectState() == 1:

                state = self.serverGubun + " 서버 연결중"
            else:
                state = "서버 미연결"

            self.statusbar.showMessage("현재시간: " + currentTime + " | " + state)

            # 자동 주문 실행
            # 1100은 11시 00분을 의미합니다.
            if self.isAutomaticOrder and int(automaticOrderTime) >= 1100:
                self.isAutomaticOrder = False
                self.automaticOrder()
                self.setAutomatedStocks()

            # log
            if self.kiwoom.msg:
                self.logTextEdit.append(self.kiwoom.msg)
                self.kiwoom.msg = ""

        # 실시간 조회 타이머
        else:
            if self.realtimeCheckBox.isChecked():
                self.inquiryBalance()

    def setCodeName(self):
        """ 종목코드에 해당하는 한글명을 codeNameLineEdit에 설정한다. """

        code = self.codeLineEdit.text()
        codeName = self.kiwoom.getCodeNameFromCode(code)
        if (codeName != ""):
            self.codeNameLineEdit.setText(codeName)

    def processSilsiganJongMokTextChanged(self):
        code = self.lineEditSilsiganJongmok.text()
        codeName = self.kiwoom.getCodeNameFromCode(code)
        if (codeName == ""):
            if (self.checkBoxSilsiganJongmok.isChecked()):
                self.checkBoxSilsiganJongmok.setCheckState(Qt.Unchecked)
            return

        if (code in self.silsiganJongkmok):
            self.checkBoxSilsiganJongmok.setCheckState(Qt.Checked)
        else:
            self.checkBoxSilsiganJongmok.setCheckState(Qt.Unchecked)

        self.setSilsiganCodeName()

    def setSilsiganCodeName(self):
        code = self.lineEditSilsiganJongmok.text()
        codeName = self.kiwoom.getCodeNameFromCode(code)
        if (codeName != ""):
            self.codeNameLineEditSilsiganJongmok.setText(codeName)

    silsiganJongkmok = []

    def makeCodeList (self, code):
        if (code not in self.silsiganJongkmok):
            self.silsiganJongkmok.append(code)
        return ";".join(self.silsiganJongkmok)

    def changeSilsiganJonkmok(self):
        code = self.lineEditSilsiganJongmok.text()
        if (code == ""):
            return
        if (self.checkBoxSilsiganJongmok.isChecked()):
            if (code not in self.silsiganJongkmok):
                codelist = self.makeCodeList(code)
                self.kiwoom.set_real_req(codelist)
                print ("[종목",codelist,'] 실시간현황 설정')
        else:
            self.kiwoom.setRealRemove("0101", code)
            print ("[종목",code,'] 실시간현황 해재')

    def setAccountComboBox(self):
        """ accountComboBox에 계좌번호를 설정한다. """

        try:
            cnt = int(self.kiwoom.getLoginInfo("ACCOUNT_CNT"))
            accountList = self.kiwoom.getLoginInfo("ACCNO").split(';')
            self.accountComboBox.addItems(accountList[0:cnt])
        except (KiwoomConnectError, ParameterTypeError, ParameterValueError) as e:
            self.showDialog('Critical', e)

    def sendOrder(self):
        """ 키움서버로 주문정보를 전송한다. """

        orderTypeTable = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hogaTypeTable = {'지정가': "00", '시장가': "03"}

        account = self.accountComboBox.currentText()
        orderType = orderTypeTable[self.orderTypeComboBox.currentText()]
        code = self.codeLineEdit.text()
        hogaType = hogaTypeTable[self.hogaTypeComboBox.currentText()]
        qty = self.qtySpinBox.value()
        price = self.priceSpinBox.value()

        try:
            self.kiwoom.sendOrder("수동주문", "0101", account, orderType, code, qty, price, hogaType, "")

        except (ParameterTypeError, KiwoomProcessingError) as e:
            self.showDialog('Critical', e)

    def inquiryBalance(self):
        """ 예수금상세현황과 계좌평가잔고내역을 요청후 테이블에 출력한다. """

        self.inquiryTimer.stop()

        try:
            # 예수금상세현황요청
            self.kiwoom.setInputValue("계좌번호", self.accountComboBox.currentText())
            self.kiwoom.setInputValue("비밀번호", "0000")
            self.kiwoom.commRqData("예수금상세현황요청", "opw00001", 0, "2000")

            # 계좌평가잔고내역요청 - opw00018 은 한번에 20개의 종목정보를 반환
            self.kiwoom.setInputValue("계좌번호", self.accountComboBox.currentText())
            self.kiwoom.setInputValue("비밀번호", "0000")
            self.kiwoom.commRqData("계좌평가잔고내역요청", "opw00018", 0, "2000")

            while self.kiwoom.inquiry == '2':
                time.sleep(0.2)

                self.kiwoom.setInputValue("계좌번호", self.accountComboBox.currentText())
                self.kiwoom.setInputValue("비밀번호", "0000")
                self.kiwoom.commRqData("계좌평가잔고내역요청", "opw00018", 2, "2")

        except (ParameterTypeError, ParameterValueError, KiwoomProcessingError) as e:
            self.showDialog('Critical', e)

        # accountEvaluationTable 테이블에 정보 출력
        item = QTableWidgetItem(self.kiwoom.opw00001Data)   # d+2추정예수금
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.accountEvaluationTable.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018Data['accountEvaluation'][i-1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.accountEvaluationTable.setItem(0, i, item)

        self.accountEvaluationTable.resizeRowsToContents()

        # stocksTable 테이블에 정보 출력
        cnt = len(self.kiwoom.opw00018Data['stocks'])
        self.stocksTable.setRowCount(cnt)

        for i in range(cnt):
            row = self.kiwoom.opw00018Data['stocks'][i]

            for j in range(len(row)):
                item = QTableWidgetItem(row[j])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.stocksTable.setItem(i, j, item)

        self.stocksTable.resizeRowsToContents()

        # 데이터 초기화
        self.kiwoom.opwDataReset()

        # inquiryTimer 재시작
        self.inquiryTimer.start(1000*10)

    # 경고창
    def showDialog(self, grade, error):
        gradeTable = {'Information': QMessageBox.Information, 'Warning': QMessageBox.Warning, 'Critical':
                        QMessageBox.Critical, 'Question': QMessageBox.Question, 'NoIcon': QMessageBox.NoIcon}

        dialog = QMessageBox()
        dialog.setIcon(gradeTable[grade])
        dialog.setText(error.msg)
        dialog.setWindowTitle(grade)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec_()

    def automaticOrder(self):
        fileList = ["buy_list.txt", "sell_list.txt"]
        hogaTypeTable = {'지정가': "00", '시장가': "03"}
        account = self.accountComboBox.currentText()
        automatedStocks = []

        # 파일읽기
        try:
            for file in fileList:
                # utf-8로 작성된 파일을
                # cp949 환경에서 읽기위해서 encoding 지정
                with open(file, 'rt', encoding='utf-8') as f:
                    stocksList = f.readlines()
                    automatedStocks += stocksList
        except Exception as e:
            e.msg = "automaticOrder() 에러"
            self.showDialog('Critical', e)
            return

        cnt = len(automatedStocks)

        # 주문하기
        buyResult = []
        sellResult = []

        for i in range(cnt):
            stocks = automatedStocks[i].split(';')

            code = stocks[1]
            hoga = stocks[2]
            qty = stocks[3]
            price = stocks[4]

            try:
                if stocks[5].rstrip() == '매수전':
                    self.kiwoom.sendOrder("자동매수주문", "0101", account, 1, code, int(qty), int(price), hogaTypeTable[hoga], "")

                    # 주문 접수시
                    if self.kiwoom.orderNo:
                        buyResult += automatedStocks[i].replace("매수전", "매수주문완료")
                        self.kiwoom.orderNo = ""
                    # 주문 미접수시
                    else:
                        buyResult += automatedStocks[i]

                # 참고: 해당 종목을 현재도 보유하고 있다고 가정함.
                elif stocks[5].rstrip() == '매도전':
                    self.kiwoom.sendOrder("자동매도주문", "0101", account, 2, code, int(qty), int(price), hogaTypeTable[hoga], "")

                    # 주문 접수시
                    if self.kiwoom.orderNo:
                        sellResult += automatedStocks[i].replace("매도전", "매도주문완료")
                        self.kiwoom.orderNo = ""
                    # 주문 미접수시
                    else:
                        sellResult += automatedStocks[i]

            except (ParameterTypeError, KiwoomProcessingError) as e:
                self.showDialog('Critical', e)

        # 잔고및 보유종목 디스플레이 갱신
        self.inquiryBalance()

        # 결과저장하기
        for file, result in zip(fileList, [buyResult, sellResult]):
            with open(file, 'wt', encoding='utf-8') as f:
                for data in result:
                    f.write(data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    sys.exit(app.exec_())
