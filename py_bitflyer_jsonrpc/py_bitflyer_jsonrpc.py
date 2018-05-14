#!/usr/bin/python3
# coding: utf-8

import websocket
import threading
import traceback
from time import sleep
import json
import logging

class BitflyerJSON_RPC:

    MAX_LIMIT_LEN = 1000
    
    '''
    #
    # symbolに購読する通貨セットを指定してください
    # 'BTC_JPY','FX_BTC_JPY','ETH_BTC','BTCJPY28APR2017','BTCJPY05MAY2017','BTCJPY29JUN2018'
    #
    '''
    def __init__(self, symbol):
        # ロガー生成
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing WebSocket.")

        self.endpoint = "wss://ws.lightstream.bitflyer.com/json-rpc"
        self.symbol = symbol
        # 購読するsubscriptionsを設定
        
        self.channel_snapshot = "lightning_board_snapshot" + '_' + self.symbol
        self.channel_board = "lightning_board"  + '_' + self.symbol
        self.channel_ticker = "lightning_ticker"  + '_' + self.symbol
        self.channel_executions = "lightning_executions"  + '_' + self.symbol
        
        self.channels = [self.channel_snapshot, self.channel_board, self.channel_ticker, self.channel_executions]
        
        # データを格納する変数を宣言
        self.data = {}

        self.exited = False
        # findItemByKeys高速化のため、インデックスを作成・格納するための変数を作っておく
        self.itemIdxs = {}

        # スナップショットの値を格納する辞書
        self.snapshot = {}
        self.snapshot_bids_dict = {}
        self.snapshot_asks_dict = {}
        # Ticker情報を格納する配列
        self.tickers = []
        # 成約情報を格納する配列と辞書
        self.executions = []
        self.executions_sell_dict = {}
        self.executions_buy_dict = {}
        
        wsURL = self.endpoint

        self.logger.info("Connecting to %s" % wsURL)
        self.__connect(wsURL, symbol)
        self.logger.info('Connected to WS.')
        self.__wait_for_first_data()

    def exit(self):
        '''WebSocketクローズ時に呼ばれます'''
        self.exited = True
        self.ws.close()

    def get_board_snapshot(self):
        '''板情報のスナップショットを取得します'''
        return self.data['snapshot']

    def get_ticker(self):
        '''最新のTicker情報を取得します'''
        return self.data['tickers'][-1]

    def get_execution(self, order_acceptance_id=''):
        '''指定されたorder_acceptance_idに関連する約定情報の配列を返却します
            指定されなかった場合、直近MAX_LIMIT_LEN分の約定情報を返却します'''
        if order_acceptance_id == '':
            return self.data['executions']
        elif order_acceptance_id in self.executions_buy_dict.keys():
            return self.executions_buy_dict[order_acceptance_id]
        elif order_acceptance_id in self.executions_sell_dict.keys():
            return self.executions_sell_dict[order_acceptance_id]
        else:
            return []


    #
    # End Public Methods
    #

    def __connect(self, wsURL, symbol):
        '''Connect to the websocket in a thread.'''
        self.logger.debug("Starting thread")

        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error,
                                         header=None)

        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()
        self.logger.debug("Started thread")

        # Wait for connect before continuing
        conn_timeout = 5
        while not self.ws.sock or not self.ws.sock.connected and conn_timeout:
            sleep(1)
            conn_timeout -= 1
        if not conn_timeout:
            self.logger.error("Couldn't connect to WS! Exiting.")
            self.exit()
            raise websocket.WebSocketTimeoutException('Couldn\'t connect to WS! Exiting.')

    def __on_open(self, ws):
        '''コネクションオープン時の処理'''
        self.logger.debug("Websocket Opened.")
        # 指定されている通貨セットの全てのチャンネルを購読します
        for channel in self.channels:
            output_json = json.dumps(
                {'method' : 'subscribe',
                'params' : {'channel' : channel}
                }
            )
            ws.send(output_json)
            
    def __wait_for_first_data(self):
        # 全ての購読の最初のデータが揃うまで待ちます
        while not {'snapshot', 'tickers', 'executions'} <= set(self.data):
            sleep(0.1)


    def __on_close(self, ws):
        '''WebSocketクローズ時の処理'''
        self.logger.info('Websocket Closed')

    def __on_error(self, ws, error):
        '''WebSocketでエラーが発生したときの処理'''
        if not self.exited:
            self.logger.error("Error : %s" % error)
            raise websocket.WebSocketException(error)

    def __on_message(self, ws, message):
        '''WebSocketがメッセージを取得したときの処理'''
        message = json.loads(message)['params']
        self.logger.debug(json.dumps(message))
        try:
            recept_channel = message['channel']
            recept_data = message['message']
            
            if recept_channel == self.channel_snapshot:
                # 板スナップショット
                self.data["snapshot"] = recept_data
                for bid in self.data["snapshot"]["bids"]:
                    self.snapshot_bids_dict[bid["price"]] = bid
                for ask in self.data["snapshot"]["asks"]:
                    self.snapshot_asks_dict[bid["price"]] = ask
                
            elif recept_channel == self.channel_board:
                # 板更新情報
                #取得したデータでスナップショットを更新する
                if "snapshot" not in self.data.keys() :
                    return
                #mid_price
                self.data["snapshot"]["mid_price"] = recept_data["mid_price"]
                # bids
                if len(recept_data["bids"]) > 0 :
                    for re_bit in recept_data["bids"]:
                        if re_bit["price"] in self.snapshot_bids_dict.keys():
                            if re_bit["size"] == 0:
                                del self.snapshot_bids_dict[re_bit["price"]]
                            else:
                                self.snapshot_bids_dict[re_bit["price"]] = re_bit
                        else:
                            self.snapshot_bids_dict[re_bit["price"]] = re_bit
                # asks
                if len(recept_data["asks"]) > 0 :
                    for re_ask in recept_data["asks"]:
                        if re_ask["price"] in self.snapshot_asks_dict.keys():
                            if re_ask["size"] == 0:
                                del self.snapshot_asks_dict[re_ask["price"]]
                            else:
                                self.snapshot_asks_dict[re_ask["price"]] = re_ask
                        else:
                            self.snapshot_asks_dict[re_ask["price"]] = re_ask
                # 更新したデータを組み立てて、dataテーブルに組み込む
                self.data["snapshot"]["bids"] = [i[1] for i in sorted(self.snapshot_bids_dict.items(), key=lambda bid: bid[1]["price"],reverse=True)]
                self.data["snapshot"]["asks"] = [i[1] for i in sorted(self.snapshot_asks_dict.items(), key=lambda ask: ask[1]["price"],reverse=False)]

            elif recept_channel == self.channel_ticker:
                # Ticker情報
                self.tickers.append(recept_data)
                if len(self.tickers) > BitflyerJSON_RPC.MAX_LIMIT_LEN :
                    self.tickers = self.tickers[len(self.tickers)-BitflyerJSON_RPC.MAX_LIMIT_LEN:]
                self.data["tickers"] = self.tickers
                
            elif recept_channel == self.channel_executions:
                # 約定情報
                # 取得したデータをスタックに入れ込む
                # sell側とbuy側のchild_order_idとの辞書を登録する

                for execution in recept_data:
                    self.executions.append(execution)
                    if execution["sell_child_order_acceptance_id"] in self.executions_sell_dict:
                        self.executions_sell_dict[execution["sell_child_order_acceptance_id"]].append(execution)
                    else:
                        self.executions_sell_dict[execution["sell_child_order_acceptance_id"]] = [execution]
                    if execution["buy_child_order_acceptance_id"] in self.executions_buy_dict:
                        self.executions_buy_dict[execution["buy_child_order_acceptance_id"]].append(execution)
                    else:
                        self.executions_buy_dict[execution["buy_child_order_acceptance_id"]] = [execution]

                if len(self.executions) > BitflyerJSON_RPC.MAX_LIMIT_LEN:
                    del_index = len(self.executions) - BitflyerJSON_RPC.MAX_LIMIT_LEN
                    del_target = self.executions[0:del_index-1]
                    for del_ex in del_target:
                        del self.executions_sell_dict[del_ex["sell_child_order_acceptance_id"]]
                        del self.executions_buy_dict[del_ex["buy_child_order_acceptance_id"]]
                    self.executions = self.executions[del_index:]
                self.data["executions"] = self.executions

            else:
                raise Exception("Unknown channel: %s" % recept_channel)
        except:
            self.logger.error(traceback.format_exc())

if __name__ == '__main__':
    ex = BitflyerJSON_RPC(symbol='BTCJPY29JUN2018')
    print("snapshot:{0}".format(ex.get_board_snapshot()['mid_price']))
    print("tiker:{0}".format(ex.get_ticker()))
    print("execution:{0}".format(ex.get_execution()))
